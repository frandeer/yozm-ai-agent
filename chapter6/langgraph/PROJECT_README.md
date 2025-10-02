# 🎯 실전 프로젝트: 스마트 회의록 자동화 시스템

## 📋 프로젝트 소개

**회사에서 바로 사용 가능한 Human-in-the-Loop 실전 프로젝트!**

회의가 끝나면 AI가 자동으로:
- 📝 회의 내용 요약
- 🎯 액션 아이템 추출
- 👤 담당자 자동 배정
- 📅 마감일 제안
- 📄 최종 보고서 생성

**하지만!** 중요한 결정마다 사람이 검토하고 승인합니다. (Human-in-the-Loop!)

---

## 🌟 왜 이 프로젝트인가?

### ✅ 실제 회사 문제 해결
- 회의록 작성에 30분 이상 소요 → **AI가 3분 안에**
- 액션 아이템 누락 문제 → **AI가 자동 추출**
- 담당자 배정 애매함 → **AI가 제안**

### ✅ Human-in-the-Loop 필수 지점
1. **요약 검토** - AI가 회의 내용을 잘못 이해할 수 있음
2. **액션 아이템 확인** - 중요한 항목을 놓치면 안 됨
3. **담당자 승인** - 민감한 인사 결정
4. **전송 승인** - 실수로 잘못된 내용이 전송되면 안 됨

### ✅ 실무 적용 가능
- 팀 미팅
- 스프린트 회의
- 프로젝트 킥오프
- 고객 미팅
- 브레인스토밍

---

## 🚀 실행 방법

### 방법 1: 터미널 버전 (간단)

```bash
cd chapter6/langgraph
python project_meeting_assistant.py
```

#### 실행 흐름:
```
1. 샘플 회의록 사용 or 직접 입력 선택
   ↓
2. AI가 요약 생성
   ↓
3. 👤 사람이 요약 검토 (승인/거부/수정)
   ↓
4. AI가 액션 아이템 추출
   ↓
5. 👤 사람이 액션 아이템 검토 (승인/추가/삭제/수정)
   ↓
6. AI가 최종 보고서 생성
   ↓
7. 👤 사람이 전송 승인
   ↓
8. ✅ 완료!
```

### 방법 2: 웹 버전 (실용적)

```bash
# Flask 설치 (필요시)
pip install flask

# 서버 실행
python project_meeting_assistant_web.py
```

브라우저에서 `http://localhost:5000` 접속!

---

## 📊 Human-in-the-Loop 지점 분석

### 🎯 지점 1: 요약 검토

**왜 필요한가?**
- AI가 농담을 중요한 내용으로 오해할 수 있음
- 맥락을 잘못 이해할 수 있음
- 중요도 판단이 틀릴 수 있음

**사람의 역할:**
```python
✅ 승인 → 다음 단계
✏️ 수정 → 수정 후 진행
❌ 거부 → AI가 다시 생성
```

---

### 🎯 지점 2: 액션 아이템 검토

**왜 필요한가?**
- 중요한 액션 아이템이 누락될 수 있음
- 담당자가 잘못 배정될 수 있음
- 마감일이 비현실적일 수 있음

**사람의 역할:**
```python
✅ 승인 → 다음 단계
➕ 추가 → 새 항목 추가
➖ 삭제 → 불필요한 항목 제거
✏️ 수정 → 담당자/마감일 조정
```

---

### 🎯 지점 3: 전송 승인

**왜 필요한가?**
- 잘못된 내용이 전체 팀에게 전송되면 안 됨
- 민감한 정보가 포함될 수 있음
- 최종 검토 필요

**사람의 역할:**
```python
✅ 승인 → 이메일 전송
❌ 취소 → 전송 중단
```

---

## 💡 실제 사용 예시

### 시나리오: 스프린트 회의

**입력:**
```
팀장: 이번 스프린트 목표를 논의합시다.
개발자A: 로그인 기능 완료했습니다.
개발자B: 다음은 결제 모듈이 필요합니다.
팀장: 개발자B님이 다음 주까지 결제 모듈 설계해주세요.
```

**AI 처리:**
```
요약 생성 →
  "이번 스프린트는 결제 모듈 설계가 주요 목표.
   로그인 기능은 완료됨."

액션 아이템 추출 →
  1. 결제 모듈 설계
     담당: 개발자B
     마감: 1주일 후
     우선순위: high
```

**Human-in-the-Loop:**
```
👤 사람 검토:
   - 요약 승인 ✅
   - 액션 아이템 확인
   - "기술 스택 선택" 항목 추가 ➕
   - 담당자에 "개발자A" 추가 (리뷰어로)
   - 전송 승인 ✅
```

**결과:**
```
📧 완벽한 회의록이 팀 전체에게 전송됨!
⏱️ 소요 시간: 5분 (기존 30분 → 83% 절약)
```

---

## 🔧 커스터마이징

### 팀에 맞게 수정하기

#### 1. 팀원 목록 변경
```python
team_members = ["김철수", "이영희", "박민수"]
```

#### 2. 보고서 형식 변경
`generate_final_report()` 함수의 프롬프트 수정

#### 3. 추가 Human-in-the-Loop 지점
```python
# 예: 우선순위 재평가 단계 추가
def review_priorities(state):
    # 사람이 우선순위를 검토
    pass

workflow.add_node("review_priorities", review_priorities)
```

#### 4. 이메일 전송 연동
```python
import smtplib
from email.mime.text import MIMEText

def send_email(report, recipients):
    msg = MIMEText(report)
    msg['Subject'] = '회의록'
    msg['From'] = 'bot@company.com'
    msg['To'] = ', '.join(recipients)
    
    # SMTP 서버 설정
    # ...
```

---

## 📈 확장 아이디어

### 1. Slack 연동
```python
from slack_sdk import WebClient

def send_to_slack(report):
    client = WebClient(token=os.environ['SLACK_TOKEN'])
    client.chat_postMessage(
        channel='#meetings',
        text=report
    )
```

### 2. 음성 → 텍스트 변환
```python
import whisper

def transcribe_meeting(audio_file):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result["text"]
```

### 3. 캘린더 연동
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

def add_to_calendar(action_item):
    # Google Calendar API로 일정 추가
    pass
```

### 4. 진행 상황 추적
```python
def track_action_items():
    # 액션 아이템 완료 여부 추적
    # 주간 리마인더 발송
    pass
```

---

## 🎓 학습 포인트

이 프로젝트를 통해 배우는 것:

### ✅ Human-in-the-Loop 패턴
- 언제 사람의 개입이 필요한가?
- 어떻게 워크플로우를 멈추는가?
- 상태를 어떻게 유지하는가?

### ✅ LangGraph 실전 활용
- 복잡한 워크플로우 설계
- 조건부 라우팅
- 상태 관리

### ✅ 프로덕션 레벨 고려사항
- 에러 처리
- 사용자 입력 검증
- 로깅

---

## 🐛 문제 해결

### Q: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask
```

### Q: AI 응답이 이상해요
- `temperature` 값 조정 (0.7 → 0.3으로 낮추면 더 보수적)
- 프롬프트 수정

### Q: 더 빠르게 실행하고 싶어요
- `gpt-4o-mini` 대신 `gpt-3.5-turbo` 사용

---

## 📊 성과 측정

### Before (AI 없이)
- ⏱️ 회의록 작성: 30분
- 😰 액션 아이템 누락: 자주 발생
- 📧 전송: 수동, 실수 가능

### After (Human-in-the-Loop AI)
- ⏱️ 회의록 작성: 5분 (83% 절약!)
- ✅ 액션 아이템 누락: AI가 추출 + 사람이 검증
- 📧 전송: 반자동, 승인 프로세스

---

## 🎯 다음 단계

1. ✅ 이 프로젝트 실행해보기
2. ✅ 팀 회의에 적용해보기
3. ✅ 피드백 받아서 개선
4. ✅ 다른 Human-in-the-Loop 시나리오 생각해보기
   - 코드 리뷰 자동화?
   - 고객 지원 티켓 분류?
   - 문서 번역 검수?

---

## 📝 라이선스

MIT License - 자유롭게 사용하세요!

---

## 🙌 기여

개선 아이디어나 버그 제보 환영합니다!

---

**만든 이:** AI Assistant  
**목적:** Human-in-the-Loop 실전 학습  
**난이도:** ⭐⭐⭐ (중급)  
**예상 소요 시간:** 30분

---

## 💬 피드백

이 프로젝트가 도움이 되었나요?
- 실제로 회사에서 써보셨나요?
- 어떤 개선이 필요한가요?
- 다른 Human-in-the-Loop 아이디어가 있나요?

**Happy Coding! 🚀**


