from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json


# ① 학습 상태 정의
class TutorState(BaseModel):
    topic: str = Field(default="", description="학습 주제")
    explanation: str = Field(default="", description="AI의 설명")
    quiz_question: str = Field(default="", description="퀴즈 문제")
    quiz_answer: str = Field(default="", description="정답")
    quiz_choices: list[str] = Field(default_factory=list, description="선택지")
    user_answer: str = Field(default="", description="사용자 답변")
    feedback: str = Field(default="", description="피드백")
    score: int = Field(default=0, description="점수")
    quiz_count: int = Field(default=0, description="푼 퀴즈 수")
    max_quizzes: int = Field(default=3, description="최대 퀴즈 수")
    status: str = Field(default="explaining", description="상태: explaining, quizzing, reviewing, done")
    previous_questions: list[str] = Field(default_factory=list, description="이전에 낸 문제들")


# LLM 초기화
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


# ② 주제 설명 노드
def explain_topic(state: TutorState) -> Dict[str, Any]:
    """AI가 주제를 설명합니다."""
    topic = state.topic
    
    if state.quiz_count == 0:
        print(f"\n=== 📚 AI 학습 튜터 시작! ===")
        print(f"주제: {topic}\n")
    
    system_prompt = f"""당신은 친절한 선생님입니다.
'{topic}' 주제를 쉽고 명확하게 설명하세요.

3-4문장으로 핵심 개념을 설명하되, 예시를 포함하세요."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"{topic}에 대해 설명해주세요.")
    ]
    
    response = llm.invoke(messages)
    explanation = response.content
    
    print(f"📖 설명:\n{explanation}\n")
    
    return {
        "explanation": explanation,
        "status": "quizzing"
    }


# ③ 퀴즈 생성 노드
def generate_quiz(state: TutorState) -> Dict[str, Any]:
    """학습 내용에 대한 퀴즈를 생성합니다."""
    print("🧠 퀴즈를 생성 중...\n")
    
    # 이전 문제들이 있으면 표시
    previous_questions_text = ""
    if state.previous_questions:
        previous_questions_text = "\n\n이미 낸 문제들 (중복 금지):\n" + "\n".join(
            f"- {q}" for q in state.previous_questions
        )
    
    system_prompt = f"""당신은 퀴즈 출제자입니다.
다음 설명을 바탕으로 4지선다 퀴즈를 만드세요:

{state.explanation}
{previous_questions_text}

다음 JSON 형식으로 응답하세요:
{{
  "question": "질문 (명확하고 구체적으로)",
  "choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
  "answer": "정답 선택지의 정확한 텍스트"
}}

중요: 
- 이전에 낸 문제와 완전히 다른 각도의 문제를 만드세요
- 같은 개념의 다른 측면을 다루세요
- 난이도는 중간 정도로, 이해도를 확인할 수 있는 문제를 만드세요"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="퀴즈를 만들어주세요.")
    ]
    
    response = llm.invoke(messages)
    result = json.loads(response.content)
    
    question = result["question"]
    choices = result["choices"]
    answer = result["answer"]
    
    print(f"❓ 퀴즈 #{state.quiz_count + 1}")
    print(f"{question}\n")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    
    # 이전 문제 목록에 추가
    updated_previous = state.previous_questions.copy()
    updated_previous.append(question)
    
    return {
        "quiz_question": question,
        "quiz_choices": choices,
        "quiz_answer": answer,
        "previous_questions": updated_previous,
        "status": "reviewing"
    }


# ④ 답변 입력 및 평가 노드
def review_answer(state: TutorState) -> Dict[str, Any]:
    """사용자 답변을 받고 AI가 평가합니다."""
    print()
    
    # 사용자 답변 입력
    while True:
        try:
            choice_num = int(input("답을 선택하세요 (번호 입력): "))
            if 1 <= choice_num <= len(state.quiz_choices):
                user_answer = state.quiz_choices[choice_num - 1]
                break
            else:
                print(f"1-{len(state.quiz_choices)} 사이의 숫자를 입력하세요.")
        except ValueError:
            print("숫자를 입력하세요.")
    
    # 정답 확인
    is_correct = user_answer == state.quiz_answer
    
    if is_correct:
        print("✅ 정답입니다!")
        new_score = state.score + 1
    else:
        print(f"❌ 틀렸습니다. 정답은: {state.quiz_answer}")
        new_score = state.score
    
    # AI 피드백 생성
    print("💬 AI 피드백 생성 중...\n")
    
    system_prompt = f"""당신은 친절한 선생님입니다.
학생의 답변에 대해 피드백을 주세요.

질문: {state.quiz_question}
정답: {state.quiz_answer}
학생 답변: {user_answer}
결과: {'정답' if is_correct else '오답'}

{'칭찬하며' if is_correct else '격려하며'} 2-3문장으로 피드백을 작성하세요.
{'추가로 관련 지식을 알려주세요.' if is_correct else '왜 틀렸는지, 올바른 개념을 설명해주세요.'}"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="피드백을 주세요.")
    ]
    
    response = llm.invoke(messages)
    feedback = response.content
    
    print(f"📝 {feedback}\n")
    
    return {
        "user_answer": user_answer,
        "feedback": feedback,
        "score": new_score,
        "quiz_count": state.quiz_count + 1,
        "status": "quizzing"
    }


# ⑤ 학습 완료 노드
def finish_learning(state: TutorState) -> Dict[str, Any]:
    """학습을 마무리하고 최종 평가를 제공합니다."""
    print("\n=== 🎓 학습 완료! ===\n")
    
    score = state.score
    total = state.quiz_count
    percentage = (score / total * 100) if total > 0 else 0
    
    print(f"최종 점수: {score}/{total} ({percentage:.0f}%)")
    
    # AI 총평 생성
    system_prompt = f"""당신은 선생님입니다.
학생의 학습 결과에 대한 총평을 작성하세요.

주제: {state.topic}
점수: {score}/{total}

격려와 함께 2-3문장으로 총평을 작성하세요."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="총평을 작성해주세요.")
    ]
    
    response = llm.invoke(messages)
    summary = response.content
    
    print(f"📢 선생님 총평:\n{summary}\n")
    
    return {"status": "done"}


# ⑥ 라우팅 함수
def route_learning(state: TutorState) -> Literal["continue", "finish"]:
    """학습 진행 상태를 확인하고 다음 단계를 결정합니다."""
    if state.quiz_count >= state.max_quizzes:
        return "finish"
    return "continue"


# ⑦ 그래프 생성
def create_tutor_graph():
    """AI 학습 튜터 그래프를 생성합니다."""
    workflow = StateGraph(TutorState)
    
    # 노드 추가
    workflow.add_node("explain", explain_topic)
    workflow.add_node("quiz", generate_quiz)
    workflow.add_node("review", review_answer)
    workflow.add_node("finish", finish_learning)
    
    # 엣지 연결
    workflow.add_edge(START, "explain")
    workflow.add_edge("explain", "quiz")
    workflow.add_edge("quiz", "review")
    
    # 조건부 엣지 - 계속하거나 종료
    workflow.add_conditional_edges(
        "review",
        route_learning,
        {
            "continue": "quiz",  # 다시 퀴즈로 (루프!)
            "finish": "finish"
        }
    )
    
    workflow.add_edge("finish", END)
    
    return workflow.compile()


def main():
    print("=== AI 학습 튜터 (LangGraph + LLM) ===")
    print("AI 선생님과 함께 학습해봅시다!\n")
    
    # 주제 입력
    topic = input("학습하고 싶은 주제를 입력하세요 (예: 파이썬 리스트 컴프리헨션): ")
    
    if not topic:
        topic = "파이썬 리스트 컴프리헨션"
        print(f"기본 주제 선택: {topic}")
    
    app = create_tutor_graph()
    
    # 학습 시작
    initial_state = TutorState(topic=topic, max_quizzes=3)
    result = app.invoke(initial_state)
    
    # 그래프 시각화
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./04_ai_learning_tutor.png", "wb") as f:
            f.write(mermaid_png)
        print("그래프가 04_ai_learning_tutor.png로 저장되었습니다.")
    except Exception as e:
        print(f"그래프 출력 실패: {e}")


if __name__ == "__main__":
    main()

