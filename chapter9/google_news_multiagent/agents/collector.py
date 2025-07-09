import json
import re
import asyncio
from typing import Optional
from datetime import datetime, timedelta

import httpx
import feedparser
import trafilatura
from bs4 import BeautifulSoup

from state import NewsState


# 상수 정의
KST_OFFSET_HOURS = 9
GOOGLE_NEWS_BASE_URL = "https://news.google.com"
GOOGLE_NEWS_API_URL = f"{GOOGLE_NEWS_BASE_URL}/_/DotsSplashUi/data/batchexecute"

# 한국 뉴스 설정
KOREA_PARAMS = "&hl=ko&gl=KR&ceid=KR:ko"


class RSSCollectorAgent:
    """RSS 피드를 수집하는 에이전트"""

    def __init__(self):
        self.name = "RSS Collector"
        self.rss_url = f"{GOOGLE_NEWS_BASE_URL}/rss?{KOREA_PARAMS[1:]}"
        self.feed = None

    def load_feed(self) -> None:
        """RSS 피드를 로드합니다."""
        self.feed = feedparser.parse(self.rss_url)

    @staticmethod
    def convert_gmt_to_kst(gmt_time_str: str) -> str:
        """
        GMT 시간을 KST로 변환합니다.
        Args:
            gmt_time_str: GMT 시간 문자열 (예: "Mon, 01 Jan 2024 12:00:00 GMT")
        Returns:
            KST 시간 문자열 (예: "2024-01-01 21:00:00")
        """
        gmt_time = datetime.strptime(gmt_time_str, "%a, %d %b %Y %H:%M:%S GMT")
        kst_time = gmt_time + timedelta(hours=KST_OFFSET_HOURS)
        return kst_time.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def extract_actual_article_content(html_content):
        """
        실제 기사 내용을 Fusion.globalContent에서 추출합니다.
        """
        # Fusion.globalContent 찾기
        pattern = r"Fusion\.globalContent\s*=\s*({.*?});"
        match = re.search(pattern, html_content, re.DOTALL)

        if match:
            try:
                # JSON 파싱
                content_data = json.loads(match.group(1))

                # content_elements에서 텍스트 추출
                texts = []
                if "content_elements" in content_data:
                    for element in content_data["content_elements"]:
                        if element.get("type") == "text" and "content" in element:
                            texts.append(element["content"])

                return "\n\n".join(texts)
            except json.JSONDecodeError as e:
                return f"JSON 파싱 오류: {e}"

        return "기사 내용을 찾을 수 없습니다."

    async def extract_article_url(self, google_news_url: str) -> Optional[str]:
        """
        구글 뉴스 리디렉션 URL에서 실제 기사 URL을 추출합니다.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(google_news_url)
                soup = BeautifulSoup(response.text, "html.parser")

                data_element = soup.select_one("c-wiz[data-p]")
                if not data_element:
                    return None

                raw_data = data_element.get("data-p")
                json_data = json.loads(raw_data.replace("%.@.", '["garturlreq",'))
                payload = {
                    "f.req": json.dumps(
                        [
                            [
                                [
                                    "Fbv4je",
                                    json.dumps(json_data[:-6] + json_data[-2:]),
                                    "null",
                                    "generic",
                                ]
                            ]
                        ]
                    )
                }
                headers = {
                    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
                }

                api_response = await client.post(
                    GOOGLE_NEWS_API_URL, headers=headers, data=payload
                )
                cleaned_response = api_response.text.replace(")]}'", "")
                response_data = json.loads(cleaned_response)
                article_data = json.loads(response_data[0][2])
                article_url = article_data[1]
                return article_url

            except Exception as e:
                print(f"URL 추출 중 오류 발생: {e}")
                return None

    async def parse_entry(self, entry) -> dict[str, Optional[str]]:
        """
        RSS 피드 항목을 파싱합니다.

        Args:
            entry: feedparser 엔트리 객체

        Returns:
            파싱된 뉴스 정보 딕셔너리
        """
        # 구글 뉴스 리디렉션 URL 생성
        google_news_url = entry.link + KOREA_PARAMS

        # 실제 기사 URL 추출
        original_url = await self.extract_article_url(google_news_url)

        content = ""
        if original_url:
            downloaded = trafilatura.fetch_url(original_url)
            if "chosun.com" in original_url:
                content = self.extract_actual_article_content(downloaded)
            else:
                content = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_images=False,
                    include_links=False,
                    include_tables=True,
                    target_language="ko",
                    output_format="json",
                )

        return {
            "title": entry.title,
            "published_kst": self.convert_gmt_to_kst(entry.published),
            "source": entry.source.get("title", "Unknown"),
            "google_news_url": google_news_url,
            "original_url": original_url,
            "content": content,
        }

    async def parse_all_entries(self) -> list[dict[str, Optional[str]]]:
        """
        모든 RSS 피드 항목을 비동기적으로 파싱합니다.

        Returns:
            파싱된 뉴스 정보 리스트
        """
        if not self.feed:
            self.load_feed()

        # 모든 엔트리를 비동기적으로 처리
        tasks = [self.parse_entry(entry) for entry in self.feed.entries]
        results = await asyncio.gather(*tasks)

        return results

    async def collect_rss(self, state: NewsState) -> NewsState:
        """
        GoogleNewsParser를 사용하여 RSS 피드를 수집하고 상태를 업데이트합니다.
        """
        print("--- RSS 피드 수집 시작 ---")
        try:
            raw_news = await self.parse_all_entries()
            state.raw_news = raw_news
            print(f"총 {len(raw_news)}개의 뉴스 기사 수집 완료")
        except Exception as e:
            print(f"RSS 피드 수집 중 오류 발생: {e}")
            state.error_log.append(f"RSSCollectorAgent: {str(e)}")

        return state
