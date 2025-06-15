from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import json
import os


# ① 워크플로우 단계 정의
class WorkflowStep:
    LOAD_MEMORY = "LOAD_MEMORY"
    PROCESS_MESSAGE = "PROCESS_MESSAGE"
    SAVE_MEMORY = "SAVE_MEMORY"


# ② 그래프 상태 정의
class MemoryBotState(BaseModel):
    user_message: str = Field(default="", description="사용자 입력 메시지")
    user_name: str = Field(default="", description="사용자 이름")
    conversation_history: list = Field(default_factory=list, description="대화 기록")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="사용자 선호도")
    response: str = Field(default="", description="최종 응답")
    session_id: str = Field(default="default", description="세션 ID")


# ③ 메모리 로드 노드
def load_memory(state: MemoryBotState) -> Dict[str, Any]:
    session_id = state.session_id
    print(f"[load_memory] 세션 '{session_id}'의 메모리를 불러오는 중...")
    
    # 기존 대화 기록과 사용자 정보가 이미 있다면 그대로 사용
    if state.conversation_history or state.user_name:
        print(f"[load_memory] 기존 메모리 발견: 사용자={state.user_name}, 대화수={len(state.conversation_history)}")
        return {}
    
    # 새 세션의 경우 빈 상태로 시작
    print(f"[load_memory] 새로운 세션 시작")
    return {
        "conversation_history": [],
        "user_preferences": {},
        "user_name": ""
    }


# ④ 메시지 처리 노드
def process_message(state: MemoryBotState) -> Dict[str, Any]:
    message = state.user_message
    user_name = state.user_name
    history = state.conversation_history
    preferences = state.user_preferences
    
    print(f"[process_message] 메시지 처리: '{message}'")
    
    response = ""
    updated_name = user_name
    updated_preferences = preferences.copy()
    
    # 이름 학습
    if "내 이름은" in message or "나는" in message:
        # 간단한 이름 추출
        if "내 이름은" in message:
            name_part = message.split("내 이름은")[1].strip()
            name = name_part.split()[0].replace("이야", "").replace("야", "").replace("입니다", "").replace(".", "")
            updated_name = name
            response = f"안녕하세요, {name}님! 이름을 기억하겠습니다. 😊"
        elif "나는" in message:
            name_part = message.split("나는")[1].strip()
            name = name_part.split()[0].replace("이야", "").replace("야", "").replace("입니다", "").replace(".", "")
            updated_name = name
            response = f"반가워요, {name}님! 😊"
    
    # 선호도 학습
    elif "좋아해" in message or "싫어해" in message:
        if "좋아해" in message:
            item = message.replace("좋아해", "").replace("를", "").replace("을", "").strip()
            if "likes" not in updated_preferences:
                updated_preferences["likes"] = []
            updated_preferences["likes"].append(item)
            response = f"{item}를 좋아하시는군요! 기억해두겠습니다. 👍"
        elif "싫어해" in message:
            item = message.replace("싫어해", "").replace("를", "").replace("을", "").strip()
            if "dislikes" not in updated_preferences:
                updated_preferences["dislikes"] = []
            updated_preferences["dislikes"].append(item)
            response = f"{item}는 싫어하시는군요. 알겠습니다. 😅"
    
    # 이름 확인 질문
    elif "내 이름" in message and ("뭐" in message or "무엇" in message):
        if updated_name:
            response = f"당신의 이름은 {updated_name}님이시죠! 😊"
        else:
            response = "아직 이름을 알려주시지 않으셨어요. 이름을 가르쳐 주세요! 🤔"
    
    # 선호도 확인 질문
    elif "뭘 좋아하는지" in message or "좋아하는 것" in message:
        if "likes" in updated_preferences and updated_preferences["likes"]:
            likes = ", ".join(updated_preferences["likes"])
            response = f"지금까지 말씀해주신 좋아하는 것들: {likes} 이네요! 😄"
        else:
            response = "아직 좋아하시는 것을 알려주시지 않으셨어요! 😊"
    
    # 대화 기록 확인
    elif "우리가 뭘 얘기했는지" in message or "대화 기록" in message:
        if history:
            response = f"지금까지 {len(history)}번의 대화를 나눴네요! 최근 대화들을 기억하고 있어요. 💭"
        else:
            response = "이제 막 대화를 시작했네요! 😊"
    
    # 일반적인 인사나 대화
    else:
        if updated_name:
            response = f"{updated_name}님, 안녕하세요! 오늘은 어떤 이야기를 나누고 싶으세요? 😊"
        else:
            response = "안녕하세요! 저는 여러분을 기억하는 챗봇이에요. 이름을 알려주시면 더 친근하게 대화할 수 있어요! 😊"
    
    # 대화 기록에 추가
    updated_history = history + [
        {"user": message, "bot": response, "timestamp": "now"}
    ]
    
    print(f"[process_message] 응답 생성: '{response}'")
    print(f"[process_message] 업데이트된 사용자명: '{updated_name}'")
    print(f"[process_message] 대화 기록 수: {len(updated_history)}")
    
    return {
        "response": response,
        "user_name": updated_name,
        "conversation_history": updated_history,
        "user_preferences": updated_preferences
    }


# ⑤ 메모리 저장 노드
def save_memory(state: MemoryBotState) -> Dict[str, Any]:
    session_id = state.session_id
    user_name = state.user_name
    history_count = len(state.conversation_history)
    preferences_count = len(state.user_preferences)
    
    print(f"[save_memory] 세션 '{session_id}' 메모리 저장 완료")
    print(f"[save_memory] 사용자: {user_name}, 대화수: {history_count}, 선호도: {preferences_count}개")
    
    # 실제로는 체크포인팅 시스템이 자동으로 저장함
    return {}


# ⑥ 메모리 저장소 (간단한 딕셔너리 방식)
memory_storage = {}

def save_session_memory(session_id: str, state: MemoryBotState):
    """세션 메모리를 저장소에 저장"""
    memory_storage[session_id] = {
        "user_name": state.user_name,
        "conversation_history": state.conversation_history,
        "user_preferences": state.user_preferences
    }

def load_session_memory(session_id: str) -> Dict[str, Any]:
    """세션 메모리를 저장소에서 로드"""
    if session_id in memory_storage:
        return memory_storage[session_id]
    return {
        "user_name": "",
        "conversation_history": [],
        "user_preferences": {}
    }

# ⑦ 그래프 생성 (간단한 메모리 방식)
def create_memory_bot_graph():
    workflow = StateGraph(MemoryBotState)
    
    # 노드 추가
    workflow.add_node(WorkflowStep.LOAD_MEMORY, load_memory)
    workflow.add_node(WorkflowStep.PROCESS_MESSAGE, process_message)
    workflow.add_node(WorkflowStep.SAVE_MEMORY, save_memory)
    
    # 엣지 설정
    workflow.add_edge(START, WorkflowStep.LOAD_MEMORY)
    workflow.add_edge(WorkflowStep.LOAD_MEMORY, WorkflowStep.PROCESS_MESSAGE)
    workflow.add_edge(WorkflowStep.PROCESS_MESSAGE, WorkflowStep.SAVE_MEMORY)
    workflow.add_edge(WorkflowStep.SAVE_MEMORY, END)
    
    # 일반 컴파일
    app = workflow.compile()
    
    return app

# ⑧ 대화 세션 관리
def chat_with_memory_bot(app, session_id: str, message: str):
    """메모리 저장소를 활용한 대화"""
    
    # 기존 메모리 로드
    saved_memory = load_session_memory(session_id)
    
    initial_state = MemoryBotState(
        user_message=message,
        session_id=session_id,
        user_name=saved_memory["user_name"],
        conversation_history=saved_memory["conversation_history"],
        user_preferences=saved_memory["user_preferences"]
    )
    
    # 그래프 실행
    final_state = app.invoke(initial_state)
    
    # 메모리 저장
    save_session_memory(session_id, MemoryBotState(**final_state))
    
    return final_state


# ⑨ 테스트 함수
def test_memory_bot():
    print("=== 지속적 메모리 챗봇 테스트 ===\n")
    
    app = create_memory_bot_graph()
    session_id = "user_123"
    
    # 테스트 시나리오: 연속적인 대화
    conversations = [
        "안녕하세요!",
        "내 이름은 철수야",
        "나는 피자를 좋아해",
        "커피는 싫어해",
        "안녕! 나 기억하니?",
        "내 이름이 뭐였지?",
        "내가 뭘 좋아하는지 기억해?",
        "우리가 뭘 얘기했는지 알려줘",
    ]
    
    print(f"세션 ID: {session_id}")
    print("=" * 60)
    
    for i, message in enumerate(conversations, 1):
        print(f"\n[대화 {i}] 사용자: {message}")
        
        result = chat_with_memory_bot(app, session_id, message)
        
        print(f"[대화 {i}] 챗봇: {result['response']}")
        print(f"[메모리] 이름: {result.get('user_name', '없음')}")
        print(f"[메모리] 대화수: {len(result.get('conversation_history', []))}")
        print(f"[메모리] 선호도: {result.get('user_preferences', {})}")
        print("-" * 40)


# ⑨ 새 세션 테스트
def test_new_session():
    print("\n=== 새로운 세션 테스트 ===\n")
    
    app = create_memory_bot_graph()
    new_session_id = "user_456"
    
    print(f"새 세션 ID: {new_session_id}")
    
    # 새 세션에서 테스트
    message = "안녕하세요! 저를 기억하시나요?"
    result = chat_with_memory_bot(app, new_session_id, message)
    
    print(f"사용자: {message}")
    print(f"챗봇: {result['response']}")
    print(f"[메모리] 이름: {result.get('user_name', '없음')}")
    print(f"[메모리] 대화수: {len(result.get('conversation_history', []))}")


def main():
    print("=== LangGraph 지속적 메모리 예제 ===\n")
    
    # 메모리 봇 테스트
    test_memory_bot()
    
    # 새 세션 테스트
    test_new_session()
    
    # 그래프 시각화
    print("\n=== 워크플로우 시각화 ===")
    app = create_memory_bot_graph()
    
    # ASCII 그래프 출력
    ascii_graph = app.get_graph().draw_ascii()
    print("\n[ASCII 그래프]")
    print(ascii_graph)
    
    # Mermaid PNG 생성
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./03_persistent_memory.png", "wb") as f:
            f.write(mermaid_png)
        print("\n[그래프 이미지] 03_persistent_memory.png 파일이 생성되었습니다!")
    except Exception as e:
        print(f"\n[그래프 이미지] 생성 실패: {e}")


if __name__ == "__main__":
    main()
