# agents/reporter.py
from datetime import datetime
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

from models.state import NewsState
from config import Config
from utils.text_processing import format_date


class ReportGeneratorAgent:
    """최종 보고서를 생성하는 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.name = "Report Generator"
        self.llm = llm

    def _generate_statistics_table(
        self, category_stats: Dict[str, int], total_news: int
    ) -> str:
        """카테고리별 통계 테이블 생성"""
        table_header = "| 카테고리 | 뉴스 수 | 비율 |\n|---------|--------|------|\n"
        table_rows = [
            f"| {category} | {count}건 | {(count / total_news) * 100:.1f}% |"
            for category, count in sorted(
                category_stats.items(), key=lambda x: x[1], reverse=True
            )
            if count > 0
        ]
        return table_header + "\n".join(table_rows)

    def _generate_news_section(self, category: str, news_list: list) -> str:
        """카테고리별 뉴스 섹션 생성"""
        section_header = f"### {category} ({len(news_list)}건)\n\n"
        display_count = min(len(news_list), Config.NEWS_PER_CATEGORY)

        news_items = []
        for i, news in enumerate(news_list[:display_count], 1):
            pub_date = format_date(news.get("published", ""))
            news_item = f"""#### {i}. {news["title"]}

- **출처**: {news["source"]}
- **발행**: {pub_date}
- **요약**: {news.get("ai_summary", news["summary"])}
- **링크**: [기사 보기]({news["link"]})
"""
            news_items.append(news_item)

        section_body = "\n".join(news_items)

        remaining = len(news_list) - display_count
        section_footer = f"\n*... 외 {remaining}건의 뉴스*\n" if remaining > 0 else ""

        return f"{section_header}{section_body}{section_footer}"

    def _build_header(self, state: NewsState) -> str:
        """보고서 헤더 생성"""
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        total_processed = sum(len(v) for v in state["categorized_news"].values())
        return f"""# Google News 한국 뉴스 AI 요약 리포트

## 기본 정보
- **수집 시간**: {current_time}
- **RSS 소스**: Google News Korea
- **수집 뉴스**: {len(state["raw_news"])}건
- **처리 완료**: {total_processed}건"""

    def _build_statistics(self, state: NewsState) -> str:
        """통계 섹션 생성"""
        category_stats = {
            cat: len(news_list) for cat, news_list in state["categorized_news"].items()
        }
        total_news = sum(category_stats.values())
        if not total_news:
            return ""

        stats_table = self._generate_statistics_table(category_stats, total_news)
        return f"## 카테고리별 뉴스 분포\n\n{stats_table}"

    def _build_news_sections(self, state: NewsState) -> str:
        """모든 뉴스 섹션 생성"""
        sections = [
            self._generate_news_section(category, state["categorized_news"][category])
            for category in Config.NEWS_CATEGORIES
            if category in state["categorized_news"] and state["categorized_news"][category]
        ]
        if not sections:
            return ""

        return "## 카테고리별 주요 뉴스\n\n" + "\n---\n\n".join(sections)

    def _build_error_log(self, state: NewsState) -> str:
        """오류 로그 섹션 생성"""
        if not state.get("error_log"):
            return ""
        errors = "\n".join([f"- {error}" for error in state["error_log"]])
        return f"## 처리 중 발생한 오류\n\n{errors}"

    def _build_footer(self) -> str:
        """보고서 푸터 생성"""
        return """## 참고사항
- 이 보고서는 AI(LangGraph + LangChain)를 활용하여 자동으로 생성되었습니다.
- 뉴스 요약은 OpenAI GPT 모델을 사용하여 작성되었습니다.
- 카테고리 분류는 AI가 제목과 내용을 분석하여 자동으로 수행했습니다.
- 상세한 내용은 각 뉴스의 원문 링크를 참조하시기 바랍니다."""

    async def generate_report(self, state: NewsState) -> NewsState:
        """최종 보고서 생성"""
        print(f"\n[{self.name}] 보고서 생성 시작...")

        report_parts = [
            self._build_header(state),
            self._build_statistics(state),
            self._build_news_sections(state),
            self._build_error_log(state),
            self._build_footer(),
        ]

        # 비어 있지 않은 섹션만 필터링하여 최종 보고서 생성
        final_report = "\n\n---\n\n".join(filter(None, report_parts))

        state["final_report"] = final_report
        state["messages"].append(AIMessage(content="최종 보고서가 생성되었습니다."))

        print(f"[{self.name}] 보고서 생성 완료")
        return state
