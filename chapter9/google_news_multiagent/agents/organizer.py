# agents/organizer.py
import asyncio
from typing import Dict, Any, Tuple
from collections import defaultdict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from state import NewsState
from config import Config


class NewsOrganizerAgent:
    """뉴스를 카테고리별로 정리하는 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.name = "News Organizer"
        self.llm = llm
        self.categories = Config.NEWS_CATEGORIES

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
    ) -> Tuple[str, Dict[str, Any]]:
        """단일 뉴스의 카테고리 판단"""

        chain = self.categorize_prompt | self.llm
        response = await chain.ainvoke(
            {
                "title": news_item["title"],
                "summary": news_item.get("ai_summary", news_item["content"]),
            }
        )

        category = response.content.strip()
        return category, news_item

    async def organize_news(self, state: NewsState) -> NewsState:
        """뉴스를 카테고리별로 정리"""
        print(f"\n[{self.name}] 뉴스 분류 시작...")

        # 배치 처리
        batch_size = Config.BATCH_SIZE
        results = []
        total_news = len(state.summarized_news)

        for i in range(0, total_news, batch_size):
            batch = state.summarized_news[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_news + batch_size - 1) // batch_size

            print(f"  배치 {batch_num}/{total_batches} 분류 중...")

            tasks = [self.categorize_single_news(news) for news in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in enumerate(batch_results):
                results.append(result)

        # 카테고리별로 그룹화
        categorized = defaultdict(list)
        for result in results:
            if isinstance(result, Exception):
                print(f"    분류 작업 실패: {result}")
                continue
            category, news = result
            categorized[category].append(news)

        # 카테고리별 통계 출력
        print("\n  카테고리별 분포:")
        for category in self.categories:
            count = len(categorized.get(category, []))
            if count > 0:
                print(f"    {category}: {count}건")

        state.categorized_news = dict(categorized)
        state.messages.append(
            AIMessage(content=f"뉴스를 {len(categorized)}개 카테고리로 분류했습니다.")
        )

        print(f"[{self.name}] 분류 완료\n")
        return state
