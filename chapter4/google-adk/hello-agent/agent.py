from google.adk.agents import Agent

def hello(name: str) -> str:
    """인사하는 함수"""
    return f"{name}님 안녕하세요!"

root_agent = Agent(
    name="hello_agent",
    model="gemini-2.0-flash",
    description=(
        "헬로에이전트"
    ),
    instruction=(
        "당신은 인사 전문가입니다. 사용자에게 친절하고 따뜻한 인사를 전하세요. "
    ),
    tools=[hello],
)