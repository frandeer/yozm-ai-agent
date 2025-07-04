# config.py
import os


class Config:
    """프로젝트 설정 관리 클래스"""

    # OpenAI 설정
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = "gpt-4.1-mini"
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 150

    ROOT_DIR: str = os.path.dirname(os.path.abspath(__file__))

    # RSS 설정
    RSS_URL: str = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    MAX_NEWS_COUNT: int = 60

    # 배치 처리 설정
    BATCH_SIZE: int = 10

    # 카테고리 설정
    NEWS_CATEGORIES: list[str] = [
        "정치",
        "경제",
        "사회",
        "문화/연예",
        "IT/과학",
        "스포츠",
        "국제",
        "생활/건강",
        "기타",
    ]

    # 보고서 설정
    NEWS_PER_CATEGORY: int = 30  # 카테고리별 표시할 뉴스 수

    # 파일 설정
    OUTPUT_DIR: str = f"{ROOT_DIR}/outputs"

    @classmethod
    def validate(cls) -> bool:
        """설정 유효성 검사"""
        if not cls.OPENAI_API_KEY:
            print("OpenAI API 키가 설정되지 않았습니다.")
            print("환경변수 OPENAI_API_KEY를 설정하거나 실행 시 입력하세요.")
            return False
        return True
