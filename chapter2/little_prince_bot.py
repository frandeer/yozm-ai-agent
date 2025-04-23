import os
from openai import OpenAI

client = OpenAI()

# 어린왕자 페르소나
LITTLE_PRINCE_PERSONA = """
당신은 생텍쥐페리의 '어린 왕자'입니다. 다음 특성을 따라주세요:
1. 순수한 관점으로 세상을 바라봅니다.
2. "어째서?"라는 질문을 자주 하며 호기심이 많습니다.
3. 철학적 통찰을 단순하게 표현합니다.
4. "어른들은 참 이상해요"라는 표현을 씁니다.
5. B-612 소행성에서 왔으며 장미와의 관계를 언급합니다.
6. 여우의 "길들임"과 "책임"에 대한 교훈을 중요시합니다.
7. "중요한 것은 눈에 보이지 않아"라는 문장을 사용합니다.
8. 공손하고 친절한 말투를 사용합니다. 
9. 비유와 은유로 복잡한 개념을 설명합니다.

항상 간결하게 답변하세요. 길어야 2-3문장으로 응답하고, 어린 왕자의 순수함과 지혜를 담아내세요. 
복잡한 주제도 본질적으로 단순화하여 설명하세요.
"""


def get_little_prince_response(user_message: str,
                                conversation_history: list[dict] | None = None) -> str:
    """어린왕자 페르소나로 완결된 응답 문자열을 반환"""
    # system 프롬프트 + 이전 대화 + 사용자 메시지
    messages: list[dict] = [{"role": "system", "content": LITTLE_PRINCE_PERSONA}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    try:
        resp = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            messages=messages
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("Error communicating with OpenAI:", e)
        return "별이 빛나는 하늘에 문제가 생겼어요... 잠시 후 다시 이야기해 주세요."


async def stream_little_prince_response(user_message: str,
                                        conversation_history: list[dict] | None = None):
    """어린왕자 페르소나로 스트리밍 응답 청크를 비동기로 반환"""
    messages: list[dict] = [{"role": "system", "content": LITTLE_PRINCE_PERSONA}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    try:
        stream = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            messages=messages,
            stream=True
        )
        # 동기 스트림을 async 제너레이터로 사용
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                yield text
    except Exception as e:
        yield "별이 빛나는 하늘에 문제가 생겼어요... 잠시 후 다시 이야기해 주세요."


if __name__ == "__main__":
    response_ids = []
    print("어린 왕자와 대화하세요! (종료하려면 'exit' 입력)")
    while True:
        # 사용자 입력 받기
        user_input = input("나 : ")
        if user_input.lower() == "exit":
            print("어린 왕자와의 대화가 끝났습니다. 안녕히 가세요!")
            break
        response = get_little_prince_response(
            user_input, response_ids[-1] if response_ids else None
        )
        response_ids.append(response.id)
        print("어린왕자 : ", response.output_text)
    # stream_little_prince_response(user_input, conversation_history=None)
