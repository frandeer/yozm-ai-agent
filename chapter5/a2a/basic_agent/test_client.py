"""Test client for Basic Hello World A2A Agent."""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import httpx

sys.path.append(str(Path(__file__).parent.parent))

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
    SendMessageResponse,
)

from shared.utils import create_user_message
from a2a.utils import get_message_text


async def test_basic_agent():
    """Test the basic Hello World agent with various messages."""
    base_url = "http://localhost:9999"

    print("Basic Hello World A2A Agent 테스트 시작...")
    print(f"서버 URL: {base_url}")
    print("-" * 50)

    async with httpx.AsyncClient() as httpx_client:
        try:
            # Initialize A2A card resolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=base_url,
            )

            # Get agent card
            print("에이전트 카드를 가져오는 중...")
            agent_card = await resolver.get_agent_card()
            print(f"에이전트 이름: {agent_card.name}")
            print(f"에이전트 설명: {agent_card.description}")
            print(f"지원 스킬: {[skill.name for skill in agent_card.skills]}")
            print()

            # Create A2A client
            # client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)
            client = await A2AClient.get_client_from_agent_card_url(
                base_url=base_url,
                httpx_client=httpx_client,
            )


            # Test messages
            test_messages = [
                "안녕하세요",
                "날씨가 어때요?",
                "고마워요",
                "이름이 뭔가요?",
                "오늘 기분이 어때요?",
            ]

            # Test non-streaming messages
            print("=== 비스트리밍 메시지 테스트 ===")
            for i, message_text in enumerate(test_messages, 1):
                print(f"\n{i}. 사용자: {message_text}")

                # Create message request
                user_message = create_user_message(message_text)
                request = SendMessageRequest(
                    id=str(uuid4()), params=MessageSendParams(message=user_message)
                )

                # Send message
                response: SendMessageResponse = await client.send_message(request)
                message_text = get_message_text(
                    response.root.result
                )  # Ensure message text is set
                print(message_text)

            print("\n" + "=" * 50)

            # Test streaming messages
            print("=== 스트리밍 메시지 테스트 ===")
            for i, message_text in enumerate(
                test_messages[:3], 1
            ):  # Test first 3 messages
                print(f"\n{i}. 사용자: {message_text}")

                # Create streaming message request
                user_message = create_user_message(message_text)
                streaming_request = SendStreamingMessageRequest(
                    id=str(uuid4()), params=MessageSendParams(message=user_message)
                )

                # Send streaming message
                print("   에이전트 (스트리밍): ", end="", flush=True)
                stream_response = client.send_message_streaming(streaming_request)
                async for stream_response in stream_response:
                    print(get_message_text(stream_response.root.result))
                print()  # New line after streaming

            print("\n테스트 완료!")

        except Exception as e:
            print(f"테스트 중 오류 발생: {e}")
            print("서버가 실행 중인지 확인해주세요.")
            print("서버 실행: python basic_agent/__main__.py")


async def main():
    """Main function to run the test."""
    await test_basic_agent()


if __name__ == "__main__":
    asyncio.run(main())
