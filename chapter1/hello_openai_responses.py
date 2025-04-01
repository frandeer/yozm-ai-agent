#  OpenAI API를 사용하여 AI 응답을 받아오는 코드
from openai import OpenAI
client = OpenAI()  # OpenAI 클라이언트 초기화


def get_responses(prompt, model="gpt-4o-mini"):
    # ① 입력된 프롬프트에 대한 AI 응답을 받아오는 함수
    # prompt: 사용자 입력 텍스트
    # model: 사용할 AI 모델 (기본값: gpt-4o-mini)
    response = client.responses.create(
        model=model,  # 사용할 모델 지정
        tools=[{"type": "web_search_preview"}],  # ② 웹 검색 도구 활성화
        input=prompt  # 사용자 입력 전달
    )
    
    return response.output_text  # 텍스트 응답만 반환

if __name__ == '__main__':
    # ③ 스크립트가 직접 실행될 때 테스트 실행
    output = get_responses("영어 문장 한마디")  # "영어 문장 한마디"라는 프롬프트로 응답 요청
    print(output)  # 결과 출력