# Chapter 9 Hands-on: Mini News Pipeline

간소화된 파이프라인으로 Chapter 9의 핵심 단계(수집 → LLM 요약 → LLM 분류 → 리포트)를 30분 안에 체험할 수 있습니다. OpenAI Chat Completions API를 직접 호출하므로 API 키가 반드시 필요합니다.

## 준비물 (5분)
1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install langchain-openai langchain-core` (또는 프로젝트 루트 의존성 활용)
3. `export OPENAI_API_KEY="sk-..."` 형태로 환경 변수 설정
4. 데이터는 `data/news_sample.json`으로 제공되며 정치 기사는 제외되어 있습니다.

## 구현 단계 (약 20분)
- **0~5분**: `config.py`와 `ai_ops.py`를 살펴 AI 모델 설정과 프롬프트 구성을 이해합니다.
- **5~15분**: `pipeline.py`에서 비동기 워크플로우(`asyncio`)로 요약·분류를 연계하는 방식을 확인하고 수정해봅니다.
- **15~20분**: `renderers.py`와 `mini_main.py`를 수정해 출력 포맷을 확장하거나 CLI 옵션을 추가해봅니다.

## 실행 (5분)
```bash
cd chapter9/programmers_hands_on
python mini_main.py --format markdown
python mini_main.py --format json --output outputs/news_report.json
```

보고서는 `outputs/` 디렉터리에 저장되며, 생성 내용은 모두 정치 기사를 제외한 샘플 뉴스만 포함합니다.

## 확장 아이디어
- `ai_ops.py`에 사용자 정의 프롬프트나 다른 모델을 연결해 비교 실험하기
- 배치 크기(`Config.BATCH_SIZE`)를 조정해 속도와 품질 변화를 탐색하기
- 테스트 파일(`tests/`)을 추가해 프롬프트/파이프라인의 기대 동작을 검증하기
