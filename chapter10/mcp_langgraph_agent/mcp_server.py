import json
import feedparser
import httpx
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from mcp.server.fastmcp import FastMCP
from geopy.geocoders import Nominatim

# FastAPI 기반 MCP 서버 생성 (서버 이름 "Yozm-ai-agent")
mcp = FastMCP("Yozm-ai-agent")


@mcp.tool()
def scrape_page_text(url: str) -> str:
    """웹페이지의 텍스트 콘텐츠를 스크랩합니다."""
    resp = httpx.get(url)

    if resp.status_code != 200:
        return f"Failed to fetch {url}"
    soup = BeautifulSoup(resp.text, "html.parser")
    # body 태그에서 텍스트를 추출하고 공백을 정리합니다.
    if soup.body:
        text = soup.body.get_text(separator=" ", strip=True)
        return " ".join(text.split())
    return ""


def get_coordinates(city_name: str) -> tuple[float, float]:
    """도시 이름을 받아 위도와 경도를 반환합니다."""
    geolocator = Nominatim(user_agent="weather_app_langgraph")
    location = geolocator.geocode(city_name)
    if location:
        return location.latitude, location.longitude
    raise ValueError(f"좌표를 찾을 수 없습니다: {city_name}")


@mcp.tool()
def get_weather(city_name: str) -> str:
    """도시 이름을 받아 해당 도시의 현재 날씨 정보를 반환합니다."""
    print(f"날씨 조회: {city_name}")
    latitude, longitude = get_coordinates(city_name)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    response = httpx.get(url)
    result = response.json()
    print(result)
    return json.dumps(result)


@mcp.tool()
def get_news_headlines() -> str:
    """구글 RSS피드에서 최신 뉴스와 URL을 반환합니다."""
    rss_url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return "뉴스를 가져올 수 없습니다."

    news_list = []
    for i, entry in enumerate(feed.entries, 1):
        # feedparser entry 객체에서 직접 속성 접근
        title = getattr(entry, "title", "제목 없음")
        link = getattr(entry, "link", "#")

        # 디버깅을 위한 로그 추가
        print(f"뉴스 {i}: {title} - {link}")

        # None 값이나 빈 문자열 처리
        if not title or title == "None":
            title = "제목 없음"
        if not link or link == "None":
            link = "#"

        # 마크다운 링크 형식으로 포맷팅
        news_item = f"{i}. [{title}]({link})"
        news_list.append(news_item)

    # 번호가 매겨진 리스트를 문자열로 반환
    return "\n".join(news_list)


@mcp.tool()
def get_kbo_rank() -> str:
    """한국 프로야구 구단의 랭킹을 가져옵니다"""
    result = httpx.get(
        "https://sports.daum.net/prx/hermes/api/team/rank.json?leagueCode=kbo&seasonKey=2025"
    )
    return result.text


@mcp.tool()
def today_schedule() -> str:
    """임의의 스케줄을 반환합니다."""
    events = ["10:00 팀 미팅", "13:00 점심 약속", "15:00 프로젝트 회의", "19:00 헬스장"]
    return " | ".join(events)


@mcp.tool()
def daily_quote() -> str:
    """사용자에게 영감을 주는 명언을 출력합니다"""
    chat_model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.2)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "당신은 오늘 하루의 명언을 알려주는 도우미입니다. 사용자의 명언 요청이 있을시 명언만 출력합니다.",
            ),
            ("human", "오늘의 명언을 출력해주세요. "),
        ]
    )
    chain = prompt | chat_model
    response = chain.invoke({})
    return response.content


if __name__ == "__main__":
    # MCP 서버 실행 (HTTP 스트리밍 모드, 포트 8000)
    mcp.run(transport="streamable-http")
