import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# GEMINI API 키 가져오기
api_key = os.environ.get("GOOGLE_API_KEY")
client = OpenAI(
    api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def get_chat_completion(
    prompt,
    model="gemini-2.5-flash",  # 제미나이 모델을 사용
):
    # Chat Completion API 호출
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "당신은 친절하고 도움이 되는 AI 비서입니다."},
            {"role": "user", "content": prompt},
        ],
    )

    # 응답 텍스트 반환
    return response.choices[0].message.content


if __name__ == "__main__":
    # 사용자 입력 받기
    user_prompt = input("AI에게 물어볼 질문을 입력하세요: ")
    # AI 응답 받기
    response = get_chat_completion(user_prompt)
    print("\nAI 응답:")
    print(response)
