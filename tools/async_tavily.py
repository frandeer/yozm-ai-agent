"""
비동기 Tavily 검색 도구

기존 TavilySearch를 비동기로 감싸서 여러 검색을 동시에 실행할 수 있게 해주는 재사용 가능한 래퍼 클래스입니다.

사용 예시:
    # 기본 사용법
    from tools.async_tavily import create_async_tavily

    async_tool = create_async_tavily(api_key="your_key", max_results=5)

    # 단일 검색
    result = await async_tool.search_async("오봉저수지")

    # 여러 검색 동시 실행
    results = await async_tool.search_multiple_async(["쿼리1", "쿼리2", "쿼리3"])
"""

import asyncio
from typing import List, Union, Optional, Any
from langchain_core.tools import BaseTool
from pydantic import Field
from .tavily import TavilySearch


class AsyncTavilyWrapper(BaseTool):
    """
    TavilySearch를 비동기로 감싸는 래퍼 클래스

    기존 TavilySearch 도구를 비동기적으로 실행할 수 있게 해주며,
    여러 검색을 동시에 처리하여 성능을 향상시킵니다.
    """

    name: str = "async_tavily_search"
    description: str = (
        "비동기 웹 검색 도구. 여러 검색을 동시에 실행하여 빠른 결과를 제공합니다. "
        "단일 검색 또는 여러 검색을 리스트로 입력할 수 있습니다."
    )
    tavily_tool: TavilySearch = Field(description="래핑할 TavilySearch 인스턴스")

    def __init__(self, tavily_tool: TavilySearch, **kwargs):
        """
        AsyncTavilyWrapper 초기화

        Args:
            tavily_tool (TavilySearch): 래핑할 TavilySearch 인스턴스
        """
        super().__init__(tavily_tool=tavily_tool, **kwargs)

    def _run(self, query: Union[str, List[str]]) -> Union[str, List[str]]:
        """BaseTool의 _run 메서드 구현 (동기 버전)"""
        if isinstance(query, str):
            return self.tavily_tool._run(query)
        else:
            return [self.tavily_tool._run(q) for q in query]

    async def search_async(self, query: str) -> str:
        """
        단일 검색을 비동기로 실행

        Args:
            query (str): 검색 쿼리

        Returns:
            str: 검색 결과
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.tavily_tool._run, query)
        return result

    async def search_multiple_async(self, queries: List[str]) -> List[str]:
        """
        여러 검색을 동시에 비동기로 실행

        Args:
            queries (List[str]): 검색 쿼리 리스트

        Returns:
            List[str]: 검색 결과 리스트
        """
        tasks = [self.search_async(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 예외 처리된 결과를 문자열로 변환
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(f"검색 실패 ({queries[i]}): {str(result)}")
            else:
                processed_results.append(result)

        return processed_results

    async def invoke_async(self, query: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        비동기 invoke 메서드

        Args:
            query: 단일 쿼리 문자열 또는 쿼리 리스트

        Returns:
            단일 결과 또는 결과 리스트
        """
        if isinstance(query, str):
            return await self.search_async(query)
        else:
            return await self.search_multiple_async(query)


def create_async_tavily(
    api_key: Optional[str] = None,
    max_results: int = 3,
    **kwargs: Any
) -> AsyncTavilyWrapper:
    """
    AsyncTavilyWrapper 인스턴스를 생성하는 팩토리 함수

    재사용 가능한 비동기 Tavily 검색 도구를 쉽게 생성할 수 있습니다.

    Args:
        api_key (str, optional): Tavily API 키. None이면 환경변수에서 가져옴
        max_results (int): 최대 검색 결과 수 (기본값: 3)
        **kwargs: TavilySearch에 전달할 추가 인자
                  - include_domains: 포함할 도메인 리스트
                  - exclude_domains: 제외할 도메인 리스트
                  - topic: "general" 또는 "news"
                  - search_depth: "basic" 또는 "advanced"
                  - include_raw_content: 원본 콘텐츠 포함 여부

    Returns:
        AsyncTavilyWrapper: 비동기 Tavily 검색 도구

    Example:
        >>> # 기본 사용
        >>> tool = create_async_tavily()
        >>>
        >>> # 고급 설정
        >>> tool = create_async_tavily(
        ...     api_key="your_key",
        ...     max_results=5,
        ...     topic="news",
        ...     search_depth="advanced"
        ... )
    """
    import os

    if api_key is None:
        api_key = os.environ.get("TAVILY_API_KEY", None)

    tavily_tool = TavilySearch(
        api_key=api_key,
        max_results=max_results,
        **kwargs
    )

    return AsyncTavilyWrapper(tavily_tool=tavily_tool)


# 편의를 위한 별칭 함수들
def create_async_tavily_news(
    api_key: Optional[str] = None,
    max_results: int = 5,
    days: int = 7
) -> AsyncTavilyWrapper:
    """뉴스 검색에 최적화된 비동기 Tavily 도구 생성"""
    return create_async_tavily(
        api_key=api_key,
        max_results=max_results,
        topic="news",
        days=days,
        search_depth="advanced"
    )


def create_async_tavily_general(
    api_key: Optional[str] = None,
    max_results: int = 3
) -> AsyncTavilyWrapper:
    """일반 검색에 최적화된 비동기 Tavily 도구 생성"""
    return create_async_tavily(
        api_key=api_key,
        max_results=max_results,
        topic="general",
        search_depth="basic"
    )