"""
🎯 실전 프로젝트: 스마트 회의록 자동화 시스템
=================================================

회사에서 바로 활용 가능한 Human-in-the-Loop 실전 예제

기능:
    1. 회의 내용 요약 생성 (AI) → 승인 (Human)
    2. 액션 아이템 추출 (AI) → 확인/수정 (Human)
    3. 담당자 자동 배정 제안 (AI) → 승인 (Human)
    4. 마감일 제안 (AI) → 조정 (Human)
    5. 최종 보고서 생성 및 이메일 전송 승인 (Human)

Human-in-the-Loop 지점:
    - 요약 내용 확인 (잘못된 이해 방지)
    - 액션 아이템 누락/추가 (중요한 항목 놓치지 않기)
    - 담당자 배정 승인 (민감한 인사 결정)
    - 마감일 조정 (현실성 검토)
    - 최종 전송 승인 (실수 방지)
"""

from typing import Dict, Any, Literal, List
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
from datetime import datetime, timedelta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 상태 정의
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class ActionItem(BaseModel):
    """액션 아이템"""
    title: str
    description: str
    assignee: str = ""
    deadline: str = ""
    priority: str = "medium"  # low, medium, high


class MeetingState(BaseModel):
    """회의록 시스템 상태"""
    # 입력
    meeting_transcript: str = Field(default="", description="회의 내용 (대화록)")
    team_members: List[str] = Field(default_factory=list, description="팀원 목록")
    
    # AI 생성 → Human 검토
    summary: str = Field(default="", description="AI가 생성한 회의 요약")
    summary_approved: bool = Field(default=False, description="요약 승인 여부")
    
    action_items: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="AI가 추출한 액션 아이템"
    )
    action_items_approved: bool = Field(default=False, description="액션 아이템 승인 여부")
    
    # 최종 결과
    final_report: str = Field(default="", description="최종 회의록 보고서")
    send_approved: bool = Field(default=False, description="전송 승인 여부")
    
    # 메타데이터
    current_step: str = Field(default="", description="현재 진행 단계")


# LLM 초기화
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 노드 1: 회의 요약 생성 (AI)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_summary(state: MeetingState) -> Dict[str, Any]:
    """AI가 회의 내용을 요약합니다."""
    print("\n" + "="*70)
    print("📝 [1단계] AI가 회의 내용을 요약합니다...")
    print("="*70)
    
    prompt = f"""다음 회의 내용을 간결하게 요약해주세요:

회의 내용:
{state.meeting_transcript}

요약 형식:
1. 회의 목적 (1-2문장)
2. 주요 논의 사항 (3-5개 불릿 포인트)
3. 결정 사항 (있는 경우)

명확하고 구체적으로 작성하세요."""
    
    messages = [
        SystemMessage(content="당신은 회의록 작성 전문가입니다."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    summary = response.content
    
    print(f"\n✅ 요약 생성 완료:")
    print("-" * 70)
    print(summary)
    print("-" * 70)
    
    return {
        "summary": summary,
        "current_step": "summary_generated"
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 노드 2: 요약 승인 받기 (Human) ⭐
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def approve_summary(state: MeetingState) -> Dict[str, Any]:
    """사람이 요약을 검토하고 승인합니다."""
    print("\n" + "🔔"*35)
    print("👤 [Human-in-the-Loop] 요약 검토가 필요합니다!")
    print("🔔"*70)
    
    print(f"\n📋 AI가 생성한 요약:\n")
    print(state.summary)
    print("\n" + "-"*70)
    
    while True:
        approval = input("\n✅ 이 요약을 승인하시겠습니까? (y: 승인, n: 거부, e: 수정): ").lower()
        
        if approval == 'y':
            print("✅ 요약이 승인되었습니다!")
            return {
                "summary_approved": True,
                "current_step": "summary_approved"
            }
        elif approval == 'e':
            print("\n✏️ 수정할 내용을 입력하세요:")
            edited_summary = input()
            print("✅ 요약이 수정되었습니다!")
            return {
                "summary": edited_summary,
                "summary_approved": True,
                "current_step": "summary_approved"
            }
        elif approval == 'n':
            print("❌ 요약이 거부되었습니다. 다시 생성합니다...")
            return {
                "summary_approved": False,
                "current_step": "summary_rejected"
            }
        else:
            print("⚠️ y, n, e 중 하나를 입력하세요.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 노드 3: 액션 아이템 추출 (AI)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def extract_action_items(state: MeetingState) -> Dict[str, Any]:
    """AI가 액션 아이템을 추출합니다."""
    print("\n" + "="*70)
    print("🎯 [2단계] AI가 액션 아이템을 추출합니다...")
    print("="*70)
    
    team_members_str = ", ".join(state.team_members)
    
    prompt = f"""다음 회의 내용에서 액션 아이템을 추출해주세요:

회의 내용:
{state.meeting_transcript}

팀원 목록: {team_members_str}

다음 JSON 형식으로 응답하세요 (오직 JSON만 반환하고 다른 텍스트는 포함하지 마세요):
{{
  "action_items": [
    {{
      "title": "액션 아이템 제목",
      "description": "상세 설명",
      "assignee": "담당자 이름 (팀원 중에서)",
      "deadline": "권장 마감일 (오늘부터 며칠 후, 예: '3일 후', '1주일 후')",
      "priority": "low/medium/high"
    }}
  ]
}}

실제로 실행해야 할 구체적인 작업만 추출하세요."""
    
    messages = [
        SystemMessage(content="당신은 회의록에서 액션 아이템을 추출하는 전문가입니다. 응답은 반드시 순수 JSON 형식만 반환하세요."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    try:
        # LLM 응답에서 JSON 추출 (마크다운 코드 블록 제거)
        content = response.content.strip()
        
        # ```json ... ``` 형식 제거
        if content.startswith("```"):
            # 첫 번째 줄 제거 (```json)
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
            # 마지막 ``` 제거
            content = content.replace("```", "").strip()
        
        # JSON 파싱
        result = json.loads(content)
        action_items = result.get("action_items", [])
        
        print(f"\n✅ {len(action_items)}개의 액션 아이템을 찾았습니다:")
        print("-" * 70)
        for i, item in enumerate(action_items, 1):
            print(f"\n{i}. {item['title']}")
            print(f"   담당자: {item['assignee']}")
            print(f"   마감일: {item['deadline']}")
            print(f"   우선순위: {item['priority']}")
        print("-" * 70)
        
        return {
            "action_items": action_items,
            "current_step": "action_items_extracted"
        }
    except Exception as e:
        print(f"⚠️ 액션 아이템 추출 실패: {e}")
        print(f"🔍 LLM 응답 내용:")
        print(f"{response.content[:500]}...")  # 디버깅용: 응답 일부 출력
        return {
            "action_items": [],
            "current_step": "action_items_extracted"
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 노드 4: 액션 아이템 확인 (Human) ⭐
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def review_action_items(state: MeetingState) -> Dict[str, Any]:
    """사람이 액션 아이템을 검토합니다."""
    print("\n" + "🔔"*35)
    print("👤 [Human-in-the-Loop] 액션 아이템 검토가 필요합니다!")
    print("🔔"*70)
    
    print(f"\n📋 AI가 추출한 액션 아이템 ({len(state.action_items)}개):\n")
    
    for i, item in enumerate(state.action_items, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   설명: {item['description']}")
        print(f"   담당자: {item['assignee']}")
        print(f"   마감일: {item['deadline']}")
        print(f"   우선순위: {item['priority']}")
    
    print("\n" + "-"*70)
    
    while True:
        choice = input("\n선택하세요 (y: 승인, a: 추가, d: 삭제, m: 수정): ").lower()
        
        if choice == 'y':
            print("✅ 모든 액션 아이템이 승인되었습니다!")
            return {
                "action_items_approved": True,
                "current_step": "action_items_approved"
            }
        
        elif choice == 'a':
            print("\n➕ 새 액션 아이템 추가:")
            title = input("제목: ")
            description = input("설명: ")
            assignee = input("담당자: ")
            deadline = input("마감일 (예: 3일 후): ")
            priority = input("우선순위 (low/medium/high): ")
            
            new_item = {
                "title": title,
                "description": description,
                "assignee": assignee,
                "deadline": deadline,
                "priority": priority
            }
            
            updated_items = state.action_items.copy()
            updated_items.append(new_item)
            
            print("✅ 액션 아이템이 추가되었습니다!")
            
            return {
                "action_items": updated_items,
                "current_step": "action_items_modified"
            }
        
        elif choice == 'd':
            idx = int(input("삭제할 항목 번호: ")) - 1
            updated_items = state.action_items.copy()
            if 0 <= idx < len(updated_items):
                removed = updated_items.pop(idx)
                print(f"✅ '{removed['title']}'이(가) 삭제되었습니다!")
                return {
                    "action_items": updated_items,
                    "current_step": "action_items_modified"
                }
        
        elif choice == 'm':
            idx = int(input("수정할 항목 번호: ")) - 1
            if 0 <= idx < len(state.action_items):
                print(f"\n현재 값: {state.action_items[idx]}")
                print("수정할 내용 입력 (Enter = 유지):")
                
                updated_items = state.action_items.copy()
                item = updated_items[idx].copy()
                
                title = input(f"제목 [{item['title']}]: ")
                if title: item['title'] = title
                
                assignee = input(f"담당자 [{item['assignee']}]: ")
                if assignee: item['assignee'] = assignee
                
                deadline = input(f"마감일 [{item['deadline']}]: ")
                if deadline: item['deadline'] = deadline
                
                priority = input(f"우선순위 [{item['priority']}]: ")
                if priority: item['priority'] = priority
                
                updated_items[idx] = item
                print("✅ 수정되었습니다!")
                
                return {
                    "action_items": updated_items,
                    "current_step": "action_items_modified"
                }
        else:
            print("⚠️ y, a, d, m 중 하나를 입력하세요.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 노드 5: 최종 보고서 생성 (AI)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_final_report(state: MeetingState) -> Dict[str, Any]:
    """AI가 최종 회의록 보고서를 생성합니다."""
    print("\n" + "="*70)
    print("📄 [3단계] AI가 최종 보고서를 생성합니다...")
    print("="*70)
    
    # 액션 아이템을 텍스트로 변환
    action_items_text = "\n".join([
        f"- {item['title']} (담당: {item['assignee']}, 마감: {item['deadline']}, 우선순위: {item['priority']})"
        for item in state.action_items
    ])
    
    prompt = f"""다음 정보를 바탕으로 최종 회의록 보고서를 작성해주세요:

회의 요약:
{state.summary}

액션 아이템:
{action_items_text}

보고서 형식:
===========================================
📋 회의록
===========================================
날짜: {datetime.now().strftime('%Y년 %m월 %d일')}

[회의 요약]
{{요약 내용}}

[액션 아이템] ({len(state.action_items)}개)
{{액션 아이템 목록 - 번호, 제목, 담당자, 마감일}}

[다음 단계]
{{간단한 다음 단계 안내}}
===========================================

전문적이고 명확하게 작성하세요."""
    
    messages = [
        SystemMessage(content="당신은 회의록 보고서 작성 전문가입니다."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    final_report = response.content
    
    print("\n✅ 최종 보고서 생성 완료!")
    
    return {
        "final_report": final_report,
        "current_step": "report_generated"
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 노드 6: 전송 승인 (Human) ⭐
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def approve_send(state: MeetingState) -> Dict[str, Any]:
    """사람이 최종 보고서 전송을 승인합니다."""
    print("\n" + "🔔"*35)
    print("👤 [Human-in-the-Loop] 최종 전송 승인이 필요합니다!")
    print("🔔"*70)
    
    print("\n📄 최종 보고서:")
    print("="*70)
    print(state.final_report)
    print("="*70)
    
    while True:
        approval = input("\n✅ 이 보고서를 팀원들에게 전송하시겠습니까? (y/n): ").lower()
        
        if approval == 'y':
            print("\n✅ 승인되었습니다!")
            print("📧 보고서를 팀원들에게 전송합니다...")
            print("✉️  이메일 전송 완료! (시뮬레이션)")
            return {
                "send_approved": True,
                "current_step": "completed"
            }
        elif approval == 'n':
            print("❌ 전송이 취소되었습니다.")
            return {
                "send_approved": False,
                "current_step": "send_cancelled"
            }
        else:
            print("⚠️ y 또는 n을 입력하세요.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 라우팅 함수들
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def route_after_summary_approval(state: MeetingState) -> Literal["approved", "regenerate"]:
    """요약 승인 여부에 따라 라우팅"""
    if state.summary_approved:
        return "approved"
    return "regenerate"


def route_after_action_review(state: MeetingState) -> Literal["approved", "modify_again"]:
    """액션 아이템 검토 후 라우팅"""
    if state.action_items_approved:
        return "approved"
    return "modify_again"


def route_after_send_approval(state: MeetingState) -> Literal["sent", "cancelled"]:
    """전송 승인 여부에 따라 라우팅"""
    if state.send_approved:
        return "sent"
    return "cancelled"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 그래프 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def create_meeting_assistant_graph():
    """회의록 자동화 시스템 그래프 생성"""
    workflow = StateGraph(MeetingState)
    
    # 노드 추가
    workflow.add_node("generate_summary", generate_summary)
    workflow.add_node("approve_summary", approve_summary)
    workflow.add_node("extract_actions", extract_action_items)
    workflow.add_node("review_actions", review_action_items)
    workflow.add_node("generate_report", generate_final_report)
    workflow.add_node("approve_send", approve_send)
    
    # 엣지 연결
    workflow.add_edge(START, "generate_summary")
    workflow.add_edge("generate_summary", "approve_summary")
    
    # 요약 승인 → 진행 or 재생성
    workflow.add_conditional_edges(
        "approve_summary",
        route_after_summary_approval,
        {
            "approved": "extract_actions",
            "regenerate": "generate_summary"
        }
    )
    
    workflow.add_edge("extract_actions", "review_actions")
    
    # 액션 아이템 검토 → 진행 or 다시 검토
    workflow.add_conditional_edges(
        "review_actions",
        route_after_action_review,
        {
            "approved": "generate_report",
            "modify_again": "review_actions"
        }
    )
    
    workflow.add_edge("generate_report", "approve_send")
    
    # 전송 승인 → 완료 or 취소
    workflow.add_conditional_edges(
        "approve_send",
        route_after_send_approval,
        {
            "sent": END,
            "cancelled": END
        }
    )
    
    return workflow.compile()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "🎯 스마트 회의록 자동화 시스템" + " "*16 + "║")
    print("║" + " "*20 + "Human-in-the-Loop 실전 프로젝트" + " "*16 + "║")
    print("╚" + "="*68 + "╝")
    
    print("""
🎬 시나리오:
    회사에서 주간 팀 회의를 마쳤습니다.
    AI가 회의록을 작성하고, 당신은 중요한 결정마다 검토합니다.
    
✨ Human-in-the-Loop 지점 (총 3곳):
    1️⃣ 요약 검토 및 승인
    2️⃣ 액션 아이템 확인/수정
    3️⃣ 최종 전송 승인
""")
    
    # 샘플 회의 내용
    sample_transcript = """
    [팀장 김철수]: 안녕하세요, 이번 주 스프린트 회의를 시작하겠습니다.
    
    [개발자 이영희]: 지난주에 계획했던 사용자 인증 기능이 완료되었습니다. 
    테스트는 완료했고, 내일 배포 예정입니다.
    
    [팀장 김철수]: 좋습니다. 다음 스프린트 목표를 논의해볼까요?
    
    [디자이너 박민수]: UI 리뉴얼 작업이 필요합니다. 특히 대시보드 화면이 
    사용자 피드백에서 복잡하다는 의견이 많았어요.
    
    [팀장 김철수]: 알겠습니다. 박민수님이 다음 주까지 새 디자인 시안을 
    준비해주시고, 이영희님은 기술적 검토를 부탁드립니다.
    
    [개발자 정수진]: API 성능 최적화가 시급합니다. 응답 시간이 평균 3초인데,
    1초 이내로 줄여야 합니다. 데이터베이스 인덱싱을 다시 해야 할 것 같아요.
    
    [팀장 김철수]: 중요한 문제네요. 정수진님이 이번 주 내로 분석 보고서를 
    작성해주시고, 다음 회의에서 해결 방안을 논의합시다.
    
    [PM 최지은]: 고객사 A에서 커스텀 기능 요청이 들어왔습니다. 
    견적을 내야 하는데, 개발 공수가 얼마나 될지 확인이 필요합니다.
    
    [팀장 김철수]: 이영희님과 정수진님이 내일까지 검토해서 최지은님께 
    전달해주세요. 그럼 이번 회의는 여기까지 하겠습니다.
    """
    
    team_members = ["김철수", "이영희", "박민수", "정수진", "최지은"]
    
    # 사용자에게 선택지 제공
    print("회의 내용을 입력하시겠습니까?")
    print("1. 샘플 회의록 사용 (빠른 테스트)")
    print("2. 직접 입력")
    
    choice = input("\n선택 (1 or 2): ").strip()
    
    if choice == "2":
        print("\n회의 내용을 입력하세요 (완료: 빈 줄에서 Enter):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        transcript = "\n".join(lines)
        
        print("\n팀원 이름을 입력하세요 (쉼표로 구분):")
        team_input = input()
        team_members = [name.strip() for name in team_input.split(",")]
    else:
        transcript = sample_transcript
        print("\n✅ 샘플 회의록을 사용합니다.")
    
    # 그래프 생성 및 실행
    app = create_meeting_assistant_graph()
    
    initial_state = MeetingState(
        meeting_transcript=transcript,
        team_members=team_members
    )
    
    print("\n" + "🚀"*35)
    print("🚀 회의록 자동화 시스템을 시작합니다!")
    print("🚀"*70)
    
    # 실행
    final_state = app.invoke(initial_state)
    
    # 최종 결과
    print("\n\n" + "🎉"*35)
    print("🎉 시스템 완료!")
    print("🎉"*70)
    
    if final_state.get("send_approved"):
        print("\n✅ 회의록이 성공적으로 전송되었습니다!")
        print(f"📊 통계:")
        print(f"   - 액션 아이템: {len(final_state['action_items'])}개")
        print(f"   - 담당자: {len(set(item['assignee'] for item in final_state['action_items']))}명")
    else:
        print("\n⚠️ 회의록 전송이 취소되었습니다.")
    
    # 그래프 시각화
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./meeting_assistant_graph.png", "wb") as f:
            f.write(mermaid_png)
        print("\n💾 워크플로우 그래프 저장: meeting_assistant_graph.png")
    except Exception as e:
        print(f"\n⚠️ 그래프 저장 실패: {e}")


if __name__ == "__main__":
    main()


