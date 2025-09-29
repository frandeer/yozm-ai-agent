import os
from .get_key import get_env_variable # 상대 경로로 get_key.py에서 함수 import

def langsmith(project_name=None, set_enable=True):

    if set_enable:
        # get_env_variable 함수를 사용하여 환경 변수를 가져옵니다.
        langchain_key = get_env_variable("LANGCHAIN_API_KEY", "")
        langsmith_key = get_env_variable("LANGSMITH_API_KEY", "")

        # 더 긴 API 키 선택
        if len(langchain_key.strip()) >= len(langsmith_key.strip()):
            result = langchain_key
        else:
            result = langsmith_key

        if result.strip() == "":
            print(
                "LangChain/LangSmith API Key가 설정되지 않았습니다."
            )
            return

        os.environ["LANGSMITH_ENDPOINT"] = (
            "https://api.smith.langchain.com"  # LangSmith API 엔드포인트
        )
        os.environ["LANGSMITH_TRACING"] = "true"  # true: 활성화
        os.environ["LANGSMITH_PROJECT"] = project_name
        # 여기에 로켓 아이콘 추가
        print(f"🚀 [LangSmith] Start: {project_name}")
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        # 여기에 정지 아이콘 또는 다른 아이콘 추가
        print("⏹️ [LangSmith] Tracking Disabled")


def env_variable(key, value):
    os.environ[key] = value