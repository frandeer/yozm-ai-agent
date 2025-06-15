from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import random


# ① 워크플로우 단계 정의
class WorkflowStep:
    GAME_SETUP = "GAME_SETUP"
    USER_GUESS = "USER_GUESS"
    CHECK_GUESS = "CHECK_GUESS"
    PROVIDE_HINT = "PROVIDE_HINT"
    GAME_END = "GAME_END"


# ② 그래프 상태 정의
class GuessGameState(BaseModel):
    target_number: int = Field(default=0, description="맞춰야 할 숫자")
    user_guess: int = Field(default=0, description="사용자 추측")
    attempts: int = Field(default=0, description="시도 횟수")
    max_attempts: int = Field(default=7, description="최대 시도 횟수")
    min_range: int = Field(default=1, description="범위 최솟값")
    max_range: int = Field(default=100, description="범위 최댓값")
    game_status: str = Field(default="playing", description="게임 상태: playing/won/lost")
    hint_message: str = Field(default="", description="힌트 메시지")
    response: str = Field(default="", description="최종 응답")
    guess_history: list = Field(default_factory=list, description="추측 기록")


# ③ 게임 설정 노드
def game_setup(state: GuessGameState) -> Dict[str, Any]:
    target = random.randint(state.min_range, state.max_range)
    
    print(f"[game_setup] 🎯 목표 숫자: {target} (범위: {state.min_range}-{state.max_range})")
    print(f"[game_setup] 🎮 최대 시도 횟수: {state.max_attempts}회")
    
    setup_message = (
        f"🎲 숫자 맞추기 게임을 시작합니다!\n"
        f"📊 범위: {state.min_range} ~ {state.max_range}\n"
        f"🎯 최대 시도 횟수: {state.max_attempts}회\n"
        f"💭 첫 번째 숫자를 추측해보세요!"
    )
    
    return {
        "target_number": target,
        "game_status": "playing",
        "response": setup_message,
        "attempts": 0,
        "guess_history": []
    }


# ④ 사용자 추측 노드 (실제로는 시뮬레이션)
def user_guess(state: GuessGameState) -> Dict[str, Any]:
    # 실제 사용자 입력 대신 랜덤 추측 (시뮬레이션)
    min_val = state.min_range
    max_val = state.max_range
    
    # 이전 추측들을 고려한 스마트한 추측
    if state.guess_history:
        last_guess = state.guess_history[-1]
        if last_guess["result"] == "too_high":
            max_val = min(max_val, last_guess["guess"] - 1)
        elif last_guess["result"] == "too_low":
            min_val = max(min_val, last_guess["guess"] + 1)
    
    # 유효한 범위에서 랜덤 추측
    if min_val <= max_val:
        guess = random.randint(min_val, max_val)
    else:
        guess = random.randint(state.min_range, state.max_range)
    
    print(f"[user_guess] 🤔 사용자 추측: {guess}")
    
    return {
        "user_guess": guess,
        "attempts": state.attempts + 1
    }


# ⑤ 추측 확인 노드
def check_guess(state: GuessGameState) -> Dict[str, Any]:
    target = state.target_number
    guess = state.user_guess
    attempts = state.attempts
    
    print(f"[check_guess] 🔍 추측 확인: {guess} vs 목표: {target}")
    
    # 결과 판정
    if guess == target:
        # 정답!
        game_status = "won"
        result = "correct"
        response = f"🎉 축하합니다! {guess}가 정답입니다!\n{attempts}번 만에 맞추셨네요!"
        hint_message = ""
    elif attempts >= state.max_attempts:
        # 시도 횟수 초과
        game_status = "lost"
        result = "game_over"
        response = f"😔 게임 종료! 시도 횟수를 모두 사용했습니다.\n정답은 {target}이었습니다."
        hint_message = ""
    else:
        # 계속 플레이
        game_status = "playing"
        if guess < target:
            result = "too_low"
            hint_message = f"📈 {guess}보다 큽니다!"
        else:
            result = "too_high"
            hint_message = f"📉 {guess}보다 작습니다!"
        
        remaining = state.max_attempts - attempts
        response = f"❌ 틀렸습니다! 남은 기회: {remaining}회"
    
    # 추측 기록 업데이트
    updated_history = state.guess_history + [{
        "guess": guess,
        "result": result,
        "attempt": attempts
    }]
    
    print(f"[check_guess] 📊 결과: {result}, 게임 상태: {game_status}")
    
    return {
        "game_status": game_status,
        "hint_message": hint_message,
        "response": response,
        "guess_history": updated_history
    }


# ⑥ 힌트 제공 노드
def provide_hint(state: GuessGameState) -> Dict[str, Any]:
    hint = state.hint_message
    attempts = state.attempts
    remaining = state.max_attempts - attempts
    
    # 추가 힌트 생성
    target = state.target_number
    extra_hints = []
    
    if attempts >= 3:  # 3번째 시도부터 추가 힌트 제공
        if target % 2 == 0:
            extra_hints.append("🔢 짝수입니다")
        else:
            extra_hints.append("🔢 홀수입니다")
    
    if attempts >= 5:  # 5번째 시도부터 더 구체적인 힌트
        if target <= 25:
            extra_hints.append("📍 25 이하입니다")
        elif target <= 50:
            extra_hints.append("📍 26~50 사이입니다")
        elif target <= 75:
            extra_hints.append("📍 51~75 사이입니다")
        else:
            extra_hints.append("📍 76 이상입니다")
    
    full_hint = hint
    if extra_hints:
        full_hint += f"\n💡 추가 힌트: {', '.join(extra_hints)}"
    
    full_response = f"{state.response}\n{full_hint}\n🎯 다음 숫자를 추측해보세요! (남은 기회: {remaining}회)"
    
    print(f"[provide_hint] 💭 힌트 제공: {full_hint}")
    
    return {
        "response": full_response
    }


# ⑦ 게임 종료 노드
def game_end(state: GuessGameState) -> Dict[str, Any]:
    attempts = state.attempts
    game_status = state.game_status
    
    if game_status == "won":
        final_message = f"{state.response}\n\n🏆 게임 통계:\n📊 총 시도 횟수: {attempts}회\n⭐ 성공률: {((state.max_attempts - attempts + 1) / state.max_attempts * 100):.1f}%"
    else:
        final_message = f"{state.response}\n\n📊 게임 통계:\n❌ 총 시도 횟수: {attempts}회\n🎯 정답: {state.target_number}"
    
    print(f"[game_end] 🏁 게임 종료: {game_status}")
    
    return {
        "response": final_message
    }


# ⑧ 조건부 라우팅 함수들
def should_continue_game(state: GuessGameState) -> Literal["continue", "end"]:
    """게임을 계속할지 결정하는 라우팅 함수"""
    game_status = state.game_status
    
    print(f"[routing] 게임 상태: {game_status}")
    
    if game_status == "playing":
        return "continue"
    else:
        return "end"


def route_after_check(state: GuessGameState) -> Literal["hint", "end"]:
    """추측 확인 후 라우팅 함수"""
    game_status = state.game_status
    
    if game_status == "playing":
        return "hint"
    else:
        return "end"


# ⑨ 그래프 생성 (루프 포함)
def create_guess_game_graph():
    workflow = StateGraph(GuessGameState)
    
    # 노드 추가
    workflow.add_node(WorkflowStep.GAME_SETUP, game_setup)
    workflow.add_node(WorkflowStep.USER_GUESS, user_guess)
    workflow.add_node(WorkflowStep.CHECK_GUESS, check_guess)
    workflow.add_node(WorkflowStep.PROVIDE_HINT, provide_hint)
    workflow.add_node(WorkflowStep.GAME_END, game_end)
    
    # 시작점 설정
    workflow.add_edge(START, WorkflowStep.GAME_SETUP)
    
    # 게임 설정 후 첫 추측으로
    workflow.add_edge(WorkflowStep.GAME_SETUP, WorkflowStep.USER_GUESS)
    
    # 추측 후 확인
    workflow.add_edge(WorkflowStep.USER_GUESS, WorkflowStep.CHECK_GUESS)
    
    # 확인 후 조건부 라우팅 (핵심 루프 부분!)
    workflow.add_conditional_edges(
        WorkflowStep.CHECK_GUESS,
        route_after_check,
        {
            "hint": WorkflowStep.PROVIDE_HINT,  # 게임 계속 → 힌트 제공
            "end": WorkflowStep.GAME_END        # 게임 종료 → 종료 처리
        }
    )
    
    # 힌트 제공 후 다시 추측으로 (루프!)
    workflow.add_edge(WorkflowStep.PROVIDE_HINT, WorkflowStep.USER_GUESS)
    
    # 게임 종료 후 END
    workflow.add_edge(WorkflowStep.GAME_END, END)
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


# ⑩ 테스트 함수
def test_guess_game():
    print("=== 숫자 맞추기 게임 테스트 ===\n")
    
    app = create_guess_game_graph()
    
    # 게임 설정
    initial_state = GuessGameState(
        min_range=1,
        max_range=50,
        max_attempts=6
    )
    
    print("🎮 게임 시작!")
    print("=" * 50)
    
    # 그래프 실행 (루프가 자동으로 처리됨)
    final_state = app.invoke(initial_state)
    
    print("\n" + "=" * 50)
    print("🏁 최종 결과:")
    print(final_state['response'])
    
    print(f"\n📊 상세 통계:")
    print(f"   - 게임 상태: {final_state['game_status']}")
    print(f"   - 목표 숫자: {final_state['target_number']}")
    print(f"   - 총 시도: {final_state['attempts']}회")
    print(f"   - 추측 기록: {final_state['guess_history']}")


# ⑪ 여러 게임 테스트
def test_multiple_games():
    print("\n=== 여러 게임 통계 테스트 ===\n")
    
    app = create_guess_game_graph()
    
    games = 3
    results = {"won": 0, "lost": 0, "total_attempts": 0}
    
    for i in range(games):
        print(f"\n--- 게임 {i+1} ---")
        
        initial_state = GuessGameState(
            min_range=1,
            max_range=30,  # 더 작은 범위로 테스트
            max_attempts=5
        )
        
        final_state = app.invoke(initial_state)
        
        results[final_state['game_status']] += 1
        results["total_attempts"] += final_state['attempts']
        
        print(f"결과: {final_state['game_status']}, 시도: {final_state['attempts']}회")
    
    print(f"\n📈 전체 통계:")
    print(f"   - 승리: {results['won']}게임")
    print(f"   - 패배: {results['lost']}게임")
    print(f"   - 승률: {results['won']/games*100:.1f}%")
    print(f"   - 평균 시도: {results['total_attempts']/games:.1f}회")


def main():
    print("=== LangGraph 루프 워크플로우 예제 ===\n")
    
    # 단일 게임 테스트
    test_guess_game()
    
    # 여러 게임 통계 테스트
    test_multiple_games()
    
    # 그래프 시각화
    print("\n=== 워크플로우 시각화 ===")
    app = create_guess_game_graph()
    
    # ASCII 그래프 출력
    ascii_graph = app.get_graph().draw_ascii()
    print("\n[ASCII 그래프]")
    print(ascii_graph)
    
    # Mermaid PNG 생성
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./04_loop_workflow.png", "wb") as f:
            f.write(mermaid_png)
        print("\n[그래프 이미지] 04_loop_workflow.png 파일이 생성되었습니다!")
    except Exception as e:
        print(f"\n[그래프 이미지] 생성 실패: {e}")


if __name__ == "__main__":
    main()
