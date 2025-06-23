"""Basic Hello World A2A Agent Server."""

import sys
from pathlib import Path

import uvicorn

sys.path.append(str(Path(__file__).parent.parent))

from a2a.server.apps import A2AFastAPIApplication

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agent_executor import HelloAgentExecutor


def create_agent_card() -> AgentCard:
    """Create the agent card for the basic Hello World agent."""
    # Define the basic greeting skill
    greeting_skill = AgentSkill(
        id="basic_greeting",
        name="Basic Greeting",
        description="간단한 인사와 기본적인 대화를 제공합니다",
        tags=["greeting", "hello", "basic"],
        examples=["안녕하세요", "hello", "hi", "고마워요"],
        inputModes=["text"],
        outputModes=["text"],
    )

    # Create the public agent card
    agent_card = AgentCard(
        name="Basic Hello World Agent",
        description="A2A 프로토콜을 학습하기 위한 기본적인 Hello World 에이전트입니다",
        url="http://localhost:9999/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[greeting_skill],
        supportsAuthenticatedExtendedCard=False,
    )

    return agent_card


def main():
    """Main function to start the basic agent server."""
    port = 9999
    host = "0.0.0.0"

    print("Starting Basic Hello World A2A Agent...")
    print(f"Server will run on http://{host}:{port}")
    print(f"Agent Card: http://{host}:{port}/.well-known/agent.json")
    print("이것은 A2A 프로토콜 학습을 위한 기본 예제입니다")

    # Create agent card
    agent_card = create_agent_card()

    # Create request handler with task store
    request_handler = DefaultRequestHandler(
        agent_executor=HelloAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # Create A2A server application
    server = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    app = server.build()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
