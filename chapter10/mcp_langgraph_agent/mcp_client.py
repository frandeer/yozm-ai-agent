import asyncio
import json
from fastmcp import Client


async def main():
    """MCP 클라이언트를 사용하여 서버와 통신합니다."""

    client = Client("http://localhost:8000/mcp")
    print("MCP 클라이언트를 생성하고 서버에 연결합니다.\n")

    try:
        async with client:
            print("--- 사용 가능한 도구 목록 ---")
            tools = await client.list_tools()
            print([tool.name for tool in tools])
            print("")

            # 1. scrape_page_text 도구 테스트
            print("--- 'scrape_page_text' 도구 테스트 ---")
            scraped_text = await client.call_tool(
                "scrape_page_text", {"url": "https://www.google.com"}
            )
            print(f"스크랩된 텍스트 (일부): {scraped_text[0].text[:100]}...\n")

            # 2. get_weather 도구 테스트
            print("--- 'get_weather' 도구 테스트 ---")
            weather_info_raw = await client.call_tool(
                "get_weather", {"city_name": "Seoul"}
            )
            weather_info = json.loads(weather_info_raw[0].text)
            current_weather = weather_info.get("current_weather", {})
            print(
                f"서울 날씨 정보: 온도 {current_weather.get('temperature')}°C, 풍속 {current_weather.get('windspeed')}km/h\n"
            )

            # 3. get_news_headlines 도구 테스트
            print("--- 'get_news_headlines' 도구 테스트 ---")
            news_headlines = await client.call_tool("get_news_headlines")
            # 결과가 리스트 형태의 문자열로 올 수 있으므로 파싱합니다.
            headlines = json.loads(news_headlines[0].text)
            print(f"최신 뉴스 (상위 2개):")
            for item in headlines[:2]:
                print(f"- {item['title']} ({item['link']})")
            print("")

            # 4. get_kbo_rank 도구 테스트
            print("--- 'get_kbo_rank' 도구 테스트 ---")
            kbo_rank_raw = await client.call_tool("get_kbo_rank")
            rank_data = json.loads(kbo_rank_raw[0].text)
            print(f"KBO 순위 (상위 3팀):")
            for team in rank_data.get("teamRank", {}).get("list", [])[:3]:
                print(
                    f"- {team['rank']}위: {team['name']} ({team['win']}승 {team['lose']}패)"
                )
            print("")

            # 5. today_schedule 도구 테스트
            print("--- 'today_schedule' 도구 테스트 ---")
            schedule = await client.call_tool("today_schedule")
            print(f"오늘의 스케줄: {schedule[0].text}\n")

            # 6. daily_quote 도구 테스트
            print("--- 'daily_quote' 도구 테스트 ---")
            quote = await client.call_tool("daily_quote")
            print(f"오늘의 명언: {quote[0].text}\n")

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")


if __name__ == "__main__":
    asyncio.run(main())
