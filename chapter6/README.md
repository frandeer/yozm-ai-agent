# 뉴스 멀티에이전트 시스템 (Supervisor Pattern)

LangGraph Supervisor 패턴을 사용한 뉴스 수집 및 처리 시스템입니다.

## 시스템 구조

### Supervisor Agent
- 전체 워크플로우를 조정하는 중앙 supervisor
- 각 전문 에이전트에게 적절한 작업을 위임

### Worker Agents
1. **News Collector**: RSS 피드에서 뉴스 수집
2. **News Classifier**: 뉴스 분류 및 중요도 점수 부여
3. **News Summarizer**: 중요한 뉴스 요약
4. **Report Generator**: 종합 리포트 생성 (JSON/HTML)
5. **Email Sender**: 이메일로 리포트 발송

## 설치 방법

### 1. uv 설치 (권장)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 또는 pip로 설치
pip install uv
```

### 2. 프로젝트 설정
```bash
# 의존성 설치
uv sync

# 개발 의존성까지 설치
uv sync --dev
```

### 3. 환경변수 설정
`.env` 파일 생성:
```
OPENAI_API_KEY=your_openai_api_key

# 이메일 설정 (선택사항)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient@gmail.com
```

## 실행 방법

### uv를 사용한 실행
```bash
# 즉시 실행
uv run python collecting_news_multi_agent.py

# 또는 가상환경 활성화 후 실행
uv shell
python collecting_news_multi_agent.py
```

### 개발 환경 설정
```bash
# 가상환경 활성화
uv shell

# 코드 포매팅
uv run black collecting_news_multi_agent.py

# 타입 체크
uv run mypy collecting_news_multi_agent.py

# 테스트 실행 (향후 구현 예정)
uv run pytest
```

### 스케줄러 실행 (매일 오전 9시)
코드에서 main() 함수의 주석을 변경:
```python
# system.run_pipeline()  # 이 줄을 주석 처리
system.schedule_daily_run()  # 이 줄의 주석 해제
```

## 특징

### Supervisor Pattern 장점
- **작업 분담**: 각 에이전트가 전문 영역에 집중
- **유연성**: 새로운 에이전트 추가 용이
- **확장성**: 에이전트별 독립적 개선 가능
- **오류 처리**: 개별 에이전트 오류가 전체 시스템에 미치는 영향 최소화

### 워크플로우
1. Supervisor가 뉴스 처리 요청을 받음
2. News Collector에게 RSS 피드 수집 위임
3. News Classifier에게 뉴스 분류 및 점수 부여 위임
4. News Summarizer에게 중요 뉴스 요약 위임
5. Report Generator에게 리포트 생성 위임
6. Email Sender에게 이메일 발송 위임

### 출력 파일
- `news_reports/news_report_YYYYMMDD_HHMMSS.json`: JSON 형식 리포트
- `news_reports/news_report_YYYYMMDD_HHMMSS.html`: HTML 형식 리포트

## 프로젝트 구조

```
chapter6/
├── pyproject.toml              # uv 프로젝트 설정
├── .env                        # 환경변수 (git에 포함되지 않음)
├── collecting_news_multi_agent.py  # 메인 애플리케이션
├── news_reports/               # 생성된 리포트 저장 디렉토리
├── README.md                   # 이 파일
└── CHANGES.md                  # 변경사항 문서
```

## 설정 옵션

### Config 클래스
- `RSS_URLS`: 뉴스 소스 URL 설정
- `EMAIL` 설정: SMTP 서버 및 인증 정보
- `OUTPUT_DIR`: 리포트 저장 디렉토리
- `SCHEDULE_TIME`: 스케줄러 실행 시간
- `MODEL_NAME`: 사용할 OpenAI 모델

### 이메일 설정 주의사항
Gmail 사용시 앱 비밀번호 필요:
1. Gmail 계정의 2단계 인증 활성화
2. 앱 비밀번호 생성
3. `EMAIL_PASSWORD`에 앱 비밀번호 사용

## 개발

### 의존성 추가
```bash
# 런타임 의존성 추가
uv add package_name

# 개발 의존성 추가
uv add --dev package_name
```

### 코드 품질
```bash
# 코드 포매팅
uv run black .

# 린팅
uv run flake8 .

# 타입 체크
uv run mypy .
```

## 문제 해결

### 일반적인 오류
1. **OpenAI API 키 오류**: `OPENAI_API_KEY` 환경변수 확인
2. **이메일 인증 오류**: Gmail 앱 비밀번호 사용 확인
3. **RSS 피드 오류**: 네트워크 연결 상태 확인
4. **uv 명령 오류**: uv 설치 상태 확인

### uv 관련 문제
```bash
# uv 업데이트
uv self update

# 캐시 정리
uv cache clean

# 가상환경 재생성
rm -rf .venv
uv sync
```

### 로그 확인
실행 중 각 에이전트의 작업 상태가 콘솔에 출력됩니다.

## 라이선스
MIT License

## 기여
이슈나 풀 리퀘스트를 통해 기여해 주세요.
