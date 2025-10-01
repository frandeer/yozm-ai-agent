from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json


# ① 게임 상태 정의
class StoryGameState(BaseModel):
    story_context: str = Field(default="", description="현재까지의 스토리 맥락")
    current_scene: str = Field(default="", description="현재 장면 설명")
    choices: list[str] = Field(default_factory=list, description="사용자 선택지")
    user_choice: str = Field(default="", description="사용자가 선택한 내용")
    turn_count: int = Field(default=0, description="진행된 턴 수")
    max_turns: int = Field(default=5, description="최대 턴 수")
    game_status: str = Field(default="playing", description="게임 상태: playing, ended")


# LLM 초기화
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)


# ② 스토리 시작 노드
def start_story(state: StoryGameState) -> Dict[str, Any]:
    """게임을 시작하고 첫 번째 장면을 생성합니다."""
    print("\n=== 🎮 AI 스토리 어드벤처 게임 시작! ===\n")
    
    system_prompt = """당신은 창의적인 인터랙티브 스토리 작가입니다.
판타지 어드벤처 스토리의 시작 장면을 생성하세요.

다음 JSON 형식으로 응답하세요:
{
  "scene": "장면 설명 (3-4문장, 생생하고 흥미진진하게)",
  "choices": ["선택지1", "선택지2", "선택지3"]
}

스토리는 흥미롭고 몰입감 있게 작성하세요."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="모험이 시작되는 첫 장면을 만들어주세요.")
    ]
    
    response = llm.invoke(messages)
    result = json.loads(response.content)
    
    scene = result["scene"]
    choices = result["choices"]
    
    print(f"📖 {scene}\n")
    print("🎯 선택지:")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    
    return {
        "story_context": scene,
        "current_scene": scene,
        "choices": choices,
        "turn_count": 1,
        "game_status": "playing"
    }


# ③ 사용자 선택 입력 노드
def get_user_choice(state: StoryGameState) -> Dict[str, Any]:
    """사용자로부터 선택을 입력받습니다."""
    print(f"\n--- 턴 {state.turn_count} ---")
    
    while True:
        try:
            choice_num = int(input("선택하세요 (번호 입력): "))
            if 1 <= choice_num <= len(state.choices):
                user_choice = state.choices[choice_num - 1]
                print(f"✅ 선택: {user_choice}")
                return {"user_choice": user_choice}
            else:
                print(f"1-{len(state.choices)} 사이의 숫자를 입력하세요.")
        except ValueError:
            print("숫자를 입력하세요.")


# ④ 다음 장면 생성 노드 (AI가 스토리 진행)
def generate_next_scene(state: StoryGameState) -> Dict[str, Any]:
    """사용자 선택에 따라 다음 장면을 AI가 생성합니다."""
    print("\n🤔 AI가 다음 이야기를 생성 중...\n")
    
    system_prompt = f"""당신은 인터랙티브 스토리 작가입니다.
이전 스토리와 사용자의 선택을 바탕으로 다음 장면을 생성하세요.

이전 맥락: {state.story_context}
사용자 선택: {state.user_choice}

다음 JSON 형식으로 응답하세요:
{{
  "scene": "다음 장면 설명 (3-4문장, 사용자 선택의 결과를 반영)",
  "choices": ["선택지1", "선택지2", "선택지3"]
}}

스토리는 자연스럽게 연결되고 흥미진진해야 합니다."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="다음 장면을 생성해주세요.")
    ]
    
    response = llm.invoke(messages)
    result = json.loads(response.content)
    
    scene = result["scene"]
    choices = result["choices"]
    
    # 맥락 업데이트
    new_context = f"{state.story_context}\n\n[선택: {state.user_choice}]\n{scene}"
    
    print(f"📖 {scene}\n")
    print("🎯 선택지:")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    
    return {
        "story_context": new_context,
        "current_scene": scene,
        "choices": choices,
        "turn_count": state.turn_count + 1
    }


# ⑤ 스토리 종료 노드
def end_story(state: StoryGameState) -> Dict[str, Any]:
    """스토리를 마무리합니다."""
    print("\n🎬 AI가 스토리 결말을 생성 중...\n")
    
    system_prompt = f"""당신은 스토리 작가입니다.
다음 스토리를 감동적이고 만족스럽게 마무리하세요.

스토리 맥락:
{state.story_context}

마지막 선택: {state.user_choice}

2-3문장으로 멋진 결말을 작성하세요."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="스토리를 마무리해주세요.")
    ]
    
    response = llm.invoke(messages)
    ending = response.content
    
    print(f"📖 {ending}\n")
    print("🎉 === 게임 종료 === 🎉")
    
    return {
        "current_scene": ending,
        "game_status": "ended"
    }


# ⑥ 라우팅 함수
def route_game(state: StoryGameState) -> Literal["continue", "end"]:
    """게임 진행 상태에 따라 다음 노드를 결정합니다."""
    if state.turn_count >= state.max_turns:
        return "end"
    return "continue"


# ⑦ 그래프 생성
def create_story_game_graph():
    """AI 스토리 어드벤처 게임 그래프를 생성합니다."""
    workflow = StateGraph(StoryGameState)
    
    # 노드 추가
    workflow.add_node("start", start_story)
    workflow.add_node("get_choice", get_user_choice)
    workflow.add_node("generate", generate_next_scene)
    workflow.add_node("ending", end_story)
    
    # 엣지 연결
    workflow.add_edge(START, "start")
    workflow.add_edge("start", "get_choice")
    
    # 조건부 엣지 - 게임 계속 또는 종료
    workflow.add_conditional_edges(
        "get_choice",
        route_game,
        {
            "continue": "generate",
            "end": "ending"
        }
    )
    
    # 다음 장면 생성 후 다시 선택으로 (루프!)
    workflow.add_edge("generate", "get_choice")
    workflow.add_edge("ending", END)
    
    return workflow.compile()


def main():
    print("=== AI 스토리 어드벤처 게임 (LangGraph + LLM) ===")
    print("AI가 생성하는 스토리를 따라 모험을 떠나보세요!\n")
    
    app = create_story_game_graph()
    
    # 게임 실행
    initial_state = StoryGameState(max_turns=4)  # 4턴 진행
    result = app.invoke(initial_state)
    
    print(f"\n총 {result['turn_count']}턴 진행됨")
    
    # 그래프 시각화
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./04_ai_story_adventure.png", "wb") as f:
            f.write(mermaid_png)
        print("그래프가 04_ai_story_adventure.png로 저장되었습니다.")
    except Exception as e:
        print(f"그래프 출력 실패: {e}")


if __name__ == "__main__":
    main()

