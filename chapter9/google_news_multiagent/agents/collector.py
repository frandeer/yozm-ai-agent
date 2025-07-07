# agents/collector.py
import asyncio
import feedparser
import httpx
from playwright.async_api import async_playwright

from langchain_core.messages import AIMessage

from state import NewsState
from utils import clean_html, truncate_text
from config import Config


class RSSCollectorAgent:
    """RSS 피드를 수집하는 에이전트"""

    def __init__(self):
        self.name = "RSS Collector"
        self.playwright = None
        self.browser = None

    async def setup_browser(self):
        """브라우저 한 번만 설정 (재사용)"""
        if not self.playwright:
            self.playwright = await async_playwright().__aenter__()
            self.browser = await self.playwright.chromium.launch(headless=False)

    async def extract_with_browser(self, url: str) -> str:
        """브라우저로 콘텐츠 추출"""
        if not self.browser:
            await self.setup_browser()

        page = await self.browser.new_page()

        # 불필요한 리소스 차단으로 속도 향상
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort()
        )

        try:
            # 리디렉션 후 콘텐츠 로딩을 위해 networkidle 사용하되 타임아웃 단축
            await page.goto(url, wait_until="networkidle", timeout=10000)
            url = page.url
            print(url)

            # 메인 콘텐츠 추출 (한줄로 간략화)
            content = await page.evaluate(
                '() => document.querySelector("main, article, .content, .post, .entry")?.innerText || document.body.innerText'
            )
            print("content==================================")
            print(content[:1000])
            return content

        except Exception as e:
            print(f"페이지 로딩 실패: {url}, 오류: {e}")
            return ""
        finally:
            await page.close()

    async def cleanup(self):
        """리소스 정리"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def track_navigation_async(self, google_news_url):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            navigation_complete = asyncio.Event()
            final_url = None

            # 네비게이션 핸들러
            async def on_navigation(frame):
                nonlocal final_url
                if frame == page.main_frame:
                    current_url = frame.url
                    if "news.google.com" not in current_url:
                        final_url = current_url
                        navigation_complete.set()

            page.on("framenavigated", on_navigation)

            # 페이지 로드
            await page.goto(google_news_url)

            # 네비게이션 완료 대기 (최대 10초)
            try:
                await asyncio.wait_for(navigation_complete.wait(), timeout=10)
                print(f"네비게이션 완료! 최종 URL: {final_url}")
                return final_url
            except asyncio.TimeoutError:
                print("네비게이션 타임아웃")

            await browser.close()

    async def collect_rss(self, state: NewsState) -> NewsState:
        """RSS 피드에서 뉴스를 수집"""
        print(f"\n[{self.name}] RSS 피드 수집 시작...")

        try:
            # ② RSS 피드 파싱
            feed = feedparser.parse(Config.RSS_URL)

            raw_news = []
            # ③ 설정된 최대 개수만큼 뉴스 처리
            for idx, entry in enumerate(feed.entries[: Config.MAX_NEWS_COUNT], 1):
                # ④ Playwright로 콘텐츠 추출
                link = entry.get("link")

                url = await self.track_navigation_async(
                    f"{link}&hl=ko&gl=KR&ceid=KR:ko"
                )
                result = httpx.get(url)
                summary = clean_html(result.text)
                print(summary)

                # ⑤ 뉴스 아이템 구조화
                news_item = {
                    "id": idx,
                    "title": clean_html(entry.get("title", "")),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": truncate_text(summary, 300),  # ⑥ 요약 길이 제한
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "raw_summary": summary,  # ⑦ 원본 보존
                }

                # ⑧ 유효성 검사 및 필터링
                if news_item["title"] or news_item["summary"]:
                    raw_news.append(news_item)
                    print(f"  {idx}. {news_item['title'][:50]}...")

            # ⑨ 상태 업데이트
            state.raw_news = raw_news
            state.messages.append(
                AIMessage(
                    content=f"RSS 피드에서 {len(raw_news)}개의 뉴스를 수집했습니다."
                )
            )

            print(f"[{self.name}] {len(raw_news)}개 뉴스 수집 완료\n")

        except Exception as e:
            # ⑩ 에러 처리 및 로깅
            error_msg = f"RSS 수집 중 오류: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            state.error_log.append(error_msg)
            state.messages.append(AIMessage(content=error_msg))

        finally:
            # ⑪ 리소스 정리
            await self.cleanup()

        return state
