# agents/collector.py
import feedparser
from langchain_core.messages import AIMessage

from models.state import NewsState
from utils.text_processing import clean_html, truncate_text
from config import Config


class RSSCollectorAgent:
    """RSS 피드를 수집하는 에이전트"""
    
    def __init__(self):
        self.name = "RSS Collector"
        self.rss_url = Config.RSS_URL
    
    async def collect_rss(self, state: NewsState) -> NewsState:
        """RSS 피드에서 뉴스를 수집"""
        print(f"\n[{self.name}] RSS 피드 수집 시작...")
        
        try:
            # RSS 피드 파싱
            feed = feedparser.parse(self.rss_url)
                        
            raw_news = []
            for idx, entry in enumerate(feed.entries[:Config.MAX_NEWS_COUNT], 1):
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
                    print(f"  {idx}. {news_item['title'][:50]}...")
            
            state["raw_news"] = raw_news
            state["messages"].append(
                AIMessage(
                    content=f"RSS 피드에서 {len(raw_news)}개의 뉴스를 수집했습니다."
                )
            )
            
            print(f"[{self.name}] {len(raw_news)}개 뉴스 수집 완료\n")
            
        except Exception as e:
            error_msg = f"RSS 수집 중 오류: {str(e)}"
            print(f"[{self.name}] {error_msg}")
            state["error_log"].append(error_msg)
            state["messages"].append(AIMessage(content=error_msg))
        
        return state
