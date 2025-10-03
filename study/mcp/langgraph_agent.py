"""
심플한 LangGraph + MCP 에이전트 예제
- 상태: 간단한 메시지와 응답만 저장
- 노드: LLM 호출, 도구 실행, 응답 생성
- 엣지: 조건부 라우팅 (도구 필요 여부)
"""
import asyncio
import os
from typing import Literal
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from utils.logging import langsmith

langsmith("langgraph-ex17-simple")

# .env 파일 지원
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================
# 1. 상태 정의 (심플!)
# ============================================================
class AgentState(BaseModel):
    """에이전트 상태"""
    user_message: str = ""
    ai_message: AIMessage | None = None
    tool_results: list[ToolMessage] = Field(default_factory=list)
    final_response: str = ""


# ============================================================
# 2. 전역 변수
# ============================================================
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools_cache = None  # 전역 변수로 도구 캐싱


# ============================================================
# 3. 노드 함수들 (심플!)
# ============================================================


def llm_node(state: AgentState) -> dict:
    """LLM이 사용자 메시지를 보고 도구 사용 여부를 결정"""
    global tools_cache
    
    llm_with_tools = llm.bind_tools(tools_cache)
    
    # 시스템 메시지 + 사용자 메시지
    messages = [
        HumanMessage(content=f"""당신은 친절한 AI 어시스턴트입니다.

사용자 질문: {state.user_message}

간단한 인사는 도구 없이 바로 답변하세요.
도구가 필요한 경우에만 사용하세요.""")
    ]
    
    ai_msg = llm_with_tools.invoke(messages)
    
    # 도구 사용 여부 로깅
    if ai_msg.tool_calls:
        tool_names = [tc["name"] for tc in ai_msg.tool_calls]
        print(f"  🔧 도구 호출: {', '.join(tool_names)}")
    
    return {"ai_message": ai_msg}


async def tool_node(state: AgentState) -> dict:
    """도구를 실행 (비동기) - 모든 tool_calls 처리"""
    ai_msg = state.ai_message
    
    if not ai_msg.tool_calls:
        return {"tool_results": []}
    
    tool_messages = []
    
    # 모든 도구 호출 처리
    for tool_call in ai_msg.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        
        print(f"  ⚙️  도구 실행 중: {tool_name}({tool_args})")
        
        # 도구 실행 (비동기)
        result = None
        for tool in tools_cache:
            if tool.name == tool_name:
                result = await tool.ainvoke(tool_args)
                print(f"  ✅ 도구 결과: {result[:100]}..." if len(str(result)) > 100 else f"  ✅ 도구 결과: {result}")
                break
        
        if result is None:
            result = f"도구 '{tool_name}'를 찾을 수 없습니다."
            print(f"  ❌ {result}")
        
        # ToolMessage 생성
        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=tool_call_id)
        )
    
    return {"tool_results": tool_messages}


def response_node(state: AgentState) -> dict:
    """최종 응답 생성"""
    # 도구 사용 안 했으면 AI 메시지 그대로 반환
    if not state.ai_message.tool_calls:
        return {"final_response": state.ai_message.content}
    
    # 도구 결과를 바탕으로 최종 응답 생성
    messages = [
        HumanMessage(content=state.user_message),
        state.ai_message,
        *state.tool_results  # 모든 ToolMessage 추가
    ]
    
    final_ai_msg = llm.invoke(messages)
    return {"final_response": final_ai_msg.content}


# ============================================================
# 4. 라우팅 함수 (심플!)
# ============================================================
def should_use_tool(state: AgentState) -> Literal["use_tool", "respond"]:
    """도구 사용 여부 결정"""
    if state.ai_message and state.ai_message.tool_calls:
        return "use_tool"
    return "respond"


# ============================================================
# 5. 그래프 생성 (심플!)
# ============================================================
def create_simple_graph():
    """심플한 LangGraph 생성"""
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("llm", llm_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("respond", response_node)
    
    # 엣지 추가
    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges(
        "llm",
        should_use_tool,
        {
            "use_tool": "tool",
            "respond": "respond"
        }
    )
    workflow.add_edge("tool", "respond")
    workflow.add_edge("respond", END)
    
    return workflow.compile()


# ============================================================
# 6. 메인 실행
# ============================================================
async def main():
    """메인 실행 함수"""
    global tools_cache
    
    # 환경 체크
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 환경변수가 필요합니다.")
        return
    
    server_url = "http://localhost:8000/mcp/"
    
    try:
        print("🔧 MCP 서버 연결 중...\n")
        
        # MCP 세션을 전체 실행 기간 동안 유지
        async with streamablehttp_client(server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                # 1. 세션 초기화 및 도구 로드
                await session.initialize()
                tools_cache = await load_mcp_tools(session)
                print(f"✅ 로드된 도구: {[tool.name for tool in tools_cache]}\n")
                
                # 2. 그래프 생성
                graph = create_simple_graph()
                
                # 3. 테스트 질문들
                queries = [
                    # "안녕! 내 이름은 철수야",
                    # "코드 리뷰용 프롬프트를 알려줘",
                    "summarize 프롬프트도 보여줘",
                ]
                
                # 4. 각 질문 처리 (세션이 살아있는 동안)
                for i, query in enumerate(queries, 1):
                    print(f"[질문 {i}] {query}")
                    
                    result = await graph.ainvoke({"user_message": query})
                    
                    print(f"[응답] {result['final_response']}\n")
                    print("-" * 60 + "\n")
    
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
