import os
import logging
import asyncio
from datetime import datetime
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from workflow import create_news_workflow
from config import Config
from state import NewsState


logger = logging.getLogger(__name__)


async def process_news_async() -> NewsState:
    """뉴스 처리 비동기 함수"""

    # API 키 확인
    if not Config.validate():
        raise ValueError("유효한 API 키가 필요합니다.")

    # LLM 초기화
    llm = ChatOpenAI(
        model=Config.MODEL_NAME,
        temperature=Config.TEMPERATURE,
        max_tokens=Config.MAX_TOKENS,
        api_key=Config.OPENAI_API_KEY,
    )

    # 워크플로우 생성
    app = create_news_workflow(llm)

    # 초기 상태 설정
    initial_state: NewsState = {
        "messages": [HumanMessage(content="Google News RSS 처리를 시작합니다.")],
        "rss_url": Config.RSS_URL,
        "raw_news": [],
        "summarized_news": [],
        "categorized_news": {},
        "final_report": "",
        "error_log": [],
    }

    print("\n" + "=" * 60)
    print("뉴스 처리 시작")
    print("=" * 60)

    try:
        # 워크플로우 실행
        final_state = await app.ainvoke(initial_state)

        # 결과 저장
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(Config.OUTPUT_DIR, f"news_report_{timestamp}.md")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_state["final_report"])

        # 결과 출력
        print("\n" + "=" * 60)
        print("처리 완료")
        print("=" * 60)
        print(f"\n보고서가 저장되었습니다: {filename}")
        print(f"처리된 뉴스: {len(final_state['summarized_news'])}건")

        # 간단한 미리보기
        print("\n보고서 미리보기:")
        print("-" * 60)
        preview = final_state["final_report"][:500] + "..."
        print(preview)

        return final_state

    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        logger.exception("뉴스 처리 중 오류 발생")


def main():
    """메인 함수"""

    # 배너 출력
    print("""
Google News AI 멀티에이전트 시스템 v2.0
RSS 수집 → AI 요약 → 카테고리 분류 → 리포트 생성
""")

    try:
        # 이벤트 루프 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_news_async())

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n실행 중 오류 발생: {str(e)}")
    finally:
        try:
            loop.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
