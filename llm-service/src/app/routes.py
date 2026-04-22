import json
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agents.agent_graph import build_agent_graph
from src.agents.tools import available_tools
from src.clients.factory import create_client

router = APIRouter()

_graph = build_agent_graph()

# 会话存储
_conversations: dict[str, dict] = {}


class ConversationCreate(BaseModel):
    title: str = "新对话"


class ConversationItem(BaseModel):
    id: str
    title: str
    message_count: int


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    doc_ids: list[str] = []


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


@router.post("/conversations", response_model=ConversationItem)
async def create_conversation(req: ConversationCreate = ConversationCreate()):
    conv_id = str(uuid.uuid4())
    _conversations[conv_id] = {"title": req.title, "messages": [], "doc_ids": []}
    return ConversationItem(id=conv_id, title=req.title, message_count=0)


@router.get("/conversations", response_model=list[ConversationItem])
async def list_conversations():
    items = []
    for cid, data in _conversations.items():
        items.append(ConversationItem(
            id=cid,
            title=data["title"],
            message_count=len(data["messages"]),
        ))
    return items


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    if conversation_id in _conversations:
        del _conversations[conversation_id]
        return {"message": "deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.patch("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, body: dict):
    if conversation_id not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if "title" in body:
        _conversations[conversation_id]["title"] = body["title"]
    if "doc_ids" in body:
        _conversations[conversation_id]["doc_ids"] = body["doc_ids"]
    return {"message": "updated"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        create_client()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    conv_id = req.conversation_id or _new_conversation_id()
    if conv_id not in _conversations:
        _conversations[conv_id] = {"title": "新对话", "messages": [], "doc_ids": req.doc_ids}

    conv = _conversations[conv_id]
    conv["messages"].append({"role": "user", "content": req.message})

    messages = list(conv["messages"])
    doc_ids = req.doc_ids or conv.get("doc_ids", [])
    result = _graph.invoke({"messages": messages, "tools_used": doc_ids})

    assistant_msg = result.get("llm_response", "")
    conv["messages"].append({"role": "assistant", "content": assistant_msg})

    # 自动更新标题（首轮对话后）
    if len(conv["messages"]) == 2 and conv["title"] == "新对话":
        conv["title"] = req.message[:30] + ("..." if len(req.message) > 30 else "")

    return ChatResponse(reply=assistant_msg, conversation_id=conv_id)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_stream():
        try:
            create_client()
        except ValueError as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            return

        conv_id = req.conversation_id or _new_conversation_id()
        if conv_id not in _conversations:
            _conversations[conv_id] = {"title": "新对话", "messages": [], "doc_ids": req.doc_ids}

        conv = _conversations[conv_id]
        conv["messages"].append({"role": "user", "content": req.message})

        yield f"data: {json.dumps({'event': 'start', 'conversation_id': conv_id})}\n\n"

        full_reply = ""
        try:
            messages = list(conv["messages"])
            doc_ids = req.doc_ids or conv.get("doc_ids", [])
            # 直接调用 LLM（Agent 图的工具调用暂不适用于流式，后续升级）
            client = create_client()
            tool_result = ""
            # 先调用工具
            for tool in available_tools:
                content_lower = req.message.lower()
                keywords = ["文档", "搜索", "查找", "总结", "对比", "这份", "这些", "上传"]
                if any(kw in content_lower for kw in keywords):
                    tool_result = await tool.run(query=req.message)

            system_parts = ["你是一个专业的文档助手。"]
            if doc_ids:
                system_parts.append(f"用户指定参考的文档ID为: {', '.join(doc_ids)}。")
            if tool_result:
                system_parts.append(f"\n搜索到的文档内容：\n{tool_result}")
            messages_with_system = [{"role": "system", "content": "\n".join(system_parts)}] + messages
            async for chunk in client.chat_stream(messages_with_system):
                full_reply += chunk
                yield f"data: {json.dumps({'event': 'token', 'content': chunk})}\n\n"
        except RuntimeError as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            return

        conv["messages"].append({"role": "assistant", "content": full_reply})
        if len(conv["messages"]) == 2 and conv["title"] == "新对话":
            conv["title"] = req.message[:30] + ("..." if len(req.message) > 30 else "")
        yield f"data: {json.dumps({'event': 'end', 'conversation_id': conv_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _new_conversation_id() -> str:
    return str(uuid.uuid4())
