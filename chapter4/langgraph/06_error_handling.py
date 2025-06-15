from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import random
import time


# ① 워크플로우 단계 정의
class WorkflowStep:
    API_CALLER = "API_CALLER"
    ERROR_HANDLER = "ERROR_HANDLER"
    RETRY_LOGIC = "RETRY_LOGIC"
    FALLBACK_SERVICE = "FALLBACK_SERVICE"
    RESULT_PROCESSOR = "RESULT_PROCESSOR"


# ② 그래프 상태 정의
class RobustAPIState(BaseModel):
    api_endpoint: str = Field(default="", description="API 엔드포인트")
    request_data: Dict[str, Any] = Field(default_factory=dict, description="요청 데이터")
    
    # 실행 상태
    current_attempt: int = Field(default=0, description="현재 시도 횟수")
    max_retries: int = Field(default=3, description="최대 재시도 횟수")
    
    # 결과 및 에러
    api_response: Dict[str, Any] = Field(default_factory=dict, description="API 응답")
    error_message: str = Field(default="", description="에러 메시지")
    error_type: str = Field(default="", description="에러 타입")
    
    # 상태 플래그
    is_success: bool = Field(default=False, description="성공 여부")
    use_fallback: bool = Field(default=False, description="대체 서비스 사용 여부")
    
    # 최종 결과
    final_result: str = Field(default="", description="최종 처리 결과")
    execution_log: list = Field(default_factory=list, description="실행 로그")


# ③ API 호출 노드 (실패 시뮬레이션 포함)
def api_caller(state: RobustAPIState) -> Dict[str, Any]:
    endpoint = state.api_endpoint
    attempt = state.current_attempt + 1
    
    print(f"[api_caller] 🌐 API 호출 시도 {attempt}/{state.max_retries}")
    print(f"              엔드포인트: {endpoint}")
    
    # 로그 추가
    log_entry = f"시도 {attempt}: {endpoint} 호출"
    updated_log = state.execution_log + [log_entry]
    
    # 네트워크 지연 시뮬레이션
    time.sleep(random.uniform(0.5, 1.5))
    
    # 실패 확률 설정 (70% 실패율로 에러 처리 테스트)
    failure_rate = 0.7
    will_fail = random.random() < failure_rate
    
    if will_fail:
        # 다양한 에러 타입 시뮬레이션
        error_types = [
            ("network_timeout", "네트워크 타임아웃이 발생했습니다."),
            ("server_error", "서버 내부 오류 (500)가 발생했습니다."),
            ("rate_limit", "API 호출 한도를 초과했습니다."),
            ("authentication", "인증에 실패했습니다."),
            ("bad_request", "잘못된 요청 형식입니다.")
        ]
        
        error_type, error_msg = random.choice(error_types)
        
        print(f"[api_caller] ❌ 호출 실패: {error_msg}")
        
        return {
            "current_attempt": attempt,
            "error_type": error_type,
            "error_message": error_msg,
            "is_success": False,
            "execution_log": updated_log + [f"  → 실패: {error_msg}"]
        }
    
    else:
        # 성공 케이스
        mock_response = {
            "status": "success",
            "data": {
                "message": f"API 호출 성공! (시도 {attempt}회)",
                "timestamp": "2024-01-15T12:00:00Z",
                "request_id": f"req_{random.randint(1000, 9999)}"
            },
            "response_time": f"{random.randint(100, 500)}ms"
        }
        
        print(f"[api_caller] ✅ 호출 성공: {mock_response['response_time']}")
        
        return {
            "current_attempt": attempt,
            "api_response": mock_response,
            "is_success": True,
            "error_type": "",
            "error_message": "",
            "execution_log": updated_log + [f"  → 성공: {mock_response['response_time']}"]
        }


# ④ 에러 핸들러 노드
def error_handler(state: RobustAPIState) -> Dict[str, Any]:
    error_type = state.error_type
    error_msg = state.error_message
    attempt = state.current_attempt
    
    print(f"[error_handler] 🚨 에러 분석 중...")
    print(f"                에러 타입: {error_type}")
    print(f"                시도 횟수: {attempt}/{state.max_retries}")
    
    # 에러 타입별 처리 전략 결정
    retry_strategies = {
        "network_timeout": {"should_retry": True, "delay": 2.0, "reason": "네트워크 지연으로 인한 재시도"},
        "server_error": {"should_retry": True, "delay": 3.0, "reason": "서버 오류 복구 대기"},
        "rate_limit": {"should_retry": True, "delay": 5.0, "reason": "API 한도 초기화 대기"},
        "authentication": {"should_retry": False, "delay": 0, "reason": "인증 문제로 재시도 불가"},
        "bad_request": {"should_retry": False, "delay": 0, "reason": "요청 형식 문제로 재시도 불가"}
    }
    
    strategy = retry_strategies.get(error_type, {"should_retry": False, "delay": 0, "reason": "알 수 없는 에러"})
    
    # 재시도 가능 여부와 최대 시도 횟수 확인
    can_retry = strategy["should_retry"] and attempt < state.max_retries
    should_use_fallback = not can_retry
    
    if can_retry:
        print(f"[error_handler] 🔄 재시도 가능: {strategy['reason']}")
        print(f"                지연 시간: {strategy['delay']}초")
    else:
        print(f"[error_handler] 🔀 대체 서비스 사용: {strategy['reason']}")
    
    return {
        "use_fallback": should_use_fallback,
        "execution_log": state.execution_log + [
            f"에러 분석: {error_type} → {'재시도' if can_retry else '대체 서비스'}"
        ]
    }


# ⑤ 재시도 로직 노드
def retry_logic(state: RobustAPIState) -> Dict[str, Any]:
    error_type = state.error_type
    
    print(f"[retry_logic] ⏳ 재시도 준비 중...")
    
    # 에러 타입별 지연 시간
    delays = {
        "network_timeout": 2.0,
        "server_error": 3.0,
        "rate_limit": 5.0
    }
    
    delay = delays.get(error_type, 1.0)
    print(f"              {delay}초 대기 후 재시도...")
    
    # 실제 지연 (시뮬레이션에서는 짧게)
    time.sleep(min(delay, 1.0))
    
    print(f"[retry_logic] 🔄 재시도 준비 완료")
    
    return {
        "execution_log": state.execution_log + [f"재시도 준비: {delay}초 대기 완료"]
    }


# ⑥ 대체 서비스 노드
def fallback_service(state: RobustAPIState) -> Dict[str, Any]:
    print(f"[fallback_service] 🔀 대체 서비스 호출 중...")
    
    # 대체 서비스 시뮬레이션 (항상 성공)
    time.sleep(random.uniform(0.5, 1.0))
    
    fallback_response = {
        "status": "success_fallback",
        "data": {
            "message": "대체 서비스를 통해 응답을 제공합니다.",
            "source": "fallback_api",
            "timestamp": "2024-01-15T12:00:00Z",
            "warning": "기본 서비스 사용 불가로 인한 대체 응답"
        },
        "response_time": f"{random.randint(200, 800)}ms"
    }
    
    print(f"[fallback_service] ✅ 대체 서비스 성공: {fallback_response['response_time']}")
    
    return {
        "api_response": fallback_response,
        "is_success": True,
        "execution_log": state.execution_log + [
            f"대체 서비스 성공: {fallback_response['response_time']}"
        ]
    }


# ⑦ 결과 처리 노드
def result_processor(state: RobustAPIState) -> Dict[str, Any]:
    print(f"[result_processor] 📊 최종 결과 처리 중...")
    
    response = state.api_response
    attempts = state.current_attempt
    is_fallback = state.use_fallback
    
    # 결과 요약 생성
    result_sections = []
    
    # 헤더
    result_sections.append("🔧 견고한 API 호출 결과")
    result_sections.append("=" * 40)
    
    # 성공/실패 상태
    if state.is_success:
        if is_fallback:
            result_sections.append("✅ 상태: 대체 서비스를 통한 성공")
            result_sections.append(f"⚠️ 경고: {response['data'].get('warning', '')}")
        else:
            result_sections.append("✅ 상태: 기본 서비스 성공")
        
        result_sections.append(f"📝 메시지: {response['data']['message']}")
        result_sections.append(f"⏱️ 응답 시간: {response['response_time']}")
    else:
        result_sections.append("❌ 상태: 모든 시도 실패")
        result_sections.append(f"🚨 최종 에러: {state.error_message}")
    
    # 실행 통계
    result_sections.append(f"\n📊 실행 통계:")
    result_sections.append(f"   시도 횟수: {attempts}회")
    result_sections.append(f"   대체 서비스 사용: {'예' if is_fallback else '아니오'}")
    
    # 실행 로그
    result_sections.append(f"\n📋 실행 로그:")
    for log_entry in state.execution_log:
        result_sections.append(f"   • {log_entry}")
    
    final_result = "\n".join(result_sections)
    
    print(f"[result_processor] ✅ 결과 처리 완료")
    
    return {
        "final_result": final_result
    }


# ⑧ 라우팅 함수들
def should_retry_or_fallback(state: RobustAPIState) -> Literal["retry", "fallback", "process"]:
    """API 호출 후 라우팅 결정"""
    if state.is_success:
        return "process"
    elif state.use_fallback:
        return "fallback"
    else:
        return "retry"


def after_error_handling(state: RobustAPIState) -> Literal["retry", "fallback"]:
    """에러 처리 후 라우팅 결정"""
    if state.use_fallback:
        return "fallback"
    else:
        return "retry"


# ⑨ 그래프 생성 (에러 처리 포함)
def create_robust_api_graph():
    workflow = StateGraph(RobustAPIState)
    
    # 노드 추가
    workflow.add_node(WorkflowStep.API_CALLER, api_caller)
    workflow.add_node(WorkflowStep.ERROR_HANDLER, error_handler)
    workflow.add_node(WorkflowStep.RETRY_LOGIC, retry_logic)
    workflow.add_node(WorkflowStep.FALLBACK_SERVICE, fallback_service)
    workflow.add_node(WorkflowStep.RESULT_PROCESSOR, result_processor)
    
    # 시작점 설정
    workflow.add_edge(START, WorkflowStep.API_CALLER)
    
    # API 호출 후 조건부 라우팅 (핵심 에러 처리!)
    workflow.add_conditional_edges(
        WorkflowStep.API_CALLER,
        should_retry_or_fallback,
        {
            "retry": WorkflowStep.ERROR_HANDLER,    # 실패 시 에러 처리
            "fallback": WorkflowStep.FALLBACK_SERVICE,  # 재시도 불가 시 대체 서비스
            "process": WorkflowStep.RESULT_PROCESSOR    # 성공 시 결과 처리
        }
    )
    
    # 에러 처리 후 라우팅
    workflow.add_conditional_edges(
        WorkflowStep.ERROR_HANDLER,
        after_error_handling,
        {
            "retry": WorkflowStep.RETRY_LOGIC,      # 재시도 가능 시
            "fallback": WorkflowStep.FALLBACK_SERVICE  # 재시도 불가 시 대체 서비스
        }
    )
    
    # 재시도 로직 후 다시 API 호출 (루프!)
    workflow.add_edge(WorkflowStep.RETRY_LOGIC, WorkflowStep.API_CALLER)
    
    # 대체 서비스 후 결과 처리
    workflow.add_edge(WorkflowStep.FALLBACK_SERVICE, WorkflowStep.RESULT_PROCESSOR)
    
    # 결과 처리 후 종료
    workflow.add_edge(WorkflowStep.RESULT_PROCESSOR, END)
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


# ⑩ 테스트 함수
def test_robust_api_call():
    print("=== 견고한 API 호출 테스트 ===\n")
    
    app = create_robust_api_graph()
    
    # 테스트 케이스
    test_cases = [
        {
            "name": "사용자 정보 API",
            "endpoint": "https://api.example.com/users/123",
            "data": {"fields": ["name", "email"]}
        },
        {
            "name": "날씨 정보 API", 
            "endpoint": "https://weather.api.com/current",
            "data": {"location": "서울", "units": "metric"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 테스트 케이스 {i}: {test_case['name']} ---")
        
        initial_state = RobustAPIState(
            api_endpoint=test_case["endpoint"],
            request_data=test_case["data"],
            max_retries=3
        )
        
        print("🚀 API 호출 시작!")
        print("=" * 50)
        
        # 그래프 실행 (에러 처리 자동)
        final_state = app.invoke(initial_state)
        
        print("\n" + "=" * 50)
        print("📊 최종 결과:")
        print(final_state['final_result'])
        
        print("\n" + "-" * 50)


# ⑪ 에러 복구 시나리오 테스트
def test_error_scenarios():
    print("\n=== 특정 에러 시나리오 테스트 ===\n")
    
    app = create_robust_api_graph()
    
    scenarios = [
        "일반 API 호출 (랜덤 실패)",
        "높은 신뢰성 요구 서비스",
        "중요한 결제 API"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"--- 시나리오 {i}: {scenario} ---")
        
        initial_state = RobustAPIState(
            api_endpoint=f"https://api.service{i}.com/endpoint",
            request_data={"scenario": scenario},
            max_retries=3
        )
        
        final_state = app.invoke(initial_state)
        
        # 요약 결과만 출력
        success = final_state['is_success']
        attempts = final_state['current_attempt']
        fallback = final_state['use_fallback']
        
        status = "✅ 성공" if success else "❌ 실패"
        method = f"({'대체 서비스' if fallback else '기본 서비스'})" if success else ""
        
        print(f"결과: {status} {method} - {attempts}회 시도")
        print()


def main():
    print("=== LangGraph 에러 처리 예제 ===\n")
    
    # 기본 테스트
    test_robust_api_call()
    
    # 에러 시나리오 테스트
    test_error_scenarios()
    
    # 그래프 시각화
    print("\n=== 워크플로우 시각화 ===")
    app = create_robust_api_graph()
    
    # ASCII 그래프 출력
    ascii_graph = app.get_graph().draw_ascii()
    print("\n[ASCII 그래프]")
    print(ascii_graph)
    
    # Mermaid PNG 생성
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./06_error_handling.png", "wb") as f:
            f.write(mermaid_png)
        print("\n[그래프 이미지] 06_error_handling.png 파일이 생성되었습니다!")
    except Exception as e:
        print(f"\n[그래프 이미지] 생성 실패: {e}")


if __name__ == "__main__":
    main()
