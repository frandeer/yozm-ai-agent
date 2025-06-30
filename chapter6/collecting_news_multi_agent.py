import os
import json
import feedparser
import schedule
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, TypedDict, Annotated, Sequence, Literal
import operator
import functools
import requests
from bs4 import BeautifulSoup

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv


# Configuration
class Config:
    """시스템 설정"""
    # Google News RSS URLs
    RSS_URLS = {
        "general": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
        "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        "entertainment": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",
        "health": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtdHZLQUFQAQ?hl=ko&gl=KR&ceid=KR:ko"
    }
    
    # Email settings
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
    
    # File settings
    OUTPUT_DIR = "news_reports"
    SCHEDULE_TIME = "09:00"  # 매일 오전 9시 실행
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = "gpt-4o-mini"

    @classmethod
    def load_config(cls):
        cls.EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
        cls.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
        cls.RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Shared news data storage
news_data_store = {
    "collected_news": [],
    "classified_news": [],
    "summarized_news": [],
    "report_files": {}
}


# State definition for LangGraph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    
    
class RouteResponse(BaseModel):
    next: Literal["news_collector", "news_classifier", "news_summarizer", "report_generator", "email_sender", "FINISH"]
    
    
# Tools for agents
@tool
def collect_news_from_rss(category: str = "all") -> str:
    """RSS 피드에서 뉴스 수집"""
    all_news = []
    category_count = {}
    
    if category == "all":
        categories_to_collect = Config.RSS_URLS.keys()
    elif category in Config.RSS_URLS:
        categories_to_collect = [category]
    else:
        return f"Invalid category: {category}. Available categories: {', '.join(Config.RSS_URLS.keys())}"
    
    print(f"\n수집할 카테고리: {list(categories_to_collect)}")
    
    for cat in categories_to_collect:
        try:
            print(f"  - {cat} 카테고리 수집 중...")
            feed = feedparser.parse(Config.RSS_URLS[cat])
            count = 0
            for entry in feed.entries[:5]:  # 각 카테고리별로 5개씩만 수집 (API 호출 최적화)
                # Google News 리다이렉트 URL 처리
                original_link = entry.get('link', '')
                final_link = original_link
                
                # 최종 URL을 미리 얻어두면 나중에 중복 요청을 피할 수 있음
                if 'news.google.com/rss/articles/' in original_link:
                    try:
                        final_link = get_final_url(original_link, timeout=5)
                    except:
                        final_link = original_link  # 실패 시 원본 사용
                
                news_item = {
                    "title": entry.get('title', ''),
                    "link": final_link,  # 최종 URL 저장
                    "original_link": original_link,  # 원본 링크도 보관
                    "description": entry.get('description', ''),
                    "pub_date": entry.get('published', ''),
                    "source": entry.get('source', {}).get('title', 'Google News'),
                    "category": cat,
                    "summary": "",
                    "importance_score": 5
                }
                all_news.append(news_item)
                count += 1
            category_count[cat] = count
            print(f"    ✓ {count}개 수집 완료")
        except Exception as e:
            print(f"    ✗ 에러 발생: {e}")
            category_count[cat] = 0
    
    # Store in shared data
    news_data_store["collected_news"] = all_news
    
    # 상세한 결과 메시지
    result_msg = f"총 {len(all_news)}개 뉴스 수집 완료:\n"
    for cat, count in category_count.items():
        result_msg += f"  - {cat}: {count}개\n"
    
    return result_msg


# Pydantic models for LLM outputs
class NewsClassification(BaseModel):
    """뉴스 분류 결과"""
    category: str = Field(description="뉴스 카테고리 (politics, economy, society, technology, international, culture, sports, entertainment, health, other)")
    importance_score: int = Field(description="중요도 점수 (1-10)", ge=1, le=10)
    key_topics: List[str] = Field(description="주요 토픽 키워드 (최대 3개)")
    reasoning: str = Field(description="분류 이유")


class NewsSummary(BaseModel):
    """뉴스 요약 결과"""
    title: str = Field(description="개선된 제목 (더 명확하고 정보가 풍부하게)")
    summary: str = Field(description="3-4문장으로 핵심 내용 요약")
    key_points: List[str] = Field(description="주요 포인트 3-5개")
    impact: str = Field(description="이 뉴스의 영향이나 중요성")


# Helper function to fetch article content
def get_final_url(url: str, timeout: int = 10) -> str:
    """Google News 리다이렉트 URL에서 최종 URL 얻기"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Google News URL인 경우 특별 처리
        if 'news.google.com/rss/articles/' in url:
            # HEAD 요청으로 리다이렉트 추적
            response = requests.head(url, headers=headers, allow_redirects=True, timeout=timeout)
            final_url = response.url
            
            # 때로는 GET 요청이 필요한 경우가 있음
            if final_url == url or 'google.com' in final_url:
                response = requests.get(url, headers=headers, allow_redirects=True, timeout=timeout)
                final_url = response.url
            
            print(f"    리다이렉트: {url[:50]}... → {final_url[:50]}...")
            return final_url
        
        return url
        
    except Exception as e:
        print(f"    리다이렉트 해결 실패: {e}")
        return url


def fetch_article_content(url: str, timeout: int = 10) -> str:
    """기사 URL에서 본문 내용 추출"""
    try:
        # 이미 최종 URL인 경우 다시 리다이렉트 처리하지 않음
        if 'news.google.com/rss/articles/' in url:
            final_url = get_final_url(url, timeout)
        else:
            final_url = url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(final_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe"]):
            script.decompose()
        
        # 한국 뉴스 사이트별 셀렉터 추가
        article_selectors = [
            # 일반적인 셀렉터
            'article', 
            '[role="main"]',
            '.article-body',
            '.content',
            '.story-body',
            '.entry-content',
            '#article-body',
            '.post-content',
            # 한국 뉴스 사이트
            '.article_body',  # 네이버 뉴스
            '#articeBody',    # 다음 뉴스
            '#newsEndContents',  # 네이버 뉴스 스탠드
            '.news_end',      # 네이버
            '.article_view',  # 각종 언론사
            '.view_content',  
            '#content',
            '.news_view',
            'div[itemprop="articleBody"]',
            '.article-content'
        ]
        
        article_text = ""
        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                # 광고나 관련 기사 제거
                for ad in article.select('.ad, .advertisement, .related-articles, .photo_table'):
                    ad.decompose()
                
                article_text = article.get_text(separator='\n', strip=True)
                if len(article_text) > 100:  # 의미있는 내용이 있는지 확인
                    break
        
        # If no article container found, try to get all paragraphs
        if not article_text or len(article_text) < 100:
            paragraphs = soup.find_all('p')
            article_text = '\n'.join([
                p.get_text(strip=True) 
                for p in paragraphs 
                if len(p.get_text(strip=True)) > 30 and 
                not any(skip in p.get_text() for skip in ['광고', '©', 'Copyright', '무단전재'])
            ])
        
        # 텍스트 정리
        if article_text:
            # 연속된 공백과 줄바꿈 정리
            article_text = '\n'.join(line.strip() for line in article_text.split('\n') if line.strip())
            
            # 길이 제한
            if len(article_text) > 3000:
                article_text = article_text[:3000] + "..."
        
        if not article_text or len(article_text) < 50:
            return f"기사 내용을 가져올 수 없습니다. (URL: {final_url[:50]}...)"
            
        return article_text
        
    except requests.exceptions.Timeout:
        return "기사 내용 가져오기 시간 초과"
    except requests.exceptions.RequestException as e:
        print(f"    요청 에러: {e}")
        return "기사 내용을 가져올 수 없습니다. (네트워크 오류)"
    except Exception as e:
        print(f"    에러: {e}")
        return "기사 내용을 가져올 수 없습니다."


@tool
def classify_news_items() -> str:
    """뉴스 아이템 분류 및 중요도 점수 부여 (LLM 사용)"""
    try:
        news_items = news_data_store["collected_news"]
        
        if not news_items:
            return "No news items to classify. Please collect news first."
        
        # LLM 초기화
        llm = ChatOpenAI(model=Config.MODEL_NAME, temperature=0.3)
        
        # 분류 프롬프트
        classification_prompt = ChatPromptTemplate.from_template("""
당신은 뉴스 분류 전문가입니다. 다음 뉴스를 분석하여 분류해주세요.

뉴스 정보:
제목: {title}
설명: {description}
카테고리 힌트: {category_hint}

다음 기준으로 평가해주세요:
1. 카테고리: politics(정치), economy(경제), society(사회), technology(기술), international(국제), 
   culture(문화), sports(스포츠), entertainment(엔터테인먼트), health(건강), other(기타) 중 선택
2. 중요도 점수 (1-10):
   - 9-10: 속보, 국가적 중대사, 대규모 영향
   - 7-8: 중요한 정책 변경, 주요 기업 뉴스, 사회적 이슈
   - 5-6: 일반적인 뉴스, 업데이트, 발표
   - 3-4: 일상적인 뉴스, 지역 소식
   - 1-2: 가십, 단순 정보

반드시 JSON 형식으로 응답하세요.
""")
        
        classified = []
        batch_size = 5  # 배치 처리로 API 호출 최적화
        
        print(f"\nLLM을 사용하여 {len(news_items)}개 뉴스 분류 중...")
        
        for i in range(0, len(news_items), batch_size):
            batch = news_items[i:i+batch_size]
            
            for item in batch:
                try:
                    # LLM으로 분류
                    chain = classification_prompt | llm.with_structured_output(NewsClassification)
                    result = chain.invoke({
                        "title": item['title'],
                        "description": item.get('description', ''),
                        "category_hint": item.get('category', 'general')
                    })
                    
                    # 결과 적용
                    item['ai_category'] = result.category
                    item['importance_score'] = result.importance_score
                    item['key_topics'] = result.key_topics
                    item['classification_reasoning'] = result.reasoning
                    
                    classified.append(item)
                    
                except Exception as e:
                    print(f"  분류 실패 (기본값 사용): {item['title'][:50]}... - {e}")
                    # 실패 시 기본값 사용
                    item['importance_score'] = 5
                    classified.append(item)
            
            print(f"  진행률: {min(i+batch_size, len(news_items))}/{len(news_items)}")
        
        # Store in shared data
        news_data_store["classified_news"] = classified
        
        high_importance_count = len([item for item in classified if item['importance_score'] >= 7])
        return f"LLM으로 {len(classified)}개 뉴스 분류 완료. {high_importance_count}개 고중요도 뉴스 발견 (7점 이상)."
        
    except Exception as e:
        return f"Error classifying news: {e}"


@tool  
def summarize_important_news() -> str:
    """중요한 뉴스 요약 (LLM 사용 및 기사 본문 가져오기)"""
    try:
        classified_news = news_data_store["classified_news"]
        
        if not classified_news:
            return "No classified news to summarize. Please classify news first."
        
        # Filter important news (score >= 7)
        important_news = [item for item in classified_news if item.get('importance_score', 0) >= 7]
        
        if not important_news:
            # 중요 뉴스가 없으면 상위 5개라도 요약
            important_news = sorted(classified_news, key=lambda x: x.get('importance_score', 0), reverse=True)[:5]
            print(f"\n중요도 7 이상 뉴스가 없어 상위 {len(important_news)}개 뉴스를 요약합니다.")
        
        # LLM 초기화
        llm = ChatOpenAI(model=Config.MODEL_NAME, temperature=0.3)
        
        # 요약 프롬프트
        summary_prompt = ChatPromptTemplate.from_template("""
당신은 뉴스 요약 전문가입니다. 다음 뉴스를 분석하여 핵심 내용을 요약해주세요.

뉴스 정보:
제목: {title}
설명: {description}
본문 내용: {article_content}
중요도: {importance_score}/10
분류 이유: {classification_reasoning}

다음 형식으로 요약해주세요:
1. 개선된 제목: 더 명확하고 정보가 풍부한 제목
2. 요약: 3-4문장으로 핵심 내용 요약
3. 주요 포인트: 3-5개의 핵심 사항
4. 영향/중요성: 이 뉴스가 왜 중요한지

반드시 한국어로 작성하고 JSON 형식으로 응답하세요.
""")
        
        summarized = []
        fetch_content = True  # 기사 본문 가져오기 여부
        
        print(f"\nLLM을 사용하여 {len(important_news)}개 중요 뉴스 요약 중...")
        
        for idx, item in enumerate(important_news):
            try:
                article_content = "본문 없음"
                
                # 기사 본문 가져오기 (선택적)
                if fetch_content and item.get('link'):
                    print(f"  [{idx+1}/{len(important_news)}] 기사 본문 가져오는 중: {item['title'][:50]}...")
                    # 이미 최종 URL이 있거나 original_link가 있는 경우 사용
                    article_url = item.get('link', item.get('original_link', ''))
                    article_content = fetch_article_content(article_url)
                    if len(article_content) > 50:  # 성공적으로 가져온 경우
                        print(f"    ✓ 본문 {len(article_content)}자 가져옴")
                    else:
                        print(f"    ✗ 본문 가져오기 실패")
                
                # LLM으로 요약
                chain = summary_prompt | llm.with_structured_output(NewsSummary)
                result = chain.invoke({
                    "title": item['title'],
                    "description": item.get('description', ''),
                    "article_content": article_content[:2000],  # 토큰 제한을 위해 2000자로 제한
                    "importance_score": item.get('importance_score', 5),
                    "classification_reasoning": item.get('classification_reasoning', '')
                })
                
                # 결과 적용
                item['improved_title'] = result.title
                item['summary'] = result.summary
                item['key_points'] = result.key_points
                item['impact'] = result.impact
                item['has_full_content'] = len(article_content) > 100
                
                summarized.append(item)
                print(f"    ✓ 요약 완료")
                
            except Exception as e:
                print(f"  요약 실패 (기본 요약 사용): {item['title'][:50]}... - {e}")
                # 실패 시 기본 요약
                item['summary'] = f"[중요도 {item.get('importance_score', 5)}] {item['title']}"
                item['key_points'] = ["요약 생성 실패"]
                summarized.append(item)
        
        # Store in shared data
        news_data_store["summarized_news"] = summarized
        
        # 전체 뉴스에도 요약 정보 업데이트
        for item in news_data_store["classified_news"]:
            for summ_item in summarized:
                if item['link'] == summ_item['link']:
                    item.update(summ_item)
                    break
        
        return f"LLM으로 {len(summarized)}개 뉴스 요약 완료. 기사 본문 수집: {len([x for x in summarized if x.get('has_full_content')])}개"
        
    except Exception as e:
        return f"Error summarizing news: {e}"


@tool
def generate_news_report() -> str:
    """뉴스 리포트 생성"""
    try:
        all_news = news_data_store["classified_news"]
        summarized_news = news_data_store["summarized_news"]
        
        if not all_news:
            return "No news data available for report generation."
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        if not os.path.exists(Config.OUTPUT_DIR):
            os.makedirs(Config.OUTPUT_DIR)
        
        # Organize news by category
        news_by_category = {}
        for item in all_news:
            cat = item.get('category', 'other')
            if cat not in news_by_category:
                news_by_category[cat] = []
            news_by_category[cat].append(item)
        
        # Create report structure
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "total_news": len(all_news),
            "important_news_count": len(summarized_news),
            "news_by_category": {cat: len(items) for cat, items in news_by_category.items()},
            "all_news": all_news,
            "top_news": summarized_news
        }
        
        # Save JSON report
        json_filename = f"{Config.OUTPUT_DIR}/news_report_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Generate HTML report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>뉴스 리포트 - {report['date']}</title>
            <style>
                body {{ 
                    font-family: 'Malgun Gothic', sans-serif; 
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{ 
                    color: #333;
                    border-bottom: 3px solid #0066cc;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #0066cc;
                    margin-top: 30px;
                    border-bottom: 2px solid #e9ecef;
                    padding-bottom: 10px;
                }}
                h3 {{
                    color: #333;
                    margin-top: 20px;
                }}
                .stats {{
                    display: flex;
                    gap: 20px;
                    margin: 20px 0;
                }}
                .stat-box {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    flex: 1;
                    text-align: center;
                }}
                .news-item {{
                    margin: 15px 0;
                    padding: 15px;
                    border-left: 3px solid #0066cc;
                    background: #f8f9fa;
                }}
                .important-news {{
                    border-left-color: #ff6b6b;
                    background: #fff5f5;
                }}
                .category-stats {{
                    margin: 20px 0;
                }}
                .category-stat {{
                    display: inline-block;
                    margin: 5px;
                    padding: 5px 10px;
                    background: #e9ecef;
                    border-radius: 3px;
                }}
                .importance-badge {{
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 0.85em;
                    font-weight: bold;
                }}
                .importance-high {{ background: #ffebee; color: #c62828; }}
                .importance-medium {{ background: #fff3e0; color: #ef6c00; }}
                .importance-low {{ background: #e8f5e9; color: #2e7d32; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📰 일일 뉴스 리포트</h1>
                <p><strong>날짜:</strong> {report['date']} {report['time']}</p>
                
                <div class="stats">
                    <div class="stat-box">
                        <h3>전체 뉴스</h3>
                        <p style="font-size: 2em; color: #0066cc;">{report['total_news']}건</p>
                    </div>
                    <div class="stat-box">
                        <h3>중요 뉴스</h3>
                        <p style="font-size: 2em; color: #ff6b6b;">{report['important_news_count']}건</p>
                    </div>
                </div>
                
                <div class="category-stats">
                    <h2>카테고리별 뉴스 통계</h2>
                    {''.join([f'<span class="category-stat">{cat}: {count}건</span>' for cat, count in report['news_by_category'].items()])}
                </div>
        """
        
        # 중요 뉴스 섹션
        if summarized_news:
            html_content += """
                <h2>🔥 중요 뉴스 (중요도 7 이상)</h2>
            """
            for item in summarized_news:
                importance_class = "importance-high" if item['importance_score'] >= 8 else "importance-medium"
                improved_title = item.get('improved_title', item['title'])
                
                html_content += f'''
                    <div class="news-item important-news">
                        <h4>{improved_title}</h4>
                        <p>
                            <strong>카테고리:</strong> {item.get("ai_category", item.get("category", "기타"))} | 
                            <span class="importance-badge {importance_class}">중요도: {item.get("importance_score", "N/A")}/10</span>
                            {' | <span style="color: green;">✓ 본문 분석 완료</span>' if item.get('has_full_content') else ''}
                        </p>
                        <p><strong>요약:</strong> {item.get("summary", item.get("description", ""))}</p>
                        
                        {f'<p><strong>주요 포인트:</strong><ul>{"".join([f"<li>{point}</li>" for point in item.get("key_points", [])])}</ul></p>' if item.get('key_points') else ''}
                        
                        {f'<p><strong>영향/중요성:</strong> {item.get("impact", "")}</p>' if item.get('impact') else ''}
                        
                        <p><strong>원본 제목:</strong> {item["title"]}</p>
                        <p><a href="{item.get("link", "#")}" target="_blank">자세히 보기 →</a></p>
                    </div>
                '''
        
        # 카테고리별 전체 뉴스
        html_content += """
            <h2>📋 카테고리별 전체 뉴스</h2>
        """
        
        for category, items in sorted(news_by_category.items()):
            html_content += f"""
                <h3>{category.upper()} ({len(items)}건)</h3>
            """
            for item in sorted(items, key=lambda x: x.get('importance_score', 0), reverse=True):
                importance = item.get('importance_score', 0)
                if importance >= 8:
                    importance_class = "importance-high"
                elif importance >= 6:
                    importance_class = "importance-medium"
                else:
                    importance_class = "importance-low"
                    
                html_content += f'''
                    <div class="news-item">
                        <h4>{item.get('improved_title', item['title'])}</h4>
                        <p>
                            <span class="importance-badge {importance_class}">중요도: {importance}/10</span> | 
                            <strong>AI 카테고리:</strong> {item.get('ai_category', item.get('category', '기타'))} |
                            <strong>발행일:</strong> {item.get("pub_date", "N/A")}
                        </p>
                        <p>{item.get('summary', item.get('description', ''))[:200]}...</p>
                        {f'<p><strong>주요 토픽:</strong> {", ".join(item.get("key_topics", []))}</p>' if item.get('key_topics') else ''}
                        <p><a href="{item.get("link", "#")}" target="_blank">자세히 보기 →</a></p>
                    </div>
                '''
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        html_filename = f"{Config.OUTPUT_DIR}/news_report_{timestamp}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Store file paths and HTML content
        news_data_store["report_files"] = {
            "json": json_filename,
            "html": html_filename
        }
        news_data_store["html_content"] = html_content
        
        return f"Report generated successfully! JSON: {json_filename}, HTML: {html_filename}"
        
    except Exception as e:
        return f"Error generating report: {e}"


@tool
def send_email_report() -> str:
    """이메일로 리포트 발송"""
    print("\n이메일 발송 시작...")
    
    # 이메일 설정 확인
    if not Config.EMAIL_ADDRESS:
        return "이메일 발송 실패: EMAIL_ADDRESS가 설정되지 않았습니다."
    if not Config.EMAIL_PASSWORD:
        return "이메일 발송 실패: EMAIL_PASSWORD가 설정되지 않았습니다."
    if not Config.RECIPIENT_EMAIL:
        return "이메일 발송 실패: RECIPIENT_EMAIL이 설정되지 않았습니다."
    
    print(f"발신자: {Config.EMAIL_ADDRESS}")
    print(f"수신자: {Config.RECIPIENT_EMAIL}")

    try:
        # HTML 컨텐츠 가져오기
        html_content = news_data_store.get("html_content", "")
        if not html_content:
            return "이메일 발송 실패: 발송할 리포트 내용이 없습니다."
        
        # 통계 정보
        total_news = len(news_data_store.get('classified_news', []))
        important_news = len(news_data_store.get('summarized_news', []))
        
        # 이메일 생성
        msg = MIMEMultipart('alternative')
        msg['From'] = Config.EMAIL_ADDRESS
        msg['To'] = Config.RECIPIENT_EMAIL
        msg['Subject'] = f"📰 일일 뉴스 리포트 - {datetime.now().strftime('%Y-%m-%d')} (총 {total_news}건)"
        
        # 텍스트 버전 (HTML을 지원하지 않는 이메일 클라이언트용)
        text_body = f"""
일일 뉴스 리포트 - {datetime.now().strftime('%Y년 %m월 %d일')}

■ 오늘의 뉴스 요약
- 총 수집된 뉴스: {total_news}건
- 중요 뉴스: {important_news}건

■ 카테고리별 뉴스
"""
        
        # 카테고리별 통계 추가
        category_stats = {}
        for item in news_data_store.get('classified_news', []):
            cat = item.get('category', 'other')
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        for cat, count in category_stats.items():
            text_body += f"  - {cat}: {count}건\n"
        
        # 중요 뉴스 목록 추가
        if news_data_store.get('summarized_news'):
            text_body += "\n■ 주요 뉴스\n"
            for idx, item in enumerate(news_data_store['summarized_news'][:10], 1):
                improved_title = item.get('improved_title', item['title'])
                text_body += f"\n{idx}. {improved_title}\n"
                text_body += f"   중요도: {item.get('importance_score', 'N/A')}/10 | 카테고리: {item.get('ai_category', item.get('category', '기타'))}\n"
                text_body += f"   {item.get('summary', '')}\n"
                if item.get('impact'):
                    text_body += f"   ▶ {item.get('impact')}\n"
        
        text_body += """
        
자세한 내용은 HTML 버전에서 확인하실 수 있습니다.

뉴스 멀티에이전트 시스템
        """
        
        # 이메일용 HTML 스타일 조정 (인라인 스타일로 변경)
        email_html_content = html_content
        # 일부 이메일 클라이언트는 <style> 태그를 무시하므로 중요한 스타일을 인라인으로 추가
        email_html_content = email_html_content.replace(
            '<div class="container">',
            '<div class="container" style="max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px;">'
        )
        email_html_content = email_html_content.replace(
            '<div class="news-item">',
            '<div class="news-item" style="margin: 15px 0; padding: 15px; border-left: 3px solid #0066cc; background: #f8f9fa;">'
        )
        email_html_content = email_html_content.replace(
            '<div class="news-item important-news">',
            '<div class="news-item important-news" style="margin: 15px 0; padding: 15px; border-left: 3px solid #ff6b6b; background: #fff5f5;">'
        )
        
        # MIMEText 객체 생성
        text_part = MIMEText(text_body, 'plain', 'utf-8')
        html_part = MIMEText(email_html_content, 'html', 'utf-8')
        
        # 메시지에 추가
        msg.attach(text_part)
        msg.attach(html_part)
        
        # 이메일 발송
        print("SMTP 서버 연결 중...")
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.set_debuglevel(0)  # 디버그 레벨 낮춤
            print("TLS 시작...")
            server.starttls()
            print("로그인 중...")
            server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
            print("이메일 발송 중...")
            server.send_message(msg)
        
        success_msg = f"이메일이 성공적으로 발송되었습니다! (수신자: {Config.RECIPIENT_EMAIL})"
        print(f"✓ {success_msg}")
        return success_msg
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"이메일 인증 실패: Gmail의 경우 앱 비밀번호를 사용해야 합니다. 에러: {e}"
        print(f"✗ {error_msg}")
        print("\n앱 비밀번호 설정 방법:")
        print("1. Google 계정 설정 > 보안으로 이동")
        print("2. 2단계 인증 활성화")
        print("3. 앱 비밀번호 생성")
        print("4. 생성된 16자리 비밀번호를 EMAIL_PASSWORD로 사용")
        return error_msg
    except smtplib.SMTPException as e:
        error_msg = f"SMTP 에러: {e}"
        print(f"✗ {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"이메일 발송 실패: {e}"
        print(f"✗ {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg


# Create agent functions
def create_agent(llm, tools, system_message: str):
    """Helper function to create an agent"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="messages"),
    ])
    prompt = prompt.partial(tools=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)


def agent_node(state, agent, name):
    """Agent node function"""
    result = agent.invoke(state)
    # Convert result to HumanMessage as supervisor expects
    if hasattr(result, 'tool_calls') and result.tool_calls:
        return {"messages": [result]}
    else:
        # If no tool calls, create a message
        return {"messages": [HumanMessage(content=result.content if hasattr(result, 'content') else str(result), name=name)]}


# Supervisor function
members = ["news_collector", "news_classifier", "news_summarizer", "report_generator", "email_sender"]
options = ["FINISH"] + members

def supervisor_agent(state):
    """Supervisor agent that routes to next agent"""
    supervisor_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a supervisor tasked with managing a conversation between the following workers: {members}. 
Given the following user request, respond with the worker to act next. Each worker will perform a task and respond with their results and status.

The workers should be called in this order:
1. news_collector - to collect news from RSS feeds
2. news_classifier - to classify and score the collected news
3. news_summarizer - to summarize important news items
4. report_generator - to create news reports
5. email_sender - to send the report via email

When all tasks are complete, respond with FINISH."""),
        MessagesPlaceholder(variable_name="messages"),
    ]).partial(members=", ".join(members))
    
    model = ChatOpenAI(model=Config.MODEL_NAME, temperature=0)
    
    supervisor_chain = supervisor_prompt | model.with_structured_output(RouteResponse)
    
    return {"next": supervisor_chain.invoke(state).next}


class NewsMultiAgentSystem:
    """뉴스 멀티에이전트 시스템"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            temperature=0,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Build the graph
        workflow = StateGraph(AgentState)
        
        # Create nodes
        collector_agent = create_agent(
            self.llm,
            [collect_news_from_rss],
            "You are a news collection specialist. Use the collect_news_from_rss tool to collect news. Always call the tool with category='all'."
        )
        collector_node = functools.partial(agent_node, agent=collector_agent, name="news_collector")
        
        classifier_agent = create_agent(
            self.llm,
            [classify_news_items],
            "You are a news classification specialist. Use the classify_news_items tool to classify collected news. This tool uses LLM to analyze and categorize news with importance scores."
        )
        classifier_node = functools.partial(agent_node, agent=classifier_agent, name="news_classifier")
        
        summarizer_agent = create_agent(
            self.llm,
            [summarize_important_news],
            "You are a news summarization specialist. Use the summarize_important_news tool to summarize classified news. This tool uses LLM and fetches full article content for better summaries."
        )
        summarizer_node = functools.partial(agent_node, agent=summarizer_agent, name="news_summarizer")
        
        generator_agent = create_agent(
            self.llm,
            [generate_news_report],
            "You are a report generation specialist. Use the generate_news_report tool to create reports."
        )
        generator_node = functools.partial(agent_node, agent=generator_agent, name="report_generator")
        
        sender_agent = create_agent(
            self.llm,
            [send_email_report],
            "You are an email sending specialist. Use the send_email_report tool to send reports."
        )
        sender_node = functools.partial(agent_node, agent=sender_agent, name="email_sender")
        
        # Add nodes
        workflow.add_node("supervisor", supervisor_agent)
        workflow.add_node("news_collector", collector_node)
        workflow.add_node("news_classifier", classifier_node)
        workflow.add_node("news_summarizer", summarizer_node)
        workflow.add_node("report_generator", generator_node)
        workflow.add_node("email_sender", sender_node)
        
        # Tool nodes
        workflow.add_node("collector_tools", ToolNode([collect_news_from_rss]))
        workflow.add_node("classifier_tools", ToolNode([classify_news_items]))
        workflow.add_node("summarizer_tools", ToolNode([summarize_important_news]))
        workflow.add_node("generator_tools", ToolNode([generate_news_report]))
        workflow.add_node("sender_tools", ToolNode([send_email_report]))
        
        # Add conditional edges for each agent
        for member, tool_node in [
            ("news_collector", "collector_tools"),
            ("news_classifier", "classifier_tools"),
            ("news_summarizer", "summarizer_tools"),
            ("report_generator", "generator_tools"),
            ("email_sender", "sender_tools")
        ]:
            workflow.add_conditional_edges(
                member,
                lambda x: "continue" if x["messages"][-1].tool_calls else "end",
                {
                    "continue": tool_node,
                    "end": "supervisor"
                }
            )
        
        # Add edges from tools back to supervisor
        for tool_node in ["collector_tools", "classifier_tools", "summarizer_tools", "generator_tools", "sender_tools"]:
            workflow.add_edge(tool_node, "supervisor")
        
        # Conditional routing from supervisor
        conditional_map = {k: k for k in members}
        conditional_map["FINISH"] = END
        workflow.add_conditional_edges("supervisor", lambda x: x["next"], conditional_map)
        
        # Set entry point
        workflow.add_edge("__start__", "supervisor")
        
        # Compile
        checkpointer = MemorySaver()
        self.app = workflow.compile(checkpointer=checkpointer)
    
    def run_pipeline(self):
        """파이프라인 실행"""
        print(f"\n{'='*60}")
        print(f"뉴스 처리 시작: {datetime.now()}")
        print(f"{'='*60}")
        
        # Clear previous data
        news_data_store.clear()
        news_data_store.update({
            "collected_news": [],
            "classified_news": [],
            "summarized_news": [],
            "report_files": {}
        })
        
        # Configuration
        config = {
            "configurable": {"thread_id": f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}"},
            "recursion_limit": 100  # Increase recursion limit further
        }
        
        # Initial message
        initial_message = HumanMessage(
            content="Please process today's news: collect all news, classify them, summarize important ones, generate a report, and send it via email."
        )
        
        try:
            # Run the workflow with streaming
            for output in self.app.stream(
                {"messages": [initial_message]},
                config=config,
                stream_mode="values"
            ):
                if "messages" in output:
                    last_message = output["messages"][-1]
                    if hasattr(last_message, 'content') and last_message.content:
                        # Tool 메시지인 경우 전체 내용 출력
                        if isinstance(last_message, ToolMessage):
                            print(f"\n[Tool Result]: {last_message.content}")
                        else:
                            print(f"\n[Agent]: {last_message.content[:200]}...")
            
            # Print summary
            print(f"\n{'='*60}")
            print("처리 완료 요약")
            print(f"{'='*60}")
            print(f"✓ 수집된 뉴스: {len(news_data_store['collected_news'])}건")
            print(f"✓ 분류된 뉴스: {len(news_data_store['classified_news'])}건")
            print(f"✓ 요약된 중요 뉴스: {len(news_data_store['summarized_news'])}건")
            
            # 카테고리별 통계
            if news_data_store['classified_news']:
                print("\n카테고리별 뉴스 수:")
                category_stats = {}
                for item in news_data_store['classified_news']:
                    cat = item.get('category', 'other')
                    category_stats[cat] = category_stats.get(cat, 0) + 1
                for cat, count in sorted(category_stats.items()):
                    print(f"  - {cat}: {count}건")
            
            if news_data_store['report_files']:
                print(f"\n생성된 리포트:")
                for file_type, file_path in news_data_store['report_files'].items():
                    print(f"  - {file_type.upper()}: {file_path}")
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"    (파일 크기: {file_size:,} bytes)")
            
            print(f"\n뉴스 처리 완료: {datetime.now()}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"Error during pipeline execution: {e}")
            print(f"{'='*60}")
            import traceback
            traceback.print_exc()
    
    def schedule_daily_run(self):
        """매일 정해진 시간에 실행"""
        schedule.every().day.at(Config.SCHEDULE_TIME).do(self.run_pipeline)
        
        print(f"스케줄러 시작: 매일 {Config.SCHEDULE_TIME}에 실행됩니다.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    """메인 함수
    
    필요한 패키지 설치:
    pip install langchain langgraph langchain-openai feedparser schedule python-dotenv requests beautifulsoup4
    """
    
    system = NewsMultiAgentSystem()
    
    # 옵션 1: 즉시 실행
    system.run_pipeline()
    
    # 옵션 2: 스케줄러로 매일 실행
    # system.schedule_daily_run()


if __name__ == "__main__":
    load_dotenv()
    Config.load_config()
    
    # API 키 확인
    if not Config.OPENAI_API_KEY:
        print("OPENAI_API_KEY 환경변수를 설정해주세요.")
        print("export OPENAI_API_KEY='your-api-key'")
        exit(1)
    
    # 이메일 설정 확인
    if not all([Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD, Config.RECIPIENT_EMAIL]):
        print("\n" + "="*60)
        print("⚠️  이메일 설정 안내")
        print("="*60)
        print("이메일 관련 환경변수가 설정되지 않았습니다.")
        print("이메일을 받으려면 다음 환경변수를 .env 파일에 추가하세요:")
        print()
        print("EMAIL_ADDRESS=your_email@gmail.com")
        print("EMAIL_PASSWORD=your_app_password  # Gmail 앱 비밀번호")
        print("RECIPIENT_EMAIL=recipient@gmail.com")
        print()
        print("📌 Gmail 앱 비밀번호 설정 방법:")
        print("1. Google 계정 설정 (https://myaccount.google.com)")
        print("2. 보안 → 2단계 인증 활성화")
        print("3. 보안 → 앱 비밀번호 생성")
        print("4. 앱 선택: 메일, 기기 선택: 기타(사용자 지정)")
        print("5. 생성된 16자리 비밀번호를 EMAIL_PASSWORD로 사용")
        print("="*60 + "\n")
    else:
        print("\n✓ 이메일 설정 확인됨")
        print(f"  발신자: {Config.EMAIL_ADDRESS}")
        print(f"  수신자: {Config.RECIPIENT_EMAIL}")

    main()