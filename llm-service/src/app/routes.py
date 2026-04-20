import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.clients.factory import create_client
from src.graph.chat_graph import build_chat_graph

router = APIRouter()

# 简易内存会话存储（后续可替换为 Redis/DB）
_conversations: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """同步对话端点"""
    try:
        client = create_client()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    conv_id = req.conversation_id or _new_conversation_id()
    messages = _conversations.setdefault(conv_id, [])
    messages.append({"role": "user", "content": req.message})

    graph = build_chat_graph(client)
    result = graph.invoke({"messages": messages})

    assistant_msg = result.get("llm_response", "")
    messages.append({"role": "assistant", "content": assistant_msg})

    return ChatResponse(reply=assistant_msg, conversation_id=conv_id)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE 流式对话端点"""

    async def event_stream():
        try:
            client = create_client()
        except ValueError as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            return

        conv_id = req.conversation_id or _new_conversation_id()
        messages = _conversations.setdefault(conv_id, [])
        messages.append({"role": "user", "content": req.message})

        yield f"data: {json.dumps({'event': 'start', 'conversation_id': conv_id})}\n\n"

        full_reply = ""
        try:
            async for chunk in client.chat_stream(messages):
                full_reply += chunk
                yield f"data: {json.dumps({'event': 'token', 'content': chunk})}\n\n"
        except RuntimeError as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            return

        messages.append({"role": "assistant", "content": full_reply})
        yield f"data: {json.dumps({'event': 'end', 'conversation_id': conv_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _new_conversation_id() -> str:
    import uuid
    return str(uuid.uuid4())
