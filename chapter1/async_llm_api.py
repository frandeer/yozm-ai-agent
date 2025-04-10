import asyncio
import os

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic


# ① 비동기 클라이언트 생성
openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
claude_client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


async def call_async_openai(prompt: str, model: str = "gpt-4o-mini") -> str:
    # ② await를 사용해 비동기적으로 API 응답을 기다림
    response = await openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


async def call_async_claude(prompt: str, model: str = "claude-3-5-haiku-latest") -> str:
    # ③ await를 사용해 비동기적으로 API 응답을 기다림
    response = await claude_client.messages.create(
        model=model, max_tokens=1000, messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


async def main():
    print("동시에 API 호출하기")
    prompt = "비동기 프로그래밍에 대해 2-3문장으로 설명해주세요."
    # ⑤ 비동기 함수 호출 시 코루틴 객체 반환(실행은 아직 안 됨)
    openai_task = call_async_openai(prompt)
    claude_task = call_async_claude(prompt)

    # ⑥ 두 API 호출을 병렬로 실행하고 둘 다 완료될 때까지 대기
    openai_response, claude_response = await asyncio.gather(openai_task, claude_task)
    print(f"OpenAI 응답: {openai_response}")
    print(f"Claude 응답: {claude_response}")


if __name__ == "__main__":
    asyncio.run(main())  # ⑦ 비동기 메인 함수를 이벤트 루프에서 실행
