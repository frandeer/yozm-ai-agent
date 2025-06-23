from uuid import uuid4

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message
from a2a.utils import new_agent_text_message


def generate_message_id() -> str:
    return uuid4().hex


class HelloAgent:
    """Simple Hello World Agent using LangChain and OpenAI."""

    def __init__(self):
        """Initialize the agent with LangChain components."""

        self.chat = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.7,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """당신은 친절한 Hello World 에이전트입니다.
            사용자와 간단한 대화를 나누고, 인사와 기본적인 질문에 답변합니다. 
            당신의 목표는 사용자에게 친근하고 도움이 되는 경험을 제공하는 것입니다.""",
                ),
                ("user", "{message}"),
            ]
        )

    async def invoke(self, user_message: str) -> str:
        """Process user message using LangChain and OpenAI."""
        chain = self.prompt | self.chat
        response = await chain.ainvoke({"message": user_message})

        return response.content


class HelloAgentExecutor(AgentExecutor):
    """Basic A2A Agent Executor Implementation."""

    def __init__(self):
        self.agent = HelloAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the agent logic and enqueue response."""
        # Extract user message from context
        message = context.message
        for part in message.parts:
            if part.root.text:
                user_message = part.root.text

        # Process the message with the agent
        result = await self.agent.invoke(user_message)

        # Create and enqueue A2A message using utility function
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Handle cancellation requests."""
        # Basic agent doesn't support cancellation
        error_msg = "취소 기능은 지원되지 않습니다. Hello 에이전트는 즉시 응답합니다."
        error_message = Message(
            role="agent",
            parts=[{"type": "text", "text": error_msg}],
            messageId="cancel_error",
        )
        event_queue.enqueue_event(error_message)
