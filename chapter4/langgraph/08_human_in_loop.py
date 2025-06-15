from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
import time
import random


# ① 워크플로우 단계 정의
class WorkflowStep:
    EMAIL_COMPOSER = "EMAIL_COMPOSER"
    CONTENT_REVIEWER = "CONTENT_REVIEWER"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    EMAIL_SENDER = "EMAIL_SENDER"
    REVISION_HANDLER = "REVISION_HANDLER"
    FINAL_REPORT = "FINAL_REPORT"


# ② 그래프 상태 정의
class EmailWorkflowState(BaseModel):
    # 이메일 정보
    recipient: str = Field(default="", description="수신자 이메일")
    subject: str = Field(default="", description="이메일 제목")
    content: str = Field(default="", description="이메일 내용")
    email_type: str = Field(default="", description="이메일 유형")
    
    # 검토 및 승인
    review_score: float = Field(default=0.0, description="내용 검토 점수")
    review_comments: list = Field(default_factory=list, description="검토 의견")
    requires_approval: bool = Field(default=True, description="승인 필요 여부")
    
    # 휴먼 승인 상태
    human_decision: str = Field(default="pending", description="승인 상태: pending/approved/rejected/revision")
    approval_message: str = Field(default="", description="승인자 메시지")
    revision_requests: list = Field(default_factory=list, description="수정 요청 사항")
    
    # 실행 결과
    is_sent: bool = Field(default=False, description="발송 완료 여부")
    send_timestamp: str = Field(default="", description="발송 시간")
    final_status: str = Field(default="", description="최종 상태")
    
    # 메타데이터
    workflow_step: str = Field(default="", description="현재 워크플로우 단계")
    attempt_count: int = Field(default=0, description="시도 횟수")


# ③ 이메일 작성 노드
def email_composer(state: EmailWorkflowState) -> Dict[str, Any]:
    recipient = state.recipient
    email_type = state.email_type
    
    print(f"[email_composer] ✍️ 이메일 작성 중...")
    print(f"                  수신자: {recipient}")
    print(f"                  유형: {email_type}")
    
    # 이메일 유형별 템플릿
    templates = {
        "welcome": {
            "subject": "환영합니다! 서비스 이용 안내",
            "content": f"""안녕하세요, {recipient}님!

저희 서비스에 가입해주셔서 진심으로 감사드립니다.

주요 기능:
• 대시보드에서 실시간 데이터 확인
• 맞춤형 알림 설정
• 24/7 고객 지원

궁금한 점이 있으시면 언제든 문의해주세요.

감사합니다.
고객 서비스팀"""
        },
        "notification": {
            "subject": "중요한 알림이 있습니다",
            "content": f"""안녕하세요, {recipient}님!

다음과 같은 중요한 업데이트가 있습니다:

• 시스템 업데이트 예정: 2024년 1월 20일 02:00-04:00
• 서비스 일시 중단될 수 있습니다
• 미리 데이터를 백업해주세요

자세한 내용은 공지사항을 확인해주세요.

감사합니다."""
        },
        "promotion": {
            "subject": "🎉 특별 할인 이벤트 안내",
            "content": f"""안녕하세요, {recipient}님!

특별한 혜택을 준비했습니다!

🎁 이벤트 내용:
• 프리미엄 플랜 50% 할인
• 기간: 2024년 1월 15일 ~ 1월 31일
• 추가 혜택: 3개월 무료 연장

지금 바로 업그레이드하고 더 많은 기능을 경험해보세요!

[업그레이드 하기] 버튼을 클릭하세요.

감사합니다."""
        }
    }
    
    template = templates.get(email_type, templates["notification"])
    
    print(f"[email_composer] ✅ 이메일 작성 완료")
    
    return {
        "subject": template["subject"],
        "content": template["content"],
        "workflow_step": "composed",
        "attempt_count": state.attempt_count + 1
    }


# ④ 내용 검토 노드
def content_reviewer(state: EmailWorkflowState) -> Dict[str, Any]:
    subject = state.subject
    content = state.content
    email_type = state.email_type
    
    print(f"[content_reviewer] 🔍 이메일 내용 검토 중...")
    
    # 자동 검토 기준
    review_criteria = {
        "length": len(content),
        "has_greeting": "안녕하세요" in content,
        "has_closing": "감사합니다" in content,
        "has_contact": "문의" in content or "연락" in content,
        "professional_tone": not any(word in content.lower() for word in ["ㅋㅋ", "ㅎㅎ", "~~"]),
        "clear_subject": len(subject) > 5 and len(subject) < 50
    }
    
    # 검토 점수 계산
    total_criteria = len(review_criteria)
    passed_criteria = sum(1 for criterion, passed in review_criteria.items() if passed)
    review_score = (passed_criteria / total_criteria) * 100
    
    # 검토 의견 생성
    comments = []
    
    if review_criteria["length"] < 50:
        comments.append("⚠️ 내용이 너무 짧습니다. 더 자세한 설명을 추가해주세요.")
    elif review_criteria["length"] > 500:
        comments.append("⚠️ 내용이 너무 깁니다. 핵심 내용만 간결하게 작성해주세요.")
    else:
        comments.append("✅ 적절한 길이입니다.")
    
    if not review_criteria["has_greeting"]:
        comments.append("⚠️ 인사말이 없습니다. '안녕하세요'를 추가해주세요.")
    else:
        comments.append("✅ 적절한 인사말이 있습니다.")
    
    if not review_criteria["has_closing"]:
        comments.append("⚠️ 마무리 인사가 없습니다. '감사합니다'를 추가해주세요.")
    else:
        comments.append("✅ 적절한 마무리 인사가 있습니다.")
    
    if not review_criteria["professional_tone"]:
        comments.append("⚠️ 비공식적인 표현이 포함되어 있습니다. 전문적인 톤으로 수정해주세요.")
    else:
        comments.append("✅ 전문적인 톤을 유지하고 있습니다.")
    
    if not review_criteria["clear_subject"]:
        comments.append("⚠️ 제목이 너무 짧거나 깁니다. 명확하고 간결한 제목으로 수정해주세요.")
    else:
        comments.append("✅ 적절한 제목입니다.")
    
    # 승인 필요 여부 결정
    requires_approval = review_score < 80 or email_type == "promotion"
    
    print(f"[content_reviewer] 📊 검토 완료: {review_score:.1f}점")
    print(f"                   승인 필요: {'예' if requires_approval else '아니오'}")
    
    return {
        "review_score": review_score,
        "review_comments": comments,
        "requires_approval": requires_approval,
        "workflow_step": "reviewed"
    }


# ⑤ 휴먼 승인 노드 (시뮬레이션)
def human_approval(state: EmailWorkflowState) -> Dict[str, Any]:
    print(f"[human_approval] 👤 휴먼 승인 대기 중...")
    print(f"                 이메일 정보:")
    print(f"                 • 수신자: {state.recipient}")
    print(f"                 • 제목: {state.subject}")
    print(f"                 • 검토 점수: {state.review_score:.1f}점")
    
    print(f"\n--- 승인 요청 ---")
    print(f"제목: {state.subject}")
    print(f"수신자: {state.recipient}")
    print(f"내용 미리보기: {state.content[:100]}...")
    print(f"\n검토 의견:")
    for comment in state.review_comments:
        print(f"  {comment}")
    
    # 실제 환경에서는 사용자 입력을 받아야 하지만, 시뮬레이션에서는 자동 결정
    print(f"\n⏳ 승인자 결정 대기 중... (시뮬레이션)")
    time.sleep(2)  # 승인 대기 시간 시뮬레이션
    
    # 검토 점수에 따른 승인 확률
    approval_probability = state.review_score / 100
    random_decision = random.random()
    
    if random_decision < approval_probability:
        if random.random() < 0.8:  # 80% 확률로 승인
            decision = "approved"
            message = "내용이 적절합니다. 발송을 승인합니다."
        else:  # 20% 확률로 수정 요청
            decision = "revision"
            message = "일부 수정이 필요합니다."
            revision_requests = ["제목을 더 구체적으로 작성해주세요.", "내용 중 일부 표현을 수정해주세요."]
    else:
        if random.random() < 0.7:  # 70% 확률로 수정 요청
            decision = "revision"
            message = "수정 후 다시 검토가 필요합니다."
            revision_requests = [
                "인사말을 더 정중하게 작성해주세요.",
                "내용을 더 자세히 설명해주세요.",
                "문의처 정보를 추가해주세요."
            ]
        else:  # 30% 확률로 거부
            decision = "rejected"
            message = "이메일 발송을 거부합니다. 내용이 부적절합니다."
            revision_requests = []
    
    print(f"[human_approval] 📝 승인 결정: {decision}")
    print(f"                 메시지: {message}")
    
    result = {
        "human_decision": decision,
        "approval_message": message,
        "workflow_step": "awaiting_approval"
    }
    
    if decision == "revision":
        result["revision_requests"] = revision_requests
    
    return result


# ⑥ 수정 처리 노드
def revision_handler(state: EmailWorkflowState) -> Dict[str, Any]:
    print(f"[revision_handler] ✏️ 수정 사항 처리 중...")
    
    revision_requests = state.revision_requests
    current_content = state.content
    current_subject = state.subject
    
    print(f"                   수정 요청 사항:")
    for i, request in enumerate(revision_requests, 1):
        print(f"                   {i}. {request}")
    
    # 수정 요청에 따른 자동 수정 (시뮬레이션)
    modified_content = current_content
    modified_subject = current_subject
    
    for request in revision_requests:
        if "제목" in request:
            if "구체적" in request:
                modified_subject = f"[중요] {current_subject}"
        
        if "인사말" in request:
            if "안녕하세요" not in modified_content:
                modified_content = f"안녕하세요!\n\n{modified_content}"
        
        if "자세히" in request:
            modified_content = modified_content.replace(
                "궁금한 점이 있으시면",
                "추가 정보나 궁금한 점이 있으시면"
            )
        
        if "문의처" in request:
            if "문의" not in modified_content:
                modified_content += "\n\n문의처: support@company.com\n전화: 1588-1234"
    
    print(f"[revision_handler] ✅ 수정 완료")
    
    return {
        "subject": modified_subject,
        "content": modified_content,
        "workflow_step": "revised",
        "human_decision": "pending"  # 다시 승인 대기 상태로
    }


# ⑦ 이메일 발송 노드
def email_sender(state: EmailWorkflowState) -> Dict[str, Any]:
    recipient = state.recipient
    subject = state.subject
    
    print(f"[email_sender] 📧 이메일 발송 중...")
    print(f"               수신자: {recipient}")
    print(f"               제목: {subject}")
    
    # 발송 시뮬레이션
    time.sleep(random.uniform(1.0, 2.0))
    
    # 발송 성공률 95%
    send_success = random.random() < 0.95
    
    if send_success:
        timestamp = "2024-01-15 14:30:25"
        print(f"[email_sender] ✅ 발송 완료: {timestamp}")
        
        return {
            "is_sent": True,
            "send_timestamp": timestamp,
            "workflow_step": "sent"
        }
    else:
        print(f"[email_sender] ❌ 발송 실패: 네트워크 오류")
        
        return {
            "is_sent": False,
            "send_timestamp": "",
            "workflow_step": "send_failed"
        }


# ⑧ 최종 리포트 노드
def final_report(state: EmailWorkflowState) -> Dict[str, Any]:
    print(f"[final_report] 📋 최종 리포트 생성 중...")
    
    # 최종 상태 결정
    if state.is_sent:
        final_status = "발송 완료"
    elif state.human_decision == "rejected":
        final_status = "발송 거부됨"
    elif state.human_decision == "pending":
        final_status = "승인 대기 중"
    else:
        final_status = "발송 실패"
    
    # 리포트 생성
    report_sections = []
    report_sections.append("📧 이메일 워크플로우 최종 리포트")
    report_sections.append("=" * 45)
    
    # 기본 정보
    report_sections.append(f"\n📝 이메일 정보:")
    report_sections.append(f"   수신자: {state.recipient}")
    report_sections.append(f"   제목: {state.subject}")
    report_sections.append(f"   유형: {state.email_type}")
    
    # 검토 결과
    report_sections.append(f"\n🔍 검토 결과:")
    report_sections.append(f"   점수: {state.review_score:.1f}/100점")
    report_sections.append(f"   승인 필요: {'예' if state.requires_approval else '아니오'}")
    
    # 승인 과정
    report_sections.append(f"\n👤 승인 과정:")
    report_sections.append(f"   결정: {state.human_decision}")
    report_sections.append(f"   메시지: {state.approval_message}")
    if state.revision_requests:
        report_sections.append(f"   수정 요청: {len(state.revision_requests)}개")
    
    # 최종 결과
    report_sections.append(f"\n🎯 최종 결과:")
    report_sections.append(f"   상태: {final_status}")
    if state.is_sent:
        report_sections.append(f"   발송 시간: {state.send_timestamp}")
    report_sections.append(f"   총 시도 횟수: {state.attempt_count}회")
    
    final_report_text = "\n".join(report_sections)
    
    print(f"[final_report] ✅ 리포트 생성 완료")
    
    return {
        "final_status": final_report_text
    }


# ⑨ 라우팅 함수들
def should_seek_approval(state: EmailWorkflowState) -> Literal["approval", "send"]:
    """승인이 필요한지 확인"""
    if state.requires_approval:
        return "approval"
    else:
        return "send"


def handle_approval_decision(state: EmailWorkflowState) -> Literal["send", "revise", "report"]:
    """승인 결정에 따른 라우팅"""
    decision = state.human_decision
    
    if decision == "approved":
        return "send"
    elif decision == "revision":
        return "revise"
    else:  # rejected
        return "report"


def after_revision(state: EmailWorkflowState) -> Literal["review", "report"]:
    """수정 후 다시 검토할지 결정"""
    # 최대 3번까지만 수정 시도
    if state.attempt_count < 3:
        return "review"
    else:
        return "report"


# ⑩ 그래프 생성 (휴먼 인 더 루프 포함)
def create_human_in_loop_graph():
    workflow = StateGraph(EmailWorkflowState)
    
    # 노드 추가
    workflow.add_node(WorkflowStep.EMAIL_COMPOSER, email_composer)
    workflow.add_node(WorkflowStep.CONTENT_REVIEWER, content_reviewer)
    workflow.add_node(WorkflowStep.HUMAN_APPROVAL, human_approval)
    workflow.add_node(WorkflowStep.EMAIL_SENDER, email_sender)
    workflow.add_node(WorkflowStep.REVISION_HANDLER, revision_handler)
    workflow.add_node(WorkflowStep.FINAL_REPORT, final_report)
    
    # 시작점 설정
    workflow.add_edge(START, WorkflowStep.EMAIL_COMPOSER)
    
    # 작성 후 검토
    workflow.add_edge(WorkflowStep.EMAIL_COMPOSER, WorkflowStep.CONTENT_REVIEWER)
    
    # 검토 후 승인 필요 여부 확인 (핵심 휴먼 인 더 루프!)
    workflow.add_conditional_edges(
        WorkflowStep.CONTENT_REVIEWER,
        should_seek_approval,
        {
            "approval": WorkflowStep.HUMAN_APPROVAL,  # 승인 필요 시
            "send": WorkflowStep.EMAIL_SENDER          # 자동 발송 가능 시
        }
    )
    
    # 승인 결정에 따른 라우팅
    workflow.add_conditional_edges(
        WorkflowStep.HUMAN_APPROVAL,
        handle_approval_decision,
        {
            "send": WorkflowStep.EMAIL_SENDER,        # 승인 시 발송
            "revise": WorkflowStep.REVISION_HANDLER,  # 수정 요청 시
            "report": WorkflowStep.FINAL_REPORT       # 거부 시 리포트
        }
    )
    
    # 수정 후 재검토 여부 결정
    workflow.add_conditional_edges(
        WorkflowStep.REVISION_HANDLER,
        after_revision,
        {
            "review": WorkflowStep.CONTENT_REVIEWER,  # 다시 검토 (루프!)
            "report": WorkflowStep.FINAL_REPORT       # 최대 시도 초과 시
        }
    )
    
    # 발송 후 리포트
    workflow.add_edge(WorkflowStep.EMAIL_SENDER, WorkflowStep.FINAL_REPORT)
    
    # 리포트 후 종료
    workflow.add_edge(WorkflowStep.FINAL_REPORT, END)
    
    # 그래프 컴파일
    app = workflow.compile()
    
    return app


# ⑪ 테스트 함수
def test_human_in_loop():
    print("=== 휴먼 인 더 루프 이메일 워크플로우 테스트 ===\n")
    
    app = create_human_in_loop_graph()
    
    # 테스트 케이스
    test_cases = [
        {
            "name": "환영 이메일",
            "recipient": "user@example.com",
            "email_type": "welcome"
        },
        {
            "name": "프로모션 이메일",
            "recipient": "customer@company.com", 
            "email_type": "promotion"
        },
        {
            "name": "시스템 알림",
            "recipient": "admin@service.com",
            "email_type": "notification"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 테스트 케이스 {i}: {test_case['name']} ---")
        
        initial_state = EmailWorkflowState(
            recipient=test_case["recipient"],
            email_type=test_case["email_type"]
        )
        
        print("🚀 이메일 워크플로우 시작!")
        print("=" * 60)
        
        # 그래프 실행 (휴먼 승인 포함)
        final_state = app.invoke(initial_state)
        
        print("\n" + "=" * 60)
        print("📊 최종 리포트:")
        print(final_state['final_status'])
        
        print("\n" + "-" * 60)


# ⑫ 승인 시나리오 시연
def demo_approval_scenarios():
    print("\n=== 다양한 승인 시나리오 시연 ===\n")
    
    app = create_human_in_loop_graph()
    
    scenarios = [
        "자동 승인 (고품질 이메일)",
        "수동 승인 필요 (일반 이메일)", 
        "수정 요청 (개선 필요)",
        "발송 거부 (부적절한 내용)"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"--- 시나리오 {i}: {scenario} ---")
        
        initial_state = EmailWorkflowState(
            recipient=f"test{i}@example.com",
            email_type="notification"
        )
        
        final_state = app.invoke(initial_state)
        
        # 요약 결과 출력
        decision = final_state.get('human_decision', 'unknown')
        sent = final_state.get('is_sent', False)
        attempts = final_state.get('attempt_count', 0)
        
        status = "✅ 발송됨" if sent else "❌ 발송 안됨"
        print(f"결과: {status} | 승인 결정: {decision} | 시도: {attempts}회")
        print()


def main():
    print("=== LangGraph 휴먼 인 더 루프 예제 ===\n")
    
    # 기본 테스트
    test_human_in_loop()
    
    # 시나리오 시연
    demo_approval_scenarios()
    
    # 그래프 시각화
    print("\n=== 워크플로우 시각화 ===")
    app = create_human_in_loop_graph()
    
    # ASCII 그래프 출력
    ascii_graph = app.get_graph().draw_ascii()
    print("\n[ASCII 그래프]")
    print(ascii_graph)
    
    # Mermaid PNG 생성
    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open("./08_human_in_loop.png", "wb") as f:
            f.write(mermaid_png)
        print("\n[그래프 이미지] 08_human_in_loop.png 파일이 생성되었습니다!")
    except Exception as e:
        print(f"\n[그래프 이미지] 생성 실패: {e}")


if __name__ == "__main__":
    main()
