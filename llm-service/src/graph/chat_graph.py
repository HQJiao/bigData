from typing import TypedDict, Annotated

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from src.clients.dashscope import DashScopeClient


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    llm_response: str


def build_chat_graph(client: DashScopeClient):
    """构建对话图，每次调用使用不同的 client 实例"""

    def call_llm(state: ChatState) -> ChatState:
        messages = state["messages"]
        response = client.chat(messages)
        return {
            "llm_response": response,
            "messages": [AIMessage(content=response)],
        }

    graph = StateGraph(ChatState)
    graph.add_node("llm", call_llm)
    graph.set_entry_point("llm")
    graph.add_edge("llm", END)

    return graph.compile()
