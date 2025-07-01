import asyncio
import feedparser
from typing import TypedDict, Annotated, List, Dict, Any
from datetime import datetime
import re
from collections import defaultdict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


# State 정의
class NewsState(TypedDict):
    """뉴스 처리 상태를 관리하는 TypedDict"""

    messages: Annotated[List[BaseMessage], add_messages]
    rss_url: str
    raw_news: List[Dict[str, Any]]
    summarized_news: List[Dict[str, Any]]
    categorized_news: Dict[str, List[Dict[str, Any]]]
    final_report: str
    error_log: List[str]


# Utility 함수들
def clean_html(html_text: str) -> str:
    """HTML 태그 제거"""
    clean_text = re.sub("<.*?>", "", html_text)
    clean_text = re.sub("\s+", " ", clean_text).strip()
    return clean_text


def truncate_text(text: str, max_length: int = 500) -> str:
    """텍스트를 적절한 길이로 자르기"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


# Agent 클래스 정의
class RSSCollectorAgent:
    """RSS 피드를 수집하는 에이전트"""

    def __init__(self):
        self.name = "RSS Collector"

    async def collect_rss(self, state: NewsState) -> NewsState:
        """RSS 피드에서 뉴스를 수집"""
        print(f"\n🔍 [{self.name}] RSS 피드 수집 시작...")

        try:
            # RSS 피드 파싱
            feed = feedparser.parse(state["rss_url"])

            if feed.bozo:
                error_msg = f"RSS 파싱 오류: {feed.bozo_exception}"
                state["error_log"].append(error_msg)
                print(f"❌ [{self.name}] {error_msg}")

            raw_news = []
            for idx, entry in enumerate(feed.entries[:30], 1):  # 30개로 늘림
                # HTML 태그 제거 및 텍스트 정리
                summary = clean_html(entry.get("summary", ""))

                news_item = {
                    "id": idx,
                    "title": clean_html(entry.get("title", "")),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": truncate_text(summary, 300),
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "raw_summary": summary,  # 원본 저장
                }

                # 제목이나 요약이 있는 경우만 추가
                if news_item["title"] or news_item["summary"]:
                    raw_news.append(news_item)
                    print(f"  ✓ {idx}. {news_item['title'][:50]}...")

            state["raw_news"] = raw_news
            state["messages"].append(
                AIMessage(
                    content=f"RSS 피드에서 {len(raw_news)}개의 뉴스를 수집했습니다."
                )
            )

            print(f"✅ [{self.name}] {len(raw_news)}개 뉴스 수집 완료\n")

        except Exception as e:
            error_msg = f"RSS 수집 중 오류: {str(e)}"
            print(f"❌ [{self.name}] {error_msg}")
            state["error_log"].append(error_msg)
            state["messages"].append(AIMessage(content=error_msg))

        return state


class NewsSummarizerAgent:
    """뉴스를 요약하는 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.name = "News Summarizer"
        self.llm = llm
        self.system_prompt = """당신은 전문 뉴스 요약 전문가입니다. 
        주어진 뉴스를 핵심만 간결하게 2-3문장으로 요약해주세요.
        - 사실만을 전달하고 추측은 피하세요
        - 중요한 숫자나 날짜는 포함하세요
        - 명확하고 이해하기 쉽게 작성하세요"""

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                HumanMessagePromptTemplate.from_template(
                    "제목: {title}\n내용: {content}\n\n위 뉴스를 2-3문장으로 요약해주세요:"
                ),
            ]
        )

    async def summarize_single_news(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """단일 뉴스 요약"""
        try:
            # 내용이 너무 짧으면 원본 사용
            if len(news_item["summary"]) < 50:
                return {**news_item, "ai_summary": news_item["summary"]}

            chain = self.prompt | self.llm
            summary_response = await chain.ainvoke(
                {
                    "title": news_item["title"],
                    "content": news_item["raw_summary"][:500],  # 너무 긴 텍스트 방지
                }
            )

            summary = summary_response.content.strip()

            return {
                **news_item,
                "ai_summary": summary if summary else news_item["summary"],
            }

        except Exception as e:
            print(
                f"  ⚠️ [{self.name}] 요약 오류 (ID: {news_item['id']}): {str(e)[:50]}..."
            )
            return {
                **news_item,
                "ai_summary": news_item["summary"],  # 오류 시 원본 사용
            }

    async def summarize_news(self, state: NewsState) -> NewsState:
        """모든 뉴스를 비동기로 요약"""
        print(f"\n📝 [{self.name}] 뉴스 요약 시작...")

        # 배치 처리를 위해 10개씩 묶어서 처리
        batch_size = 10
        summarized_news = []
        total_news = len(state["raw_news"])

        for i in range(0, total_news, batch_size):
            batch = state["raw_news"][i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_news + batch_size - 1) // batch_size

            print(f"  🔄 배치 {batch_num}/{total_batches} 처리 중...")

            tasks = [self.summarize_single_news(news) for news in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 예외 처리
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    print(f"    ⚠️ 뉴스 {batch[idx]['id']} 요약 실패")
                    summarized_news.append(
                        {**batch[idx], "ai_summary": batch[idx]["summary"]}
                    )
                else:
                    summarized_news.append(result)

            # API 속도 제한 대응
            if i + batch_size < total_news:
                await asyncio.sleep(0.5)

        state["summarized_news"] = summarized_news
        state["messages"].append(
            AIMessage(content=f"{len(summarized_news)}개의 뉴스 요약을 완료했습니다.")
        )

        print(f"✅ [{self.name}] 요약 완료\n")
        return state


class NewsOrganizerAgent:
    """뉴스를 카테고리별로 정리하는 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.name = "News Organizer"
        self.llm = llm
        self.categories = [
            "정치",
            "경제",
            "사회",
            "문화/연예",
            "IT/과학",
            "스포츠",
            "국제",
            "생활/건강",
            "기타",
        ]

        self.system_prompt = f"""당신은 뉴스 분류 전문가입니다.
        주어진 뉴스를 다음 카테고리 중 하나로 정확히 분류해주세요:
        {", ".join(self.categories)}
        
        반드시 위 카테고리 중 하나만 선택하세요."""

        self.categorize_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                HumanMessagePromptTemplate.from_template(
                    "제목: {title}\n요약: {summary}\n\n이 뉴스의 카테고리:"
                ),
            ]
        )

    async def categorize_single_news(
        self, news_item: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """단일 뉴스의 카테고리 판단"""
        try:
            chain = self.categorize_prompt | self.llm
            response = await chain.ainvoke(
                {
                    "title": news_item["title"],
                    "summary": news_item.get("ai_summary", news_item["summary"]),
                }
            )

            category = response.content.strip()

            # 유효한 카테고리인지 확인
            if category not in self.categories:
                # 키워드 기반 분류 (폴백)
                title_lower = news_item["title"].lower()
                if any(
                    word in title_lower
                    for word in ["대통령", "국회", "정치", "선거", "정당"]
                ):
                    category = "정치"
                elif any(
                    word in title_lower
                    for word in ["경제", "금융", "주식", "부동산", "기업"]
                ):
                    category = "경제"
                elif any(
                    word in title_lower for word in ["ai", "it", "기술", "과학", "연구"]
                ):
                    category = "IT/과학"
                elif any(
                    word in title_lower
                    for word in ["연예", "문화", "예술", "영화", "드라마"]
                ):
                    category = "문화/연예"
                else:
                    category = "기타"

            return category, news_item

        except Exception as e:
            print(
                f"  ⚠️ [{self.name}] 카테고리 분류 오류 (ID: {news_item['id']}): {str(e)[:50]}..."
            )
            return "기타", news_item

    async def organize_news(self, state: NewsState) -> NewsState:
        """뉴스를 카테고리별로 정리"""
        print(f"\n📊 [{self.name}] 뉴스 분류 시작...")

        # 배치 처리
        batch_size = 10
        results = []
        total_news = len(state["summarized_news"])

        for i in range(0, total_news, batch_size):
            batch = state["summarized_news"][i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_news + batch_size - 1) // batch_size

            print(f"  🔄 배치 {batch_num}/{total_batches} 분류 중...")

            tasks = [self.categorize_single_news(news) for news in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(("기타", batch[0]))  # 오류 시 기타로 분류
                else:
                    results.append(result)

            if i + batch_size < total_news:
                await asyncio.sleep(0.3)

        # 카테고리별로 그룹화
        categorized = defaultdict(list)
        for category, news in results:
            categorized[category].append(news)

        # 카테고리별 통계 출력
        print("\n  📈 카테고리별 분포:")
        for category in self.categories:
            count = len(categorized.get(category, []))
            if count > 0:
                print(f"    • {category}: {count}건")

        state["categorized_news"] = dict(categorized)
        state["messages"].append(
            AIMessage(content=f"뉴스를 {len(categorized)}개 카테고리로 분류했습니다.")
        )

        print(f"✅ [{self.name}] 분류 완료\n")
        return state


class ReportGeneratorAgent:
    """최종 보고서를 생성하는 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.name = "Report Generator"
        self.llm = llm

    async def generate_report(self, state: NewsState) -> NewsState:
        """최종 보고서 생성"""
        print(f"\n📄 [{self.name}] 보고서 생성 시작...")

        # 현재 시간
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")

        # 카테고리별 뉴스 수 계산
        category_stats = {
            cat: len(news_list) for cat, news_list in state["categorized_news"].items()
        }

        # 전체 통계
        total_news = sum(category_stats.values())

        report = f"""# 📰 Google News 한국 뉴스 AI 요약 리포트

## 📅 기본 정보
- **수집 시간**: {current_time}
- **RSS 소스**: Google News Korea
- **수집 뉴스**: {len(state["raw_news"])}건
- **처리 완료**: {total_news}건

## 📊 카테고리별 뉴스 분포

| 카테고리 | 뉴스 수 | 비율 |
|---------|--------|------|
"""

        # 카테고리별 통계 테이블
        for category, count in sorted(
            category_stats.items(), key=lambda x: x[1], reverse=True
        ):
            if count > 0:
                percentage = (count / total_news) * 100
                report += f"| {category} | {count}건 | {percentage:.1f}% |\n"

        report += "\n---\n\n"

        # 카테고리별 주요 뉴스
        report += "## 📰 카테고리별 주요 뉴스\n\n"

        # 카테고리별로 정렬하여 출력
        categories_order = [
            "정치",
            "경제",
            "사회",
            "국제",
            "IT/과학",
            "문화/연예",
            "스포츠",
            "생활/건강",
            "기타",
        ]

        for category in categories_order:
            if (
                category in state["categorized_news"]
                and state["categorized_news"][category]
            ):
                news_list = state["categorized_news"][category]
                report += f"### 🔹 {category} ({len(news_list)}건)\n\n"

                # 상위 5개 뉴스만 표시
                for i, news in enumerate(news_list, 1):
                    # 시간 포맷 개선
                    try:
                        pub_date = news["published"]
                        if pub_date:
                            # 간단한 날짜 형식으로 변환 시도
                            pub_date = pub_date.split("GMT")[0].strip()
                    except Exception:
                        pub_date = "날짜 정보 없음"

                    report += f"""#### {i}. {news["title"]}

- **📰 출처**: {news["source"]}
- **📅 발행**: {pub_date}
- **📝 요약**: {news.get("ai_summary", news["summary"])}
- **🔗 링크**: [기사 보기]({news["link"]})

"""
                report += "---\n\n"

        # 오류 로그가 있으면 추가
        if state.get("error_log"):
            report += "\n## ⚠️ 처리 중 발생한 오류\n\n"
            for error in state["error_log"]:
                report += f"- {error}\n"

        # 푸터
        report += """
---

## 📌 참고사항
- 이 보고서는 AI(LangGraph + LangChain)를 활용하여 자동으로 생성되었습니다.
- 뉴스 요약은 OpenAI GPT 모델을 사용하여 작성되었습니다.
- 카테고리 분류는 AI가 제목과 내용을 분석하여 자동으로 수행했습니다.
- 상세한 내용은 각 뉴스의 원문 링크를 참조하시기 바랍니다.

*Generated by Multi-Agent News Processing System*
"""

        state["final_report"] = report
        state["messages"].append(AIMessage(content="최종 보고서가 생성되었습니다."))

        print(f"✅ [{self.name}] 보고서 생성 완료")
        return state


# 워크플로우 정의
def create_news_workflow(llm: ChatOpenAI):
    """뉴스 처리 워크플로우 생성"""

    # 에이전트 인스턴스 생성
    collector = RSSCollectorAgent()
    summarizer = NewsSummarizerAgent(llm)
    organizer = NewsOrganizerAgent(llm)
    reporter = ReportGeneratorAgent(llm)

    # 상태 그래프 생성
    workflow = StateGraph(NewsState)

    # 노드 추가
    workflow.add_node("collect", collector.collect_rss)
    workflow.add_node("summarize", summarizer.summarize_news)
    workflow.add_node("organize", organizer.organize_news)
    workflow.add_node("report", reporter.generate_report)

    # 엣지 정의
    workflow.set_entry_point("collect")
    workflow.add_edge("collect", "summarize")
    workflow.add_edge("summarize", "organize")
    workflow.add_edge("organize", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


# 실행 함수
async def process_google_news_rss_async():
    """Google News RSS 처리 실행 (비동기 버전)"""

    # OpenAI LLM 초기화
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        max_tokens=150,  # 요약 길이 제한
    )

    # 워크플로우 생성
    app = create_news_workflow(llm)

    # 초기 상태 설정
    initial_state = {
        "messages": [HumanMessage(content="Google News RSS 처리를 시작합니다.")],
        "rss_url": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
        "raw_news": [],
        "summarized_news": [],
        "categorized_news": {},
        "final_report": "",
        "error_log": [],
    }

    # 워크플로우 실행
    print("\n" + "=" * 60)
    print("🚀 Google News AI 멀티에이전트 시스템 시작")
    print("=" * 60)

    try:
        # 비동기 실행
        final_state = await app.ainvoke(initial_state)

        # 결과 출력
        print("\n" + "=" * 60)
        print("📋 최종 보고서")
        print("=" * 60 + "\n")

        # 보고서 내용 출력 (일부만)
        report_preview = final_state["final_report"][:1000] + "..."
        print(report_preview)

        # 결과를 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_report_{timestamp}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_state["final_report"])

        print(f"\n✅ 전체 보고서가 '{filename}' 파일로 저장되었습니다.")
        print(f"📊 처리 완료: {len(final_state['summarized_news'])}개 뉴스")

        return final_state

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback

        traceback.print_exc()
        raise e
    finally:
        # 이벤트 루프 정리
        await asyncio.sleep(0.1)


# 동기 실행 함수
def run_news_processor():
    """뉴스 처리기 실행 (동기 버전)"""
    try:
        # 새 이벤트 루프 생성 및 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(process_google_news_rss_async())
        return result
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {str(e)}")
    finally:
        # 이벤트 루프 정리
        try:
            loop.close()
        except Exception:
            pass


# 메인 실행
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         Google News AI 멀티에이전트 시스템 v2.0               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  RSS 수집 → AI 요약 → 카테고리 분류 → 리포트 생성                ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # 필요한 패키지 확인
    print("📦 필요한 패키지:")
    print("   pip install langchain langgraph langchain-openai feedparser")
    print()

    # 실행
    run_news_processor()

# Jupyter Notebook에서 사용할 경우:
# await process_google_news_rss_async("your-api-key")
