import re


def clean_html(html_text: str) -> str:
    """HTML 태그 제거"""
    if not html_text:
        return ""

    # ① 정규표현식으로 HTML 태그 제거: <태그명>내용</태그명> 패턴 매칭
    clean_text = re.sub("<.*?>", "", html_text)
    # ② 연속된 공백(스페이스, 탭, 줄바꿈)을 하나의 공백으로 정리
    clean_text = re.sub("\s+", " ", clean_text).strip()
    return clean_text


def truncate_text(text: str, max_length: int = 500) -> str:
    """텍스트를 적절한 길이로 자르기"""
    if not text or len(text) <= max_length:
        return text
    # ③ 지정된 길이로 자르고 말줄임표(...) 추가
    return text[:max_length] + "..."


def format_date(date_string: str) -> str:
    """날짜 포맷 정리"""
    if not date_string:
        return "날짜 정보 없음"

    try:
        # ④ RSS 피드의 GMT 시간대 표기 제거
        if "GMT" in date_string:
            date_string = date_string.split("GMT")[0].strip()
        return date_string
    except Exception:
        return date_string
