from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import time
import random


# ① 워크플로우 단계 정의
class WorkflowStep:
    RESEARCHER = "RESEARCHER"
    WRITER = "WRITER"
    EDITOR = "EDITOR"


# ② 에이전트 역할 정의
class AgentRole(BaseModel):
    name: str
    description: str
    speciality: str
    personality: str


# ③ 그래프 상태 정의
class BlogCreationState(BaseModel):
    topic: str = Field(default="", description="블로그 주제")
    user_requirements: str = Field(default="", description="사용자 요구사항")
    
    # 연구원 결과
    research_data: Dict[str, Any] = Field(default_factory=dict, description="연구 데이터")
    key_points: List[str] = Field(default_factory=list, description="핵심 포인트")
    
    # 작가 결과
    draft_content: str = Field(default="", description="초안 내용")
    structure: Dict[str, str] = Field(default_factory=dict, description="글 구조")
    
    # 편집자 결과
    editor_feedback: str = Field(default="", description="편집자 피드백")
    final_blog_post: str = Field(default="", description="최종 블로그 포스트")
    
    # 협업 로그
    collaboration_log: List[Dict[str, str]] = Field(default_factory=list, description="협업 과정 로그")
    current_agent: str = Field(default="", description="현재 작업 중인 에이전트")


# ④ 에이전트 정의
AGENTS = {
    "researcher": AgentRole(
        name="Dr. Tech",
        description="기술 연구 전문가",
        speciality="기술 분석, 트렌드 조사, 데이터 수집",
        personality="체계적이고 꼼꼼한 분석가"
    ),
    "writer": AgentRole(
        name="Alex Writer",
        description="기술 블로거",
        speciality="기술 콘텐츠 작성, 독자 친화적 설명",
        personality="창의적이고 소통을 중시하는 작가"
    ),
    "editor": AgentRole(
        name="Maya Editor",
        description="콘텐츠 편집자",
        speciality="문법 검토, 구조 개선, 품질 관리",
        personality="완벽주의적이고 디테일에 집중하는 편집자"
    )
}


# ⑤ 연구원 에이전트
def researcher_agent(state: BlogCreationState) -> Dict[str, Any]:
    topic = state.topic
    requirements = state.user_requirements
    
    print(f"\n[👨‍🔬 연구원 - Dr. Tech] 주제 '{topic}' 연구 시작...")
    print(f"[👨‍🔬] 요구사항: {requirements}")
    
    # 연구 시뮬레이션
    time.sleep(random.uniform(1.0, 2.0))
    
    # 주제별 연구 데이터 (실제로는 AI가 생성하거나 API 호출)
    research_templates = {
        "python": {
            "technology": "Python",
            "version": "3.12",
            "key_features": ["타입 힌트 개선", "성능 최적화", "새로운 구문"],
            "use_cases": ["웹 개발", "데이터 사이언스", "AI/ML", "자동화"],
            "pros": ["간단한 문법", "풍부한 라이브러리", "활발한 커뮤니티"],
            "cons": ["상대적으로 느린 실행 속도", "GIL 제한"],
            "learning_curve": "초급자 친화적",
            "market_trend": "지속적 성장, AI 분야에서 급성장"
        },
        "react": {
            "technology": "React",
            "version": "18.2",
            "key_features": ["컴포넌트 기반", "Virtual DOM", "Hooks", "Concurrent Features"],
            "use_cases": ["SPA 개발", "모바일 앱", "데스크톱 앱"],
            "pros": ["재사용 가능한 컴포넌트", "강력한 생태계", "Meta 지원"],
            "cons": ["높은 학습 곡선", "빠른 변화"],
            "learning_curve": "중급 수준 필요",
            "market_trend": "프론트엔드 시장 점유율 1위 유지"
        },
        "ai": {
            "technology": "인공지능",
            "version": "2024",
            "key_features": ["생성형 AI", "멀티모달", "에이전트 시스템"],
            "use_cases": ["자동화", "콘텐츠 생성", "분석", "고객 서비스"],
            "pros": ["생산성 향상", "새로운 비즈니스 기회", "창의적 활용"],
            "cons": ["윤리적 문제", "일자리 대체 우려", "높은 비용"],
            "learning_curve": "분야별 상이",
            "market_trend": "폭발적 성장, 모든 산업에 영향"
        }
    }
    
    # 주제 키워드 매칭
    topic_lower = topic.lower()
    research_data = None
    
    for key, data in research_templates.items():
        if key in topic_lower:
            research_data = data
            break
    
    # 기본 템플릿 (매칭되지 않는 경우)
    if not research_data:
        research_data = {
            "technology": topic,
            "version": "최신",
            "key_features": ["혁신적 접근", "사용자 중심", "확장 가능"],
            "use_cases": ["다양한 프로젝트", "비즈니스 솔루션"],
            "pros": ["효율성", "사용 편의성", "커뮤니티 지원"],
            "cons": ["학습 시간 필요", "초기 설정 복잡성"],
            "learning_curve": "중급",
            "market_trend": "성장하는 분야"
        }
    
    # 핵심 포인트 추출
    key_points = [
        f"{research_data['technology']}의 주요 특징과= {', '.join(research_data['key_features'][:3])}",
        f"주요 사용 사례: {', '.join(research_data['use_cases'][:3])}",
        f"장점: {', '.join(research_data['pros'][:2])}",
        f"시장 동향: {research_data['market_trend']}"
    ]
    
    # 연구 완료 로그
    log_entry = {
        "agent": "연구원 (Dr. Tech)",
        "action": "주제 연구 완료",
        "summary": f"{len(key_points)}개 핵심 포인트 도출",
        "timestamp": time.strftime("%H:%M:%S")
    }
    
    print(f"[👨‍🔬] ✅ 연구 완료! {len(key_points)}개 핵심 포인트 도출")
    print(f"[👨‍🔬] 📊 핵심 발견사항:")
    for i, point in enumerate(key_points, 1):
        print(f"      {i}. {point}")
    
    return {
        "research_data": research_data,
        "key_points": key_points,
        "collaboration_log": [log_entry],
        "current_agent": "researcher"
    }


# ⑥ 작가 에이전트
def writer_agent(state: BlogCreationState) -> Dict[str, Any]:
    topic = state.topic
    research_data = state.research_data
    key_points = state.key_points
    
    print(f"\n[✍️ 작가 - Alex Writer] '{topic}' 블로그 포스트 작성 시작...")
    print(f"[✍️] 연구 자료 기반으로 독자 친화적인 글 작성 중...")
    
    # 작성 시뮬레이션
    time.sleep(random.uniform(1.5, 2.5))
    
    # 글 구조 설계
    structure = {
        "introduction": "독자의 관심을 끄는 도입부",
        "main_content": "핵심 내용과 예시",
        "code_examples": "실용적인 코드 예제",
        "conclusion": "정리 및 다음 단계 제안"
    }
    
    # 실제 블로그 포스트 초안 작성
    technology = research_data.get("technology", topic)
    
    draft_content = f"""# {technology}: 개발자가 알아야 할 모든 것

## 🚀 들어가며

안녕하세요, 개발자 여러분! 오늘은 현재 개발 생태계에서 주목받고 있는 **{technology}**에 대해 깊이 있게 알아보겠습니다.

{research_data.get('market_trend', '지속적으로 성장하는 분야')}라는 점에서, 지금이 바로 {technology}를 배워야 할 최적의 시기입니다.

## 💡 {technology}란 무엇인가?

{technology}는 {', '.join(research_data.get('key_features', [])[:3])}을 핵심 특징으로 하는 기술입니다.

### 주요 특징
{chr(10).join([f"- **{feature}**: 강력한 기능을 제공합니다" for feature in research_data.get('key_features', [])[:3]])}

## 🎯 실제 사용 사례

{technology}는 다음과 같은 분야에서 활용되고 있습니다:

{chr(10).join([f"### {i+1}. {use_case}" for i, use_case in enumerate(research_data.get('use_cases', [])[:3])])}
각 분야에서 {technology}의 강력함을 확인할 수 있습니다.

## ⚡ 장점과 한계

### 👍 주요 장점
{chr(10).join([f"- {pro}" for pro in research_data.get('pros', [])[:3]])}

### 🤔 고려사항
{chr(10).join([f"- {con}" for con in research_data.get('cons', [])[:2]])}

## 🏁 마무리

{technology}는 {research_data.get('learning_curve', '적절한 학습 곡선')}을 가지고 있어, 체계적으로 접근한다면 충분히 마스터할 수 있습니다.

다음 포스트에서는 {technology}의 실전 활용법과 고급 기법들을 다뤄보겠습니다. 

**여러분도 {technology}를 활용한 프로젝트 경험이 있다면 댓글로 공유해주세요!** 📝

---
*이 포스트가 도움이 되셨다면 좋아요와 공유 부탁드립니다! 🙏*
"""

    # 작가 완료 로그
    log_entry = {
        "agent": "작가 (Alex Writer)",
        "action": "초안 작성 완료", 
        "summary": f"{len(draft_content)} 문자 초안 완성",
        "timestamp": time.strftime("%H:%M:%S")
    }
    
    print(f"[✍️] ✅ 초안 작성 완료! ({len(draft_content):,} 문자)")
    print(f"[✍️] 📝 구조: {' → '.join(structure.values())}")
    
    # 기존 로그에 추가
    updated_log = state.collaboration_log + [log_entry]
    
    return {
        "draft_content": draft_content,
        "structure": structure,
        "collaboration_log": updated_log,
        "current_agent": "writer"
    }


# ⑦ 편집자 에이전트
def editor_agent(state: BlogCreationState) -> Dict[str, Any]:
    topic = state.topic
    draft_content = state.draft_content
    research_data = state.research_data
    
    print(f"\n[📝 편집자 - Maya Editor] '{topic}' 블로그 포스트 최종 검토 시작...")
    print(f"[📝] 문법, 구조, 일관성 검토 중...")
    
    # 편집 시뮬레이션
    time.sleep(random.uniform(1.0, 2.0))
    
    # 편집자 피드백 생성
    feedback_points = [
        "✅ 전체적인 구조가 논리적이고 읽기 쉽습니다",
        "✅ 기술적 내용과 독자 친화적 설명의 균형이 좋습니다",
        "✅ 실제 사용 사례가 구체적으로 제시되어 실용적입니다",
        "🔧 일부 기술 용어에 대한 간단한 설명을 추가했습니다",
        "🔧 가독성을 위해 일부 문단을 분리했습니다"
    ]
    
    editor_feedback = f"""## 📋 편집자 검토 의견

### 전체 평가: ⭐⭐⭐⭐⭐ (우수)

{chr(10).join(feedback_points)}

### 개선사항 적용:
- 독자 참여를 유도하는 CTA 문구 강화
- 기술적 용어 설명 보완
- 시각적 구분을 위한 이모지 활용 최적화
"""

    # 최종 블로그 포스트 (편집 완료)
    technology = research_data.get("technology", topic)
    
    final_blog_post = f"""# {technology}: 개발자가 알아야 할 모든 것 🚀

## 🌟 들어가며

안녕하세요, 개발자 여러분! 오늘은 현재 개발 생태계에서 **뜨거운 주목**을 받고 있는 **{technology}**에 대해 깊이 있게 알아보겠습니다.

> 📈 **시장 동향**: {research_data.get('market_trend', '지속적으로 성장하는 분야')}

지금이 바로 {technology}를 배워야 할 **골든 타임**입니다! ⏰

## 💡 {technology}란 무엇인가?

{technology}는 다음과 같은 **핵심 특징**을 가진 혁신적인 기술입니다:

### ⭐ 주요 특징
{chr(10).join([f"- **{feature}**: 개발 효율성을 크게 향상시킵니다" for feature in research_data.get('key_features', [])[:3]])}

## 🎯 실제 활용 사례

{technology}가 **실무에서 어떻게 활용**되는지 살펴보겠습니다:

{chr(10).join([f"### {i+1}. {use_case}" for i, use_case in enumerate(research_data.get('use_cases', [])[:3])])}

각 분야에서 {technology}의 **강력한 성능**을 확인할 수 있습니다! 💪

## ⚖️ 장점 vs 한계점

### 👍 **주요 장점**
{chr(10).join([f"- ✅ **{pro}**: 개발자 경험을 향상시킵니다" for pro in research_data.get('pros', [])[:3]])}

### 🤔 **고려할 점**
{chr(10).join([f"- ⚠️ **{con}**: 도입 시 고려해야 할 요소입니다" for con in research_data.get('cons', [])[:2]])}

## 📚 학습 가이드

**{research_data.get('learning_curve', '적절한 학습 곡선')}** 수준의 {technology}는 다음 단계로 학습하는 것을 권장합니다:

1. **기초 개념 이해** (1-2주)
2. **실습 프로젝트** (2-3주)  
3. **고급 기능 탐구** (3-4주)
4. **실무 프로젝트 적용** (계속)

## 🏆 마무리

{technology}는 현재 개발 트렌드에서 **빼놓을 수 없는 핵심 기술**입니다.

**체계적인 학습**과 **꾸준한 실습**을 통해 여러분도 {technology} 전문가가 될 수 있습니다! 🎯

---

### 💬 **여러분의 의견을 들려주세요!**

- {technology} 사용 경험이 있으시나요?
- 어떤 프로젝트에 적용해보고 싶으신가요?
- 궁금한 점이 있다면 언제든 댓글로 남겨주세요! 

**다음 포스트**에서는 {technology}의 **실전 활용법**과 **고급 기법**들을 상세히 다뤄보겠습니다. 

---

> 🔔 **알림**: 이런 유용한 개발 콘텐츠를 놓치고 싶지 않다면 **구독**과 **좋아요** 부탁드립니다!
> 
> 📢 **공유하기**: 동료 개발자들에게도 이 정보를 공유해주세요! 

**#개발 #{technology} #프로그래밍 #기술블로그**
"""

    # 편집자 완료 로그
    log_entry = {
        "agent": "편집자 (Maya Editor)",
        "action": "최종 편집 완료",
        "summary": f"검토 완료, {len(feedback_points)}개 개선사항 적용",
        "timestamp": time.strftime("%H:%M:%S")
    }
    
    print(f"[📝] ✅ 최종 편집 완료!")
    print(f"[📝] 📊 품질 점수: ⭐⭐⭐⭐⭐ (우수)")
    print(f"[📝] 🔧 {len(feedback_points)}개 개선사항 적용")
    
    # 기존 로그에 추가
    updated_log = state.collaboration_log + [log_entry]
    
    return {
        "editor_feedback": editor_feedback,
        "final_blog_post": final_blog_post,
        "collaboration_log": updated_log,
        "current_agent": "editor"
    }


# ⑧ 그래프 생성 (멀티 에이전트 협업)
def create_multi_agent_graph():
    workflow = StateGraph(BlogCreationState)
    
    # 에이전트 노드 추가
    workflow.add_node(WorkflowStep.RESEARCHER, researcher_agent)
    workflow.add_node(WorkflowStep.WRITER, writer_agent)
    workflow.add_node(WorkflowStep.EDITOR, editor_agent)
    
    # 순차적 협업 워크플로우 구성
    workflow.add_edge(START, WorkflowStep.RESEARCHER)  # 연구원 시작
    workflow.add_edge(WorkflowStep.RESEARCHER, WorkflowStep.WRITER)  # 연구 → 작성
    workflow.add_edge(WorkflowStep.WRITER, WorkflowStep.EDITOR)  # 작성 → 편집
    workflow.add_edge(WorkflowStep.EDITOR, END)  # 편집 → 완료
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


# ⑨ 협업 결과 요약
def print_collaboration_summary(final_state):
    print("\n" + "="*80)
    print("📊 **멀티 에이전트 협업 최종 리포트**")
    print("="*80)
    
    # 기본 정보
    print(f"\n📋 **프로젝트 정보**")
    print(f"   🎯 주제: {final_state['topic']}")
    print(f"   📝 요구사항: {final_state['user_requirements']}")
    
    # 협업 과정
    print(f"\n🤝 **협업 과정** ({len(final_state['collaboration_log'])}단계)")
    for i, log in enumerate(final_state['collaboration_log'], 1):
        print(f"   {i}. [{log['timestamp']}] {log['agent']}: {log['action']}")
        print(f"      └─ {log['summary']}")
    
    # 최종 결과물 통계
    final_post = final_state['final_blog_post']
    print(f"\n📊 **최종 결과물 통계**")
    print(f"   📝 총 글자 수: {len(final_post):,} 문자")
    print(f"   📄 예상 읽기 시간: {len(final_post) // 400 + 1}분")
    print(f"   🔍 핵심 포인트: {len(final_state['key_points'])}개")
    print(f"   📑 글 구조: {len(final_state['structure'])}개 섹션")
    
    # 품질 평가
    print(f"\n⭐ **품질 평가**")
    print(f"   🔬 연구 품질: ⭐⭐⭐⭐⭐ (전문적)")
    print(f"   ✍️ 작성 품질: ⭐⭐⭐⭐⭐ (독자 친화적)")
    print(f"   📝 편집 품질: ⭐⭐⭐⭐⭐ (완성도 높음)")
    
    print("\n" + "="*80)


# ⑩ 테스트 함수
def test_multi_agent_collaboration():
    print("=== 멀티 에이전트 협업 테스트 ===\n")
    
    app = create_multi_agent_graph()
    
    # 테스트 시나리오들
    test_scenarios = [
        {
            "topic": "Python 3.12 신기능",
            "requirements": "초보자도 이해할 수 있게, 실용적인 예제 포함"
        },
        {
            "topic": "React 18 Concurrent Features",
            "requirements": "중급 개발자 대상, 성능 최적화 중심"
        },
        {
            "topic": "AI 에이전트 개발",
            "requirements": "실무 적용 가능한 내용, 코드 예제 필수"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'🔥 시나리오 ' + str(i):=^60}")
        print(f"주제: {scenario['topic']}")
        print(f"요구사항: {scenario['requirements']}")
        print("-" * 60)
        
        # 초기 상태  
        initial_state = BlogCreationState(
            topic=scenario["topic"],
            user_requirements=scenario["requirements"]
        )
        
        # 멀티 에이전트 협업 실행
        final_state = app.invoke(initial_state)
        
        # 협업 결과 요약
        print_collaboration_summary(final_state)
        
        # 최종 블로그 포스트 일부 미리보기
        print(f"\n📖 **최종 블로그 포스트 미리보기**")
        print("-" * 60)
        preview = final_state.final_blog_post[:500] + "..."
        print(preview)
        print("-" * 60)
        
        if i < len(test_scenarios):
            print(f"\n⏳ 다음 시나리오 준비 중...")
            time.sleep(1)


# ⑪ 상세 결과 출력
def demo_detailed_collaboration():
    print("\n=== 상세 협업 과정 시연 ===\n")
    
    app = create_multi_agent_graph()
    
    # 데모 시나리오
    demo_scenario = {
        "topic": "LangGraph 멀티 에이전트",
        "requirements": "실제 구현 예제와 함께, 개발자들이 바로 따라할 수 있는 실용적인 가이드"
    }
    
    print(f"🎬 **시연 시나리오**")
    print(f"   📌 주제: {demo_scenario['topic']}")
    print(f"   📋 요구사항: {demo_scenario['requirements']}")
    
    # 상세 협업 실행
    initial_state = BlogCreationState(
        topic=demo_scenario["topic"],
        user_requirements=demo_scenario["requirements"]
    )
    
    print(f"\n🚀 **멀티 에이전트 협업 시작!**")
    final_state = app.invoke(initial_state)
    
    # 각 에이전트별 상세 결과
    print(f"\n🔬 **연구원 결과 상세**")
    print(f"   📊 연구 데이터: {len(final_state.research_data)} 항목")
    for key, value in final_state.research_data.items():
        if isinstance(value, list):
            print(f"   - {key}: {len(value)}개 ({', '.join(value[:2])}...)")
        else:
            print(f"   - {key}: {str(value)[:50]}...")
    
    print(f"\n✍️ **작가 결과 상세**")
    print(f"   📝 초안 길이: {len(final_state.draft_content):,} 문자")
    print(f"   🏗️ 글 구조: {list(final_state.structure.keys())}")
    
    print(f"\n📝 **편집자 결과 상세**")
    print(f"   📋 피드백: {final_state.editor_feedback[:100]}...")
    print(f"   📄 최종 글: {len(final_state.final_blog_post):,} 문자")
    
    # 전체 요약
    print_collaboration_summary(final_state)
    
    return final_state


def main():
    print("=== LangGraph 멀티 에이전트 협업 예제 ===\n")
    
    # 에이전트 소개
    print("👥 **협업 에이전트 팀 소개**")
    for role, agent in AGENTS.items():
        print(f"   {agent.name} ({role}): {agent.description}")
        print(f"   └─ 전문분야: {agent.speciality}")
        print(f"   └─ 성격: {agent.personality}")
        print()
    
    # 기본 테스트
    test_multi_agent_collaboration()
    
    # 상세 시연
    demo_result = demo_detailed_collaboration()
    
    # 그래프 시각화
    print("\n=== 워크플로우 시각화 ===")
    app = create_multi_agent_graph()
    
    # ASCII 그래프 출력
    ascii_graph = app.get_graph().draw_ascii()
    print("\n[ASCII 그래프]")
    print(ascii_graph)
    
    # Mermaid PNG 생성
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./chapter4/langgraph/09_multi_agent_collaboration.png", "wb") as f:
            f.write(mermaid_png)
        print("\n[그래프 이미지] 09_multi_agent_collaboration.png 파일이 생성되었습니다!")
    except Exception as e:
        print(f"\n[그래프 이미지] 생성 실패: {e}")


if __name__ == "__main__":
    main()
