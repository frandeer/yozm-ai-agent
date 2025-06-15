from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import random


# ① 워크플로우 단계 정의
class WorkflowStep:
    EMOTION_ANALYSIS = "EMOTION_ANALYSIS"
    POSITIVE_RESPONSE = "POSITIVE_RESPONSE"
    NEGATIVE_RESPONSE = "NEGATIVE_RESPONSE"
    NEUTRAL_RESPONSE = "NEUTRAL_RESPONSE"


# ② 그래프 상태 정의
class EmotionBotState(BaseModel):
    user_message: str = Field(default="", description="사용자 입력 메시지")
    emotion: str = Field(default="", description="분석된 감정 (positive/negative/neutral)")
    confidence: float = Field(default=0.0, description="감정 분석 신뢰도 (0.0-1.0)")
    response: str = Field(default="", description="최종 응답 메시지")


# ③ 감정 분석 키워드 사전
EMOTION_KEYWORDS = {
    "positive": [
        "기쁘", "행복", "좋", "훌륭", "멋지", "최고", "완벽", "사랑", "감사", "축하",
        "성공", "즐거", "신나", "흥미", "만족", "기대", "희망", "웃", "반가", "놀라운"
    ],
    "negative": [
        "슬프", "우울", "힘들", "괴로", "아프", "화나", "짜증", "스트레스", "절망", "실망",
        "피곤", "지쳐", "무서", "걱정", "불안", "미안", "죄송", "후회", "싫", "나쁘"
    ]
}


# ④ 감정 분석 노드
def analyze_emotion(state: EmotionBotState) -> Dict[str, Any]:
    message = state.user_message
    print(f"[analyze_emotion] 분석할 메시지: '{message}'")
    
    positive_count = 0
    negative_count = 0
    
    # 메시지를 소문자로 변환하여 키워드 매칭
    message_lower = message.lower()
    
    # 긍정적 키워드 카운트
    for keyword in EMOTION_KEYWORDS["positive"]:
        if keyword in message_lower:
            positive_count += 1
    
    # 부정적 키워드 카운트
    for keyword in EMOTION_KEYWORDS["negative"]:
        if keyword in message_lower:
            negative_count += 1
    
    # 감정 분류 및 신뢰도 계산
    total_keywords = positive_count + negative_count
    
    if total_keywords == 0:
        emotion = "neutral"
        confidence = 0.5
    elif positive_count > negative_count:
        emotion = "positive"
        confidence = min(0.6 + (positive_count * 0.2), 1.0)
    elif negative_count > positive_count:
        emotion = "negative"  
        confidence = min(0.6 + (negative_count * 0.2), 1.0)
    else:
        emotion = "neutral"
        confidence = 0.5
    
    print(f"[analyze_emotion] 감정: {emotion}, 신뢰도: {confidence:.2f}")
    
    return {
        "emotion": emotion,
        "confidence": confidence
    }


# ⑤ 긍정적 응답 생성 노드
def generate_positive_response(state: EmotionBotState) -> Dict[str, Any]:
    positive_responses = [
        "와! 정말 좋은 소식이네요! 🎉 더 많은 좋은 일들이 생기길 바라요!",
        "기분이 좋으시군요! 😊 그 긍정적인 에너지가 전해져요!",
        "멋지네요! ✨ 이런 기쁜 순간들이 계속 이어지길 응원합니다!",
        "정말 훌륭하네요! 🌟 행복한 마음이 느껴져요!",
        "좋은 기운이 가득하시네요! 🌈 저도 덩달아 기분이 좋아져요!"
    ]
    
    response = random.choice(positive_responses)
    print(f"[generate_positive_response] 긍정적 응답 생성: {response}")
    
    return {"response": response}


# ⑥ 부정적 응답 생성 노드  
def generate_negative_response(state: EmotionBotState) -> Dict[str, Any]:
    negative_responses = [
        "힘든 시간을 보내고 계시는군요. 😔 괜찮아요, 이런 때도 있어요. 제가 곁에 있어드릴게요.",
        "마음이 많이 아프시겠어요. 💙 천천히 하나씩 해결해나가시면 돼요.",
        "지금은 어렵겠지만, 분명 더 좋은 날이 올 거예요. 🌅 조금만 더 힘내세요!",
        "혼자가 아니에요. 😊 언제든 이야기하고 싶으시면 말씀해주세요.",
        "어려운 상황이지만 꼭 극복하실 거예요. 💪 작은 변화부터 시작해보는 건 어떨까요?"
    ]
    
    response = random.choice(negative_responses)
    print(f"[generate_negative_response] 위로 응답 생성: {response}")
    
    return {"response": response}


# ⑦ 중립적 응답 생성 노드
def generate_neutral_response(state: EmotionBotState) -> Dict[str, Any]:
    neutral_responses = [
        "말씀해주셔서 감사해요! 😌 더 자세히 이야기해주시면 더 도움을 드릴 수 있을 것 같아요.",
        "네, 이해했어요. 🤔 다른 궁금한 점이나 도움이 필요한 일이 있으시면 언제든 말씀해주세요!",
        "그렇군요! 📝 더 구체적으로 어떤 부분에 대해 이야기하고 싶으신가요?",
        "흥미로운 주제네요! 💭 관련해서 더 알고 싶은 내용이 있으시면 말씀해주세요.",
        "네, 들었어요! 🎧 어떤 방향으로 대화를 이어가고 싶으신지 알려주세요."
    ]
    
    response = random.choice(neutral_responses)
    print(f"[generate_neutral_response] 중립적 응답 생성: {response}")
    
    return {"response": response}


# ⑧ 조건부 라우팅 함수
def route_by_emotion(state: EmotionBotState) -> Literal["positive_response", "negative_response", "neutral_response"]:
    emotion = state.emotion
    confidence = state.confidence
    
    print(f"[route_by_emotion] 라우팅 결정: 감정={emotion}, 신뢰도={confidence:.2f}")
    
    # 신뢰도가 낮으면 중립으로 라우팅
    if confidence < 0.6:
        print(f"[route_by_emotion] 신뢰도가 낮아 중립 경로로 라우팅")
        return "neutral_response"
    
    # 감정별 라우팅
    if emotion == "positive":
        return "positive_response"
    elif emotion == "negative":
        return "negative_response"
    else:
        return "neutral_response"


# ⑨ 그래프 생성
def create_emotion_bot_graph():
    workflow = StateGraph(EmotionBotState)
    
    # 노드 추가
    workflow.add_node(WorkflowStep.EMOTION_ANALYSIS, analyze_emotion)
    workflow.add_node(WorkflowStep.POSITIVE_RESPONSE, generate_positive_response)
    workflow.add_node(WorkflowStep.NEGATIVE_RESPONSE, generate_negative_response)
    workflow.add_node(WorkflowStep.NEUTRAL_RESPONSE, generate_neutral_response)
    
    # 시작점 설정
    workflow.add_edge(START, WorkflowStep.EMOTION_ANALYSIS)
    
    # 조건부 엣지 추가 (핵심 기능!)
    workflow.add_conditional_edges(
        WorkflowStep.EMOTION_ANALYSIS,  # 출발 노드
        route_by_emotion,               # 라우팅 함수
        {
            "positive_response": WorkflowStep.POSITIVE_RESPONSE,
            "negative_response": WorkflowStep.NEGATIVE_RESPONSE,
            "neutral_response": WorkflowStep.NEUTRAL_RESPONSE
        }
    )
    
    # 모든 응답 노드에서 종료점으로 연결
    workflow.add_edge(WorkflowStep.POSITIVE_RESPONSE, END)
    workflow.add_edge(WorkflowStep.NEGATIVE_RESPONSE, END)
    workflow.add_edge(WorkflowStep.NEUTRAL_RESPONSE, END)
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


# ⑩ 테스트 함수
def test_emotion_bot():
    print("=== 감정 분석 챗봇 테스트 ===\n")
    
    app = create_emotion_bot_graph()
    
    # 테스트 케이스들
    test_cases = [
        "오늘 정말 기분이 좋아요! 최고의 하루예요!",
        "너무 슬프고 힘들어요... 우울해서 죽겠어요.",
        "날씨가 어떤가요? 내일 비가 올까요?",
        "와! 드디어 승진했어요! 너무 행복합니다!",
        "시험에 떨어져서 정말 실망스럽고 화가나요.",
        "안녕하세요. 처음 뵙겠습니다."
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n--- 테스트 케이스 {i} ---")
        print(f"사용자 입력: '{message}'")
        
        initial_state = EmotionBotState(user_message=message)
        
        # 그래프 실행
        final_state = app.invoke(initial_state)
        
        print(f"감정 분석: {final_state['emotion']} (신뢰도: {final_state['confidence']:.2f})")
        print(f"챗봇 응답: {final_state['response']}")
        print("-" * 50)


def main():
    print("=== LangGraph 조건부 라우팅 예제 ===\n")
    
    # 챗봇 테스트
    test_emotion_bot()
    
    # 그래프 시각화
    print("\n=== 워크플로우 시각화 ===")
    app = create_emotion_bot_graph()
    
    # ASCII 그래프 출력
    ascii_graph = app.get_graph().draw_ascii()
    print("\n[ASCII 그래프]")
    print(ascii_graph)
    
    # Mermaid PNG 생성
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./02_conditional_routing.png", "wb") as f:
            f.write(mermaid_png)
        print("\n[그래프 이미지] 02_conditional_routing.png 파일이 생성되었습니다!")
    except Exception as e:
        print(f"\n[그래프 이미지] 생성 실패: {e}")


if __name__ == "__main__":
    main()
