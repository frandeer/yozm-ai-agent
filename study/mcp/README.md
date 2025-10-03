# MCP + LangGraph 통합 예제 🚀

이 프로젝트는 FastMCP 서버와 LangGraph 에이전트를 연동하는 예제입니다.

## 📁 파일 구조

```
mcp/
├── mcp_server.py          # MCP 서버 (도구와 리소스 정의)
├── test_client.py         # MCP 클라이언트 테스트
├── langgraph_agent.py     # LangGraph 에이전트 (MCP 도구 사용)
└── README.md              # 이 파일
```

## 🛠️ MCP 서버 (mcp_server.py)

### 제공하는 도구 (Tools)
- `hello_world(name)`: 이름으로 인사
- `get_prompt(prompt_type)`: 사전 정의된 프롬프트 반환
  - `general`: 일반 어시스턴트 프롬프트
  - `code_review`: 코드 리뷰 프롬프트
  - `translate`: 번역 프롬프트
  - `summarize`: 요약 프롬프트

### 제공하는 리소스 (Resources)
- `simple://info`: 서버 정보 제공

## 🚀 실행 방법

### 1단계: MCP 서버 실행

터미널 1에서:
```bash
cd /Users/ho/lab/ai/yozm-ai-agent/study/mcp
python mcp_server.py
```

출력:
```
🚀 MCP 서버 시작 중...
📡 URL: http://localhost:8000/mcp
🔧 사용 가능한 도구: hello_world, get_prompt
📦 사용 가능한 리소스: simple://info

Ctrl+C를 눌러 종료하세요.
```

### 2단계: LangGraph 에이전트 실행

터미널 2에서:
```bash
cd /Users/ho/lab/ai/yozm-ai-agent/study/mcp
python langgraph_agent.py
```

## 📊 실행 흐름

```
┌─────────────────┐
│  MCP 서버       │  (포트 8000)
│  mcp_server.py  │
│                 │
│  Tools:         │
│  - hello_world  │
│  - get_prompt   │
│                 │
│  Resources:     │
│  - simple://info│
└────────┬────────┘
         │ HTTP
         │ http://localhost:8000/mcp
         │
┌────────▼────────┐
│ LangGraph       │
│ 에이전트        │
│                 │
│ 1. MCP 연결     │
│ 2. 도구 로드    │
│ 3. 에이전트 생성│
│ 4. 질문 처리    │
└─────────────────┘
```

## 💡 예제 시나리오

### 시나리오 1: 인사하기
```
사용자: "안녕! 내 이름은 철수야"

에이전트 사고 과정:
1. hello_world 도구를 사용해야겠다
2. hello_world(name="철수") 호출
3. 결과: "Hello, 철수!"
```

### 시나리오 2: 프롬프트 요청
```
사용자: "코드 리뷰용 프롬프트를 알려줘"

에이전트 사고 과정:
1. get_prompt 도구를 사용해야겠다
2. get_prompt(prompt_type="code_review") 호출
3. 결과 반환
```

## 🔧 테스트

### MCP 서버만 테스트 (HTTP 클라이언트)
```bash
python test_client.py
```

### LangGraph 에이전트 테스트
```bash
python langgraph_agent.py
```

## 📝 핵심 코드 설명

### MCP 서버에서 도구 정의
```python
from fastmcp import FastMCP

mcp = FastMCP("hello_world")

@mcp.tool
def hello_world(name: str = "World") -> str:
    """간단한 인사"""
    return f"Hello, {name}!"

# HTTP 모드로 실행
mcp.run(transport="http", host="0.0.0.0", port=8000)
```

### LangGraph에서 MCP 도구 사용
```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# MCP 서버 연결 및 도구 로드
async with streamablehttp_client("http://localhost:8000/mcp") as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # MCP 도구를 LangChain 도구로 변환
        tools = await load_mcp_tools(session)
        
        # LangGraph 에이전트 생성
        agent = create_react_agent(llm, tools)
        
        # 에이전트 실행
        result = await agent.ainvoke({"messages": [...]})
```

## 🎯 주요 개념

### 1. MCP (Model Context Protocol)
- 도구(Tools)와 리소스(Resources)를 표준화된 방식으로 제공
- stdio, HTTP, SSE 등 다양한 전송 방식 지원

### 2. LangGraph ReAct 에이전트
- **Re**asoning + **Act**ing 패턴
- 도구를 언제, 어떻게 사용할지 스스로 판단
- 반복적으로 사고하고 행동하며 문제 해결

### 3. 통합 구조
```
MCP 서버 (도구 제공)
    ↓
MCP Client (연결)
    ↓
load_mcp_tools (변환)
    ↓
LangChain Tools
    ↓
LangGraph Agent (사용)
```

## 🔍 디버깅 팁

### 문제: "All connection attempts failed"
- **원인**: MCP 서버가 실행되지 않음
- **해결**: `python mcp_server.py` 먼저 실행

### 문제: "No tools were found"
- **원인**: 
  1. import 경로 오류 (`from mcp.server.fastmcp` ❌)
  2. `@mcp.tool()` 괄호 있음 ❌
- **해결**:
  1. `from fastmcp import FastMCP` ✅
  2. `@mcp.tool` (괄호 없이) ✅

### 문제: Transport 오류
- **원인**: `transport="streamable-http"` (잘못된 값)
- **해결**: `transport="http"` ✅

## 📚 참고 자료

- [FastMCP 공식 문서](https://github.com/jlowin/fastmcp)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [MCP 스펙](https://spec.modelcontextprotocol.io/)

## 🎉 확장 아이디어

1. **더 많은 도구 추가**: 날씨, 뉴스, 검색 등
2. **웹 UI 추가**: FastAPI로 채팅 인터페이스 구현
3. **여러 MCP 서버 연동**: 다양한 기능을 모듈화
4. **스트리밍 응답**: 실시간으로 에이전트 사고 과정 표시

---

만든이: AI 학습자 🤖

