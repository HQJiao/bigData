import json
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.agents.agent_graph import build_agent_graph
from src.agents.tools import available_tools
from src.clients.factory import create_client
from src.app.database import get_db
from src.app.models import Conversation

router = APIRouter()

_graph = build_agent_graph()


class ConversationCreate(BaseModel):
    title: str = "新对话"


class ConversationItem(BaseModel):
    id: str
    title: str
    message_count: int


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[dict]


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    doc_ids: list[str] = []


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


def _get_conv(db: Session, conv_id: str) -> Conversation:
    try:
        uid = uuid.UUID(conv_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv = db.query(Conversation).filter(Conversation.id == uid).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.post("/conversations", response_model=ConversationItem)
async def create_conversation(req: ConversationCreate = ConversationCreate(), db: Session = Depends(get_db)):
    conv_id = uuid.uuid4()
    conv = Conversation(id=conv_id, title=req.title, messages=[], doc_ids=[], message_count=0)
    db.add(conv)
    db.commit()
    return ConversationItem(id=str(conv_id), title=req.title, message_count=0)


@router.get("/conversations", response_model=list[ConversationItem])
async def list_conversations(db: Session = Depends(get_db)):
    convs = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    return [ConversationItem(id=str(c.id), title=c.title, message_count=c.message_count) for c in convs]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = _get_conv(db, conversation_id)
    return ConversationDetail(id=str(conv.id), title=conv.title, messages=conv.messages)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = _get_conv(db, conversation_id)
    db.delete(conv)
    db.commit()
    return {"message": "deleted"}


@router.patch("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, body: dict, db: Session = Depends(get_db)):
    conv = _get_conv(db, conversation_id)
    if "title" in body:
        conv.title = body["title"]
    if "doc_ids" in body:
        conv.doc_ids = body["doc_ids"]
    db.commit()
    return {"message": "updated"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        create_client()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if req.conversation_id:
        conv = _get_conv(db, req.conversation_id)
    else:
        conv_id = uuid.uuid4()
        conv = Conversation(id=conv_id, title="新对话", messages=[], doc_ids=req.doc_ids, message_count=0)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    conv.messages = conv.messages or []
    conv.messages.append({"role": "user", "content": req.message})

    doc_ids = req.doc_ids or conv.doc_ids or []
    result = _graph.invoke({"messages": list(conv.messages), "tools_used": doc_ids})

    assistant_msg = result.get("llm_response", "")
    conv.messages.append({"role": "assistant", "content": assistant_msg})
    conv.message_count = len(conv.messages)

    if conv.message_count == 2 and conv.title == "新对话":
        conv.title = req.message[:30] + ("..." if len(req.message) > 30 else "")

    db.commit()
    return ChatResponse(reply=assistant_msg, conversation_id=str(conv.id))


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    async def event_stream():
        try:
            create_client()
        except ValueError as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
            return

        if req.conversation_id:
            conv = _get_conv(db, req.conversation_id)
        else:
            conv_id = uuid.uuid4()
            conv = Conversation(id=conv_id, title="新对话", messages=[], doc_ids=req.doc_ids, message_count=0)
            db.add(conv)
            db.commit()
            db.refresh(conv)

        conv_id = str(conv.id)
        conv.messages = conv.messages or []
        conv.messages.append({"role": "user", "content": req.message})
        db.commit()

        yield f"data: {json.dumps({'event': 'start', 'conversation_id': conv_id})}\n\n"

        full_reply = ""
        try:
            messages = list(conv.messages)
            doc_ids = req.doc_ids or conv.doc_ids or []
            client = create_client()
            tool_result = ""
            for tool in available_tools:
                content_lower = req.message.lower()
                keywords = ["文档", "搜索", "查找", "总结", "对比", "这份", "这些", "上传"]
                if any(kw in content_lower for kw in keywords) or doc_ids:
                    tool_result = await tool.run(query=req.message, doc_ids=doc_ids)

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

        conv.messages.append({"role": "assistant", "content": full_reply})
        conv.message_count = len(conv.messages)
        if conv.message_count == 2 and conv.title == "新对话":
            conv.title = req.message[:30] + ("..." if len(req.message) > 30 else "")
        db.commit()
        yield f"data: {json.dumps({'event': 'end', 'conversation_id': conv_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
