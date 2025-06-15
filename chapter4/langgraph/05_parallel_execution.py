from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import time
import random
import asyncio


# ① 워크플로우 단계 정의
class WorkflowStep:
    TASK_COORDINATOR = "TASK_COORDINATOR"
    WEATHER_CHECKER = "WEATHER_CHECKER"
    NEWS_FETCHER = "NEWS_FETCHER"
    STOCK_ANALYZER = "STOCK_ANALYZER"
    DATA_AGGREGATOR = "DATA_AGGREGATOR"


# ② 그래프 상태 정의
class DashboardState(BaseModel):
    user_location: str = Field(default="서울", description="사용자 위치")
    requested_topics: list = Field(default_factory=list, description="요청된 뉴스 주제")
    stock_symbols: list = Field(default_factory=list, description="주식 심볼 목록")
    
    # 병렬 작업 결과들
    weather_data: Dict[str, Any] = Field(default_factory=dict, description="날씨 정보")
    news_data: Dict[str, Any] = Field(default_factory=dict, description="뉴스 정보")
    stock_data: Dict[str, Any] = Field(default_factory=dict, description="주식 정보")
    
    # 최종 대시보드
    dashboard_report: str = Field(default="", description="최종 대시보드 리포트")
    
    # 실행 메타데이터
    execution_start_time: float = Field(default=0.0, description="실행 시작 시간")
    parallel_execution_time: float = Field(default=0.0, description="병렬 실행 시간")


# ③ 작업 코디네이터 노드
def task_coordinator(state: DashboardState) -> Dict[str, Any]:
    print(f"[task_coordinator] 🎯 대시보드 생성 작업 시작")
    print(f"[task_coordinator] 📍 위치: {state.user_location}")
    print(f"[task_coordinator] 📰 뉴스 주제: {state.requested_topics}")
    print(f"[task_coordinator] 📈 주식: {state.stock_symbols}")
    
    start_time = time.time()
    
    print(f"[task_coordinator] ⚡ 병렬 작업들을 시작합니다...")
    
    return {
        "execution_start_time": start_time
    }


# ④ 날씨 확인 노드 (시뮬레이션)
def weather_checker(state: DashboardState) -> Dict[str, Any]:
    print(f"[weather_checker] 🌤️ {state.user_location} 날씨 정보 수집 중...")
    
    # 네트워크 지연 시뮬레이션
    delay = random.uniform(1.0, 2.5)
    time.sleep(delay)
    
    # 가상의 날씨 데이터 생성
    weather_conditions = ["맑음", "흐림", "비", "눈", "안개"]
    temperatures = list(range(-5, 35))
    
    weather_info = {
        "location": state.user_location,
        "condition": random.choice(weather_conditions),
        "temperature": random.choice(temperatures),
        "humidity": random.randint(30, 90),
        "wind_speed": random.randint(0, 20),
        "fetch_time": delay,
        "status": "success"
    }
    
    print(f"[weather_checker] ✅ 날씨 정보 수집 완료 ({delay:.1f}s)")
    print(f"                  {weather_info['condition']}, {weather_info['temperature']}°C")
    
    return {
        "weather_data": weather_info
    }


# ⑤ 뉴스 수집 노드 (시뮬레이션)
def news_fetcher(state: DashboardState) -> Dict[str, Any]:
    topics = state.requested_topics or ["일반"]
    print(f"[news_fetcher] 📰 뉴스 수집 중... 주제: {topics}")
    
    # 네트워크 지연 시뮬레이션
    delay = random.uniform(1.5, 3.0)
    time.sleep(delay)
    
    # 가상의 뉴스 데이터 생성
    news_titles = [
        "AI 기술의 새로운 돌파구 발견",
        "글로벌 경제 전망 개선 신호",
        "신재생 에너지 투자 급증",
        "우주 탐사 프로젝트 성공",
        "바이오테크 혁신 기술 공개"
    ]
    
    articles = []
    for topic in topics:
        for i in range(3):  # 주제당 3개 기사
            articles.append({
                "title": f"[{topic}] {random.choice(news_titles)}",
                "summary": f"{topic} 관련 중요한 뉴스입니다.",
                "timestamp": "2024-01-15 12:00:00"
            })
    
    news_info = {
        "topics": topics,
        "articles": articles,
        "total_count": len(articles),
        "fetch_time": delay,
        "status": "success"
    }
    
    print(f"[news_fetcher] ✅ 뉴스 수집 완료 ({delay:.1f}s)")
    print(f"                {news_info['total_count']}개 기사 수집")
    
    return {
        "news_data": news_info
    }


# ⑥ 주식 분석 노드 (시뮬레이션)
def stock_analyzer(state: DashboardState) -> Dict[str, Any]:
    symbols = state.stock_symbols or ["KOSPI", "NASDAQ"]
    print(f"[stock_analyzer] 📊 주식 정보 분석 중... 심볼: {symbols}")
    
    # 네트워크 지연 시뮬레이션
    delay = random.uniform(2.0, 3.5)
    time.sleep(delay)
    
    # 가상의 주식 데이터 생성
    stock_info = {
        "symbols": symbols,
        "market_data": {},
        "fetch_time": delay,
        "status": "success"
    }
    
    for symbol in symbols:
        base_price = random.uniform(50, 500)
        change_percent = random.uniform(-5, 5)
        
        stock_info["market_data"][symbol] = {
            "current_price": round(base_price, 2),
            "change_percent": round(change_percent, 2),
            "volume": random.randint(1000000, 10000000),
            "market_cap": f"{random.randint(10, 1000)}조원"
        }
    
    print(f"[stock_analyzer] ✅ 주식 분석 완료 ({delay:.1f}s)")
    for symbol, data in stock_info["market_data"].items():
        print(f"                  {symbol}: {data['current_price']} ({data['change_percent']:+.1f}%)")
    
    return {
        "stock_data": stock_info
    }


# ⑦ 데이터 집계 노드
def data_aggregator(state: DashboardState) -> Dict[str, Any]:
    print(f"[data_aggregator] 📋 대시보드 리포트 생성 중...")
    
    # 병렬 실행 시간 계산
    parallel_time = time.time() - state.execution_start_time
    
    # 대시보드 리포트 생성
    report_sections = []
    
    # 헤더
    report_sections.append("🏠 개인 대시보드 리포트")
    report_sections.append("=" * 50)
    
    # 날씨 섹션
    if state.weather_data and state.weather_data.get("status") == "success":
        weather = state.weather_data
        report_sections.append(f"\n🌤️ 날씨 정보 ({weather['location']})")
        report_sections.append(f"   상태: {weather['condition']}")
        report_sections.append(f"   온도: {weather['temperature']}°C")
        report_sections.append(f"   습도: {weather['humidity']}%")
        report_sections.append(f"   풍속: {weather['wind_speed']}m/s")
    
    # 뉴스 섹션
    if state.news_data and state.news_data.get("status") == "success":
        news = state.news_data
        report_sections.append(f"\n📰 뉴스 요약 ({news['total_count']}개 기사)")
        for article in news['articles'][:3]:  # 상위 3개만 표시
            report_sections.append(f"   • {article['title']}")
    
    # 주식 섹션
    if state.stock_data and state.stock_data.get("status") == "success":
        stock = state.stock_data
        report_sections.append(f"\n📊 주식 정보")
        for symbol, data in stock['market_data'].items():
            change_emoji = "📈" if data['change_percent'] > 0 else "📉" if data['change_percent'] < 0 else "➡️"
            report_sections.append(
                f"   {symbol}: {data['current_price']} "
                f"({data['change_percent']:+.1f}%) {change_emoji}"
            )
    
    # 실행 통계
    report_sections.append(f"\n⚡ 실행 통계")
    report_sections.append(f"   병렬 실행 시간: {parallel_time:.1f}초")
    
    # 개별 작업 시간들
    times = []
    if state.weather_data.get("fetch_time"):
        times.append(f"날씨: {state.weather_data['fetch_time']:.1f}s")
    if state.news_data.get("fetch_time"):
        times.append(f"뉴스: {state.news_data['fetch_time']:.1f}s")
    if state.stock_data.get("fetch_time"):
        times.append(f"주식: {state.stock_data['fetch_time']:.1f}s")
    
    if times:
        report_sections.append(f"   개별 작업 시간: {', '.join(times)}")
        sequential_time = sum([
            state.weather_data.get("fetch_time", 0),
            state.news_data.get("fetch_time", 0),
            state.stock_data.get("fetch_time", 0)
        ])
        speedup = sequential_time / parallel_time if parallel_time > 0 else 1
        report_sections.append(f"   순차 실행 대비 속도 향상: {speedup:.1f}x")
    
    dashboard_report = "\n".join(report_sections)
    
    print(f"[data_aggregator] ✅ 대시보드 생성 완료 ({parallel_time:.1f}s)")
    
    return {
        "dashboard_report": dashboard_report,
        "parallel_execution_time": parallel_time
    }


# ⑧ 그래프 생성 (병렬 실행 포함)
def create_dashboard_graph():
    workflow = StateGraph(DashboardState)
    
    # 노드 추가
    workflow.add_node(WorkflowStep.TASK_COORDINATOR, task_coordinator)
    workflow.add_node(WorkflowStep.WEATHER_CHECKER, weather_checker)
    workflow.add_node(WorkflowStep.NEWS_FETCHER, news_fetcher)
    workflow.add_node(WorkflowStep.STOCK_ANALYZER, stock_analyzer)
    workflow.add_node(WorkflowStep.DATA_AGGREGATOR, data_aggregator)
    
    # 시작점 설정
    workflow.add_edge(START, WorkflowStep.TASK_COORDINATOR)
    
    # 코디네이터 후 병렬 작업들 시작 (핵심 병렬 실행!)
    workflow.add_edge(WorkflowStep.TASK_COORDINATOR, WorkflowStep.WEATHER_CHECKER)
    workflow.add_edge(WorkflowStep.TASK_COORDINATOR, WorkflowStep.NEWS_FETCHER)
    workflow.add_edge(WorkflowStep.TASK_COORDINATOR, WorkflowStep.STOCK_ANALYZER)
    
    # 모든 병렬 작업이 완료되면 집계 노드로 (자동 동기화!)
    workflow.add_edge(WorkflowStep.WEATHER_CHECKER, WorkflowStep.DATA_AGGREGATOR)
    workflow.add_edge(WorkflowStep.NEWS_FETCHER, WorkflowStep.DATA_AGGREGATOR)
    workflow.add_edge(WorkflowStep.STOCK_ANALYZER, WorkflowStep.DATA_AGGREGATOR)
    
    # 집계 완료 후 종료
    workflow.add_edge(WorkflowStep.DATA_AGGREGATOR, END)
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


# ⑨ 테스트 함수
def test_dashboard_creation():
    print("=== 개인 대시보드 생성 테스트 ===\n")
    
    app = create_dashboard_graph()
    
    # 테스트 설정
    initial_state = DashboardState(
        user_location="부산",
        requested_topics=["기술", "경제"],
        stock_symbols=["삼성전자", "SK하이닉스", "NAVER"]
    )
    
    print("🚀 대시보드 생성 시작!")
    print("=" * 60)
    
    # 그래프 실행 (병렬 처리 자동)
    start_time = time.time()
    final_state = app.invoke(initial_state)
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("📊 최종 대시보드:")
    print(final_state['dashboard_report'])
    
    print(f"\n⏱️ 전체 실행 시간: {total_time:.1f}초")


# ⑩ 성능 비교 테스트
def test_performance_comparison():
    print("\n=== 성능 비교 테스트 ===\n")
    
    app = create_dashboard_graph()
    
    # 여러 번 실행하여 평균 성능 측정
    runs = 3
    total_parallel_time = 0
    
    for i in range(runs):
        print(f"--- 실행 {i+1}/{runs} ---")
        
        initial_state = DashboardState(
            user_location=f"도시{i+1}",
            requested_topics=["테스트"],
            stock_symbols=["TEST"]
        )
        
        final_state = app.invoke(initial_state)
        parallel_time = final_state['parallel_execution_time']
        total_parallel_time += parallel_time
        
        print(f"실행 시간: {parallel_time:.1f}초")
    
    avg_time = total_parallel_time / runs
    print(f"\n📊 평균 병렬 실행 시간: {avg_time:.1f}초")
    
    # 이론적 순차 실행 시간 (각 작업의 평균 시간 합)
    estimated_sequential = 1.75 + 2.25 + 2.75  # 각 작업의 중간값
    theoretical_speedup = estimated_sequential / avg_time
    
    print(f"📈 이론적 순차 실행 시간: {estimated_sequential:.1f}초")
    print(f"⚡ 예상 속도 향상: {theoretical_speedup:.1f}x")


def main():
    print("=== LangGraph 병렬 실행 예제 ===\n")
    
    # 대시보드 생성 테스트
    test_dashboard_creation()
    
    # 성능 비교 테스트
    test_performance_comparison()
    
    # 그래프 시각화
    print("\n=== 워크플로우 시각화 ===")
    app = create_dashboard_graph()
    
    # ASCII 그래프 출력
    ascii_graph = app.get_graph().draw_ascii()
    print("\n[ASCII 그래프]")
    print(ascii_graph)
    
    # Mermaid PNG 생성
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./05_parallel_execution.png", "wb") as f:
            f.write(mermaid_png)
        print("\n[그래프 이미지] 05_parallel_execution.png 파일이 생성되었습니다!")
    except Exception as e:
        print(f"\n[그래프 이미지] 생성 실패: {e}")


if __name__ == "__main__":
    main()
