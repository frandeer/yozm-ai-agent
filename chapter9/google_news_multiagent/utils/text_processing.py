# utils/text_processing.py
import re
from typing import List


def clean_html(html_text: str) -> str:
    """HTML 태그 제거"""
    if not html_text:
        return ""
    
    # HTML 태그 제거
    clean_text = re.sub('<.*?>', '', html_text)
    # 여러 공백을 하나로 정리
    clean_text = re.sub('\s+', ' ', clean_text).strip()
    return clean_text


def truncate_text(text: str, max_length: int = 500) -> str:
    """텍스트를 적절한 길이로 자르기"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_date(date_string: str) -> str:
    """날짜 포맷 정리"""
    if not date_string:
        return "날짜 정보 없음"
    
    try:
        # GMT 제거
        if 'GMT' in date_string:
            date_string = date_string.split('GMT')[0].strip()
        return date_string
    except Exception:
        return date_string


def extract_keywords(text: str) -> List[str]:
    """텍스트에서 주요 키워드 추출 (간단한 버전)"""
    # 한국어 키워드 패턴
    keywords = []
    
    # 정치 관련 키워드
    political_keywords = ["대통령", "국회", "정치", "선거", "정당", "의원", "장관"]
    # 경제 관련 키워드
    economic_keywords = ["경제", "금융", "주식", "부동산", "기업", "코스피", "환율", "금리"]
    # IT 관련 키워드
    tech_keywords = ["ai", "it", "기술", "과학", "연구", "개발", "스타트업", "인공지능"]
    # 문화 관련 키워드
    culture_keywords = ["연예", "문화", "예술", "영화", "드라마", "음악", "공연"]
    # 스포츠 관련 키워드
    sports_keywords = ["스포츠", "축구", "야구", "농구", "올림픽", "월드컵"]
    
    all_keywords = political_keywords + economic_keywords + tech_keywords + culture_keywords + sports_keywords
    
    text_lower = text.lower()
    for keyword in all_keywords:
        if keyword in text_lower:
            keywords.append(keyword)
    
    return keywords