import os
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 환경변수 로드
load_dotenv()

# OpenAI API 키 가져오기
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 API 키를 추가해주세요.")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=api_key)

def get_chat_completion(prompt, model="o3-mini"):
    """
    OpenAI Chat Completion API를 사용 
    
    Args:
        prompt (str): AI에게 전달할 메시지
        model (str): 사용할 모델 (기본값: gpt-4o-mini)
    
    Returns:
        str: AI의 응답 텍스트
    """
    try:
        # Chat Completion API 호출
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 친절하고 도움이 되는 AI 비서입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # 응답의 창의성 조절 (0: 결정적, 1: 창의적)
        )
        
        # 응답 텍스트 반환
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"API 호출 중 오류가 발생했습니다: {e}")
        return None

if __name__ == "__main__":
    # 사용자 입력 받기
    user_prompt = input("AI에게 물어볼 질문을 입력하세요: ")
    
    # AI 응답 받기
    response = get_chat_completion(user_prompt)
    
    # 결과 출력
    if response:
        print("\nAI 응답:")
        print(response)
    else:
        print("응답을 받지 못했습니다.")
