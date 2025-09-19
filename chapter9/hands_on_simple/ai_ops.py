from __future__ import annotations

import asyncio
from typing import Dict, Iterable, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import Config

SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """당신은 압축적인 한국어 뉴스 요약 전문가입니다.
            주요 사실과 수치를 유지하며 2-3문장으로 간결하게 정리하세요.
            추측은 피하고, 원문 톤을 유지해주세요.""",
        ),
        (
            "human",
            "제목: {title}\n본문: {content}\n\n한글 2-3문장으로 핵심만 요약하세요.",
        ),
    ]
)

CATEGORIZE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """당신은 한국 뉴스 카테고리 분류 전문가입니다.
            다음 중에서 가장 알맞은 하나를 정확히 선택하세요:
            {categories}
            다른 설명 없이 카테고리 이름만 답변합니다.""",
        ),
        (
            "human",
            "제목: {title}\n요약: {summary}\n\n이 뉴스의 카테고리는?",
        ),
    ]
)


async def _summarize_single(chain, article: Dict) -> str:
    content = article.get("content", "")
    if len(content.strip()) < 20:
        return content.strip()
    response = await chain.ainvoke(
        {
            "title": article.get("title", ""),
            "content": content[: Config.SUMMARY_MAX_CHARS],
        }
    )
    return response.content.strip()


async def _categorize_single(chain, article: Dict) -> str:
    response = await chain.ainvoke(
        {
            "title": article.get("title", ""),
            "summary": article.get("summary", article.get("content", "")),
        }
    )
    return response.content.strip()


async def enrich_with_ai(articles: List[Dict]) -> List[Dict]:
    """Use OpenAI to summarise and categorise each article."""
    llm = ChatOpenAI(
        model=Config.MODEL_NAME,
        max_tokens=Config.MAX_TOKENS,
        api_key=Config.OPENAI_API_KEY,
    )

    summary_chain = SUMMARY_PROMPT | llm
    categorize_chain = CATEGORIZE_PROMPT.partial(
        categories=", ".join(Config.CATEGORIES)
    ) | llm

    batch_size = Config.BATCH_SIZE
    enriched: List[Dict] = []

    for offset in range(0, len(articles), batch_size):
        batch = articles[offset : offset + batch_size]

        summary_tasks = [
            asyncio.create_task(_summarize_single(summary_chain, article))
            for article in batch
        ]
        summaries = await asyncio.gather(*summary_tasks, return_exceptions=True)

        batch_with_summaries = []
        for article, summary in zip(batch, summaries):
            if isinstance(summary, Exception):
                summary_text = article.get("content", "")
            else:
                summary_text = summary or article.get("content", "")
            batch_with_summaries.append({**article, "summary": summary_text})

        category_tasks = [
            asyncio.create_task(_categorize_single(categorize_chain, article))
            for article in batch_with_summaries
        ]
        categories = await asyncio.gather(*category_tasks, return_exceptions=True)

        for article, category in zip(batch_with_summaries, categories):
            clean_category = (
                category.strip()
                if isinstance(category, str)
                else article.get("category_hint", "기타")
            )
            if clean_category not in Config.CATEGORIES:
                clean_category = "기타"
            enriched.append({**article, "category": clean_category})

    return enriched


def group_by_category(articles: Iterable[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {category: [] for category in Config.CATEGORIES}
    for article in articles:
        category = article.get("category", "기타")
        grouped.setdefault(category, []).append(article)
    return grouped
