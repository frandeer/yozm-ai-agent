import os
from dotenv import load_dotenv

load_dotenv() # .env 파일을 한 번 로드하여 환경 변수를 설정합니다.

def get_env_variable(key: str, default_value: str = None) -> str:
    """
    .env 파일 또는 시스템 환경 변수에서 지정된 키의 값을 가져옵니다.

    Args:
        key (str): 가져올 환경 변수의 키.
        default_value (str, optional): 환경 변수가 없을 경우 반환할 기본값. Defaults to None.

    Returns:
        str: 환경 변수의 값 또는 기본값.
    """
    value = os.getenv(key)
    if value is None and default_value is not None:
        return default_value
    elif value is None:
        raise ValueError(f"환경 변수 {key}가 설정되지 않았습니다.")
    return value
