from typing import Literal
from fastmcp import FastMCP

mcp = FastMCP("hello_world")

@mcp.tool
def hello_world(name: str = "World") -> str:
    """간단한 인사"""
    return f"Hello, {name}!"


@mcp.tool
def get_prompt(prompt_type: Literal["general", "code_review", "translate", "summarize"] = "general") -> str:
    """사전 정의된 프롬프트 반환
    
    Args:
        prompt_type: 프롬프트 타입 (general, code_review, translate, summarize 중 선택)
    """
    prompts = {
        "general": "당신은 도움이 되는 AI 어시스턴트입니다. 사용자의 질문에 정확하고 친절하게 답변해주세요.",
        "code_review": "다음 코드를 검토하고 개선점을 제안해주세요. 코드의 가독성, 성능, 보안 측면을 고려해주세요.",
        "translate": "다음 텍스트를 자연스러운 한국어로 번역해주세요.",
        "summarize": "다음 내용을 핵심 포인트 중심으로 간결하게 요약해주세요.",
    }
    return prompts.get(prompt_type, prompts["general"])


@mcp.resource("simple://info")
def get_server_info() -> str:
    """서버 정보를 제공하는 리소스"""
    return """
서버 정보:
- 이름: 코드리뷰어
- 버전: 1.0.0
- 설명: 코드 리뷰 어시스턴트
"""


if __name__ == "__main__":
    # HTTP 모드로 실행 (LangGraph 연동용)
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)