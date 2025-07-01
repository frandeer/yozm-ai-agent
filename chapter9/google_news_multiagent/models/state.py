# models/state.py
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class NewsState(TypedDict):
    """뉴스 처리 상태를 관리하는 TypedDict"""
    
    messages: Annotated[List[BaseMessage], add_messages]
    raw_news: List[Dict[str, Any]]
    summarized_news: List[Dict[str, Any]]
    categorized_news: Dict[str, List[Dict[str, Any]]]
    final_report: str
    error_log: List[str]