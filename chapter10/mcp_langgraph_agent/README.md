# LangGraph 및 MCP를 활용한 AI 에이전트 채팅 애플리케이션

이 프로젝트는 LangGraph와 MCP(Model-Context-Protocol)를 사용하여 구축된 AI 에이전트 채팅 애플리케이션입니다. 사용자는 웹 인터페이스를 통해 "금토깽"이라는 이름의 AI 어시스턴트와 대화할 수 있으며, AI는 다양한 도구를 활용하여 실시간 정보를 제공하고 작업을 수행합니다.

## 프로젝트 아키텍처

이 애플리케이션은 두 가지 주요 구성 요소로 이루어져 있습니다.

1.  **MCP 서버 (`mcp_server.py`)**: AI 에이전트가 사용할 수 있는 도구(Tool)들을 API 형태로 제공하는 백엔드 서버입니다. 각 도구는 특정 기능을 수행하며, 에이전트는 필요에 따라 이 도구들을 호출합니다.
2.  **채팅 에이전트 (`chat_agent.py`)**: FastAPI로 구축된 웹 애플리케이션으로, 사용자와의 상호작용을 처리합니다. MCP 서버로부터 도구를 로드하고, LangGraph를 사용하여 ReAct 기반의 에이전트를 생성합니다. 사용자의 메시지를 받아 에이전트의 응답을 실시간으로 스트리밍합니다.

## 디렉터리 구조 

.
├── chat_agent.py
├── mcp_server.py
├── README.md
├── static
│   ├── script.js
│   └── style.css
└── templates
    └── index.html

## 파일 설명

### `mcp_server.py`

`FastMCP`를 사용하여 다양한 기능을 도구로 제공하는 서버입니다.

-   **`scrape_page_text(url: str)`**: 주어진 URL의 웹페이지에서 텍스트 콘텐츠를 스크랩합니다.
-   **`get_weather(city_name: str)`**: 도시 이름을 입력받아 현재 날씨 정보를 반환합니다.
-   **`get_news_headlines()`**: 구글 뉴스의 RSS 피드를 통해 최신 뉴스 헤드라인과 링크를 제공합니다.
-   **`get_kbo_rank()`**: 한국 프로야구(KBO)의 현재 순위 정보를 가져옵니다.
-   **`today_schedule()`**: 미리 정의된 오늘의 일정을 반환합니다.
-   **`daily_quote()`**: 영감을 주는 명언을 생성하여 제공합니다.
-   **`brief_today()`**: 사용자의 위치를 기반으로 날씨, 뉴스, 일정, 명언 등을 종합하여 브리핑하는 복합 기능입니다.

### `chat_agent.py`

FastAPI 기반의 웹 애플리케이션으로, 채팅 인터페이스와 에이전트 로직을 담당합니다.

-   **`lifespan` 함수**: 애플리케이션 시작 시 MCP 서버에 연결하고, `load_mcp_tools`를 통해 도구를 로드한 후, 이 도구들을 사용하여 LangGraph 에이전트를 생성합니다.
-   **`create_prompt_template()`**: 에이전트의 역할과 능력을 정의하는 시스템 프롬프트를 생성합니다. 에이전트의 이름은 "금토깽"으로 설정되어 있습니다.
-   **`create_agent(tools)`**: `ChatOpenAI` 모델과 제공된 도구를 사용하여 `create_react_agent`로 ReAct 에이전트를 생성합니다.
-   **`/` (GET)**: 메인 채팅 페이지(`index.html`)를 렌더링합니다.
-   **`/chat` (POST)**: 사용자의 메시지를 받아 에이전트를 실행하고, `astream_events`를 통해 생성되는 응답을 서버-전송 이벤트(SSE)로 스트리밍합니다.

### `static/` 및 `templates/`

웹 프론트엔드를 구성하는 정적 파일들입니다.

-   **`templates/index.html`**: 채팅 UI의 HTML 구조를 정의합니다. 사용자가 메시지를 입력하고, 에이전트의 응답을 실시간으로 볼 수 있는 인터페이스를 제공합니다.
-   **`static/script.js`**: 클라이언트 측 로직을 처리합니다. 사용자가 보낸 메시지를 서버의 `/chat` 엔드포인트로 전송하고, 스트리밍 응답을 받아 화면에 표시하는 역할을 합니다.
-   **`static/style.css`**: 채팅 애플리케이션의 시각적 스타일을 정의합니다.

## 실행 방법

1.  **필요한 라이브러리 설치**:
    ```bash
    uv sync
    ```
    *(참고: `pyproject.toml` 파일이 프로젝트에 포함되어 있다고 가정합니다. 없다면 필요한 라이브러리들을 직접 설치해야 합니다: `fastapi`, `uvicorn`, `langgraph`, `langchain-openai`, `langchain-mcp-adapters`, `httpx`, `beautifulsoup4`, `feedparser`, `geopy` 등)*

2.  **MCP 서버 실행**:
    터미널을 열고 다음 명령어를 실행하여 MCP 서버를 시작합니다. 기본적으로 포트 8000에서 실행됩니다.
    ```bash
    python chapter10/mcp_langgraph_agent/mcp_server.py
    ```

3.  **채팅 에이전트 실행**:
    다른 터미널을 열고 다음 명령어를 실행하여 채팅 웹 애플리케이션을 시작합니다. 기본적으로 포트 8001에서 실행됩니다.
    ```bash
    python chapter10/mcp_langgraph_agent/chat_agent.py
    ```

4.  **애플리케이션 접속**:
    웹 브라우저를 열고 `http://localhost:8001` 주소로 접속하면 채팅 인터페이스를 사용할 수 있습니다.
