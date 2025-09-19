import os


class Config:
    """Settings for the hands-on AI workflow."""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "300"))
    BATCH_SIZE: int = int(os.getenv("AI_BATCH_SIZE", "5"))
    SUMMARY_MAX_CHARS: int = int(os.getenv("SUMMARY_MAX_CHARS", "600"))

    CATEGORIES: list[str] = [
        "경제",
        "사회",
        "IT/과학",
        "문화/연예",
        "스포츠",
        "생활/건강",
        "국제",
        "기타",
    ]

    @classmethod
    def validate(cls) -> None:
        if not cls.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. hands-on 실습을 위해 API 키를 환경 변수로 지정해주세요."
            )

