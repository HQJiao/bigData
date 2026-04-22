import asyncio
from typing import TypedDict, Annotated

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from src.clients.factory import create_client
from src.agents.tools import available_tools, BaseTool
from src.app.settings import settings


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    llm_response: str
    tool_result: str
    tools_used: list[str]


def _to_dict(msg) -> dict:
    role = "user" if getattr(msg, "type", "") == "human" else "assistant"
    return {"role": role, "content": msg.content}


def _build_system_prompt(doc_ids: list[str] | None = None) -> str:
    parts = ["你是一个专业的文档助手。"]
    if doc_ids:
        parts.append(f"用户指定参考的文档ID为: {', '.join(doc_ids)}。请基于这些文档内容回答问题。")
    parts.append("如果用户问题与文档相关，请使用 search_documents 工具搜索相关内容。")
    return "\n".join(parts)


def build_agent_graph():
    """构建 Agent 图"""

    def call_llm(state: AgentState) -> AgentState:
        client = create_client()
        messages = [_to_dict(m) for m in state["messages"]]

        doc_ids = state.get("tools_used", [])
        system_msg = {"role": "system", "content": _build_system_prompt(doc_ids if doc_ids else None)}
        messages = [system_msg] + messages

        response = client.chat(messages)
        return {
            "llm_response": response,
            "messages": [AIMessage(content=response)],
        }

    def call_tools(state: AgentState) -> AgentState:
        last_msg = state["messages"][-1] if state["messages"] else None
        if not last_msg or not hasattr(last_msg, "content"):
            return {"tool_result": ""}

        content = last_msg.content.lower()
        tools_used = []
        results = []

        # 简单启发式：包含关键词时调用工具
        keywords = ["文档", "搜索", "查找", "总结", "对比", "这份", "这些", "上传"]
        if any(kw in content for kw in keywords):
            for tool in available_tools:
                if isinstance(tool, BaseTool):
                    result = asyncio.run(tool.run(query=content))
                    results.append(result)
                    tools_used.append(tool.name)

        return {
            "tool_result": "\n".join(results) if results else "",
            "tools_used": tools_used,
        }

    def should_use_tools(state: AgentState) -> str:
        return "tools" if state.get("tools_used") else "end"

    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("tools", call_tools)
    graph.set_entry_point("llm")

    graph.add_conditional_edges(
        "llm",
        should_use_tools,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", END)

    return graph.compile()
