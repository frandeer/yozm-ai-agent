# workflow.py
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from state import NewsState
from agents.collector import RSSCollectorAgent
from agents.summarizer import NewsSummarizerAgent
from agents.organizer import NewsOrganizerAgent
from agents.reporter import ReportGeneratorAgent
from config import Config


def create_news_workflow(llm: ChatOpenAI = None) -> StateGraph:
    """뉴스 처리 워크플로우 생성"""

    # LLM이 제공되지 않으면 기본 설정으로 생성
    if llm is None:
        llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
            api_key=Config.OPENAI_API_KEY,
        )

    # 에이전트 인스턴스 생성
    collector = RSSCollectorAgent()
    summarizer = NewsSummarizerAgent(llm)
    organizer = NewsOrganizerAgent(llm)
    reporter = ReportGeneratorAgent(llm)

    # 상태 그래프 생성
    workflow = StateGraph(NewsState)

    # 노드 추가
    workflow.add_node("collect", collector.collect_rss)
    workflow.add_node("summarize", summarizer.summarize_news)
    workflow.add_node("organize", organizer.organize_news)
    workflow.add_node("report", reporter.generate_report)

    # 엣지 정의 (워크플로우 순서)
    workflow.set_entry_point("collect")
    workflow.add_edge("collect", "summarize")
    workflow.add_edge("summarize", "organize")
    workflow.add_edge("organize", "report")
    workflow.add_edge("report", END)

    # 컴파일된 워크플로우 반환
    return workflow.compile()
