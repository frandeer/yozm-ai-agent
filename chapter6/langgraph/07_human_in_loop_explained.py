"""
🎯 Human-in-the-Loop (사람이 루프 안에 있다!)
===============================================

핵심 개념:
    AI 에이전트가 작업을 수행하다가
    → 정보가 부족하면 사람에게 물어보고
    → 사람의 답변을 받아서
    → 다시 작업을 계속 진행!
    
실생활 비유:
    - 레스토랑에서 주문할 때 웨이터가 "매운 맛 어느 정도로 하시겠어요?" 물어보는 것
    - 의사가 "언제부터 아팠나요?" 추가 정보 물어보는 것
    - 친구가 "몇 시에 만날까?" 물어보는 것

이 모든 상황에서 대화 중간에 사람의 입력이 필요합니다!
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1️⃣ 상태 정의: 워크플로우 전체에서 공유되는 정보
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class AgentState(BaseModel):
    """에이전트의 상태를 정의합니다."""
    
    user_message: str = Field(
        default="", 
        description="사용자가 처음에 요청한 내용 (예: '블로그 글 작성')"
    )
    
    task_details: str = Field(
        default="", 
        description="사용자가 추가로 제공한 상세 정보 (예: '파이썬 튜토리얼에 대한 글')"
    )
    
    response: str = Field(
        default="", 
        description="LLM이 생성한 응답 (질문 또는 최종 답변)"
    )
    
    interaction_count: int = Field(
        default=0,
        description="사람과 몇 번 대화했는지 추적"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2️⃣ 노드 1: LLM에게 물어보기
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def llm_node(state: AgentState, llm) -> dict:
    """
    🤖 AI(LLM)가 응답을 생성하는 노드
    
    역할:
        - 상세 정보가 있으면 → 최종 답변 생성
        - 상세 정보가 없으면 → 사용자에게 질문 생성
    
    비유:
        레스토랑 웨이터가 주문을 듣고
        "무엇을 드시겠어요?" 또는 "매운맛은 어느 정도로 하시겠어요?" 물어보는 것
    """
    print("\n" + "="*60)
    print("🤖 [AI 노드] LLM이 생각 중...")
    print("="*60)
    
    # 상태 확인
    details = state.task_details
    task = state.user_message
    count = state.interaction_count
    
    print(f"📊 현재 상태:")
    print(f"   - 초기 요청: {task}")
    print(f"   - 받은 상세정보: {details if details else '(아직 없음)'}")
    print(f"   - 대화 횟수: {count}회")
    
    # 시나리오 분기
    if details:
        # 상세 정보가 있으면 → 최종 보고서 작성
        print(f"\n✅ 충분한 정보를 받았습니다! 최종 답변을 생성합니다.")
        prompt = f"""다음 요청에 대한 상세한 보고서를 작성해주세요:

요청: {task}
상세 정보: {details}

3-4문장으로 구체적인 보고서를 작성하세요. 질문하지 말고 최종 답변만 제공하세요."""
    else:
        # 상세 정보가 없으면 → 질문 생성
        print(f"\n❓ 정보가 부족합니다. 사용자에게 질문을 생성합니다.")
        prompt = f"""사용자가 '{task}' 작업을 요청했습니다.

이 작업을 수행하기 위해 필요한 정보를 물어보세요:
- 어떤 주제/내용인지
- 어떤 스타일/형식인지
- 누구를 대상으로 하는지

반드시 질문은 물음표('?')로 끝내주세요. 한 번에 2-3가지를 물어보세요."""
    
    # LLM 호출
    print(f"\n🔄 LLM에게 요청 중...")
    response = llm.invoke(prompt).content
    
    print(f"\n💬 LLM 응답:")
    print(f"   {response}")
    print("="*60)
    
    return {
        "response": response,
        "task_details": "",  # 다음 사이클을 위해 초기화
        "interaction_count": count + 1
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3️⃣ 노드 2: 사람에게 물어보기 (Human-in-the-Loop의 핵심!)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def human_input_node(state: AgentState) -> dict:
    """
    👤 사람에게 입력을 받는 노드 (Human-in-the-Loop!)
    
    역할:
        - LLM의 질문을 사용자에게 보여줌
        - 사용자의 답변을 받아서 상태에 저장
    
    비유:
        웨이터가 "매운맛 어느 정도로 하시겠어요?" 물어보고
        손님의 대답을 기다리는 것
    
    ⚠️ 핵심: 여기서 워크플로우가 멈추고 사람의 입력을 기다립니다!
    """
    print("\n" + "🔔"*30)
    print("👤 [사람 노드] AI가 추가 정보를 요청했습니다!")
    print("🔔"*60)
    print(f"\n❓ AI의 질문: {state.response}")
    print("\n💭 위 질문에 답변해주세요:")
    
    # ⭐ 핵심: input()으로 워크플로우가 멈추고 사용자 입력 대기!
    user_input = input("답변 👉 ")
    
    print(f"\n✅ 답변 받음: {user_input}")
    print("🔔"*60)
    
    return {
        "task_details": user_input
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4️⃣ 라우팅 함수: 다음에 어디로 갈지 결정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def route_after_llm(state: AgentState) -> Literal["need_human_input", "done"]:
    """
    🧭 라우터: LLM 응답을 분석해서 다음 단계 결정
    
    결정 기준:
        - 응답이 '?'로 끝나면 → 질문이다 → 사람에게 물어봐야 함
        - 응답이 '?'로 안 끝나면 → 최종 답변이다 → 완료!
    
    비유:
        교통 신호등이 빨간불인지 초록불인지 확인해서
        멈출지 계속 갈지 결정하는 것
    """
    print("\n" + "🧭"*30)
    print("🧭 [라우터] 다음 단계를 결정합니다...")
    print("🧭"*60)
    
    response = state.response.strip()
    
    # 응답이 물음표로 끝나는지 확인
    if response.endswith("?"):
        print("📌 판단: 응답이 '?'로 끝남 → AI가 질문함")
        print("🔄 결정: 사람에게 입력을 받으러 갑니다 (Human-in-the-Loop!)")
        print("🧭"*60)
        return "need_human_input"
    else:
        print("📌 판단: 응답이 '?'로 안 끝남 → 최종 답변임")
        print("✅ 결정: 작업 완료! 워크플로우 종료")
        print("🧭"*60)
        return "done"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5️⃣ 그래프 생성: 노드들을 연결
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_graph():
    """
    🏗️ Human-in-the-Loop 워크플로우 그래프 생성
    
    그래프 흐름:
        START
          ↓
        [AI 노드] ← ─────┐
          ↓               │
        {라우터}          │
          ↓ ↘            │
          ↓   ↘          │
          ↓     [사람 노드]
          ↓        ↓      │
         END    ───┘      │
                          │
        (루프: 사람→AI→사람→AI... 반복 가능!)
    """
    # LLM 초기화
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")
    
    # LLM을 클로저로 캡처하는 래퍼 함수
    def llm_node_with_llm(state):
        return llm_node(state, llm)
    
    # 그래프 생성
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("ai", llm_node_with_llm)         # AI가 생각하는 노드
    workflow.add_node("human", human_input_node)       # 사람이 입력하는 노드
    
    # 엣지 연결
    workflow.add_edge(START, "ai")                     # 시작 → AI
    
    # 조건부 엣지: AI 응답을 보고 다음 단계 결정
    workflow.add_conditional_edges(
        "ai",                    # AI 노드 다음에
        route_after_llm,         # 라우터 함수로 판단
        {
            "need_human_input": "human",   # 질문이면 → 사람 노드로
            "done": END                    # 완료면 → 종료
        }
    )
    
    # 사람 노드 다음에는 다시 AI로 (루프!)
    workflow.add_edge("human", "ai")
    
    return workflow.compile()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6️⃣ 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "🔄 Human-in-the-Loop 상세 설명 예제" + " "*10 + "║")
    print("╚" + "="*58 + "╝")
    
    print("""
💡 이 예제의 흐름:
    1. 사용자: "블로그 글 작성" 요청
    2. AI: "어떤 주제인가요?" (질문) ← 정보 부족!
    3. 👤 사람: "파이썬 튜토리얼" 입력 ← Human-in-the-Loop!
    4. AI: 최종 보고서 작성 (완료)
    
⚠️ 핵심 포인트:
    - 3번 단계에서 워크플로우가 멈추고 사람의 입력을 기다립니다
    - 사람이 답변하면 다시 워크플로우가 계속됩니다
    - 이것이 "Human-in-the-Loop"입니다!
""")
    
    # 그래프 생성
    app = create_graph()
    
    # 초기 상태로 실행
    initial_state = AgentState(user_message="블로그 글 작성")
    
    print("\n🚀 워크플로우 시작!\n")
    final_state = app.invoke(initial_state)
    
    # 최종 결과
    print("\n" + "🎉"*30)
    print("🎉 워크플로우 완료!")
    print("🎉"*60)
    print(f"\n📝 최종 응답:\n")
    print(final_state["response"])
    print(f"\n📊 총 대화 횟수: {final_state['interaction_count']}회")
    print("\n" + "🎉"*60)
    
    # 그래프 시각화 (선택사항)
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./07_human_in_loop_explained.png", "wb") as f:
            f.write(mermaid_png)
        print("\n💾 그래프 이미지가 저장되었습니다: 07_human_in_loop_explained.png")
    except Exception as e:
        print(f"\n⚠️ 그래프 시각화 실패: {e}")


if __name__ == "__main__":
    main()

