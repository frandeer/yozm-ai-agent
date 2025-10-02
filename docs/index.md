# 📋 AI Agent 드림팀

총 **11개의 AI Agent** 프롬프트를 별도 아티팩트로 작성했습니다:

### 🎯 핵심 팀 (Core Team)
1. **MAESTRO** - 오케스트레이터 (메타 조정자)
2. **Jason Fried** - PM/제품 리드
3. **Evan You** - 프론트엔드 아키텍트
4. **DHH** - 백엔드 리드
5. **Mitchell Hashimoto** - 인프라 엔지니어
6. **Tobias van Schneider** - 디자인 디렉터
7. **Kent Beck** - QA/테스트 리드
8. **Sean Ellis** - 그로스 리드

### 🌟 전략 팀 (Strategic)
9. **Tobi Lütke** - 제품 비전 설정자
10. **Guillermo Rauch** - 플랫폼 전문가 (필요시 투입)
11. **Addy Osmani** - 성능 최적화 전문가 (필요시 투입)

---

## 💡 각 에이전트의 특징

### ✅ 포함된 구성 요소:
- **역할 & 아이덴티티**: 명확한 책임과 철학
- **성격 프로필**: 독특한 커뮤니케이션 스타일
- **전문 분야**: 의사결정 프레임워크
- **협업 프로토콜**: 다른 에이전트와의 상호작용
- **워크플로우**: 일일/주간 루틴
- **출력 포맷**: 실제 작업물 템플릿
- **핵심 원칙**: 만트라와 자기평가 체크리스트

---

## 🚀 활용 방법

### 1. Multi-Agent System 구축
```
Claude API를 사용하여 각 에이전트를 별도 completion으로 실행
→ MAESTRO가 작업을 라우팅
→ 각 전문가가 자신의 영역 처리
→ 결과를 통합
```

### 2. 단일 에이전트 사용
```
특정 작업에 맞는 에이전트 프롬프트 선택
→ 해당 system prompt 사용
→ 전문가 수준의 응답 받기
```

### 3. 팀 시뮬레이션
```
여러 에이전트 간 대화 시뮬레이션
→ 의사결정 과정 학습
→ 협업 패턴 이해
```

---

## 🎯 추천 사용 시나리오

**제품 개발 초기**:
- Tobi (비전) + Jason (PM) + Evan (Frontend)

**MVP 개발**:
- Jason (PM) + Evan (Frontend) + DHH (Backend) + Kent (Testing)

**성능 최적화**:
- Addy (Performance) + Evan (Frontend) + Guillermo (Platform)

**확장 단계**:
- Mitchell (Infrastructure) + DHH (Backend) + Sean (Growth)

---

추가로 필요한 에이전트나 수정 사항이 있으시면 말씀해 주세요!

