from datetime import datetime, timezone
from typing import Annotated
import os

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

from app.security.deps import get_current_user
from app.db import get_db
from app.models.user import UserInDB
from app.models.chat import (
    ChatMessageRequest,
    ChatResponse,
    ChatSession,
    ChatSessionCreateRequest,
    ChatSessionDetail,
    ChatSessionListItem,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_openai_client() -> OpenAI:
    """Khởi tạo OpenAI client theo env hiện tại."""
    if OpenAI is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is unavailable: openai package is not installed",
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is unavailable: OPENAI_API_KEY is not configured",
        )

    return OpenAI(api_key=api_key)


async def generate_session_title(user_message: str) -> str:
    """Generate a title from the first user message"""
    title = user_message[:50]
    if len(user_message) > 50:
        title += "..."
    return title


@router.post("/sessions", response_model=ChatSessionListItem)
async def create_chat_session(
    payload: ChatSessionCreateRequest | None,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ChatSessionListItem:
    """Create a new chat session"""
    payload = payload or ChatSessionCreateRequest()
    user_oid = ObjectId(user.id)

    claim_id = payload.claim_id.strip() if payload.claim_id else None
    workflow_stage = payload.workflow_stage.strip() if payload.workflow_stage else None
    context_seed = payload.context_seed.strip() if payload.context_seed else None

    if claim_id:
        try:
            claim_obj_id = ObjectId(claim_id)
        except InvalidId:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

        claim = await db["claims"].find_one({"_id": claim_obj_id, "user_id": user_oid}, {"_id": 1})
        if not claim:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

        existing = await db["chat_sessions"].find_one(
            {
                "user_id": user_oid,
                "claim_id": claim_id,
                "workflow_stage": workflow_stage or "claim_guidance",
            }
        )
        if existing:
            updates = {"updated_at": datetime.now(timezone.utc)}
            if context_seed:
                updates["context_seed"] = context_seed
            if payload.title:
                updates["title"] = payload.title

            if len(updates) > 1:
                await db["chat_sessions"].update_one(
                    {"_id": existing["_id"], "user_id": user_oid},
                    {"$set": updates},
                )
                existing.update(updates)

            return ChatSessionListItem(
                id=str(existing["_id"]),
                title=existing.get("title", "New Chat"),
                updated_at=existing.get("updated_at", existing.get("created_at")).isoformat(),
                claim_id=existing.get("claim_id"),
                workflow_stage=existing.get("workflow_stage"),
            )

    now = datetime.now(timezone.utc)
    session_doc = {
        "user_id": user_oid,
        "title": payload.title or "New Chat",
        "claim_id": claim_id,
        "workflow_stage": workflow_stage,
        "context_seed": context_seed,
        "seeded_from_eligibility": payload.seeded_from_eligibility,
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db["chat_sessions"].insert_one(session_doc)
    
    return ChatSessionListItem(
        id=str(result.inserted_id),
        title=session_doc["title"],
        updated_at=now.isoformat(),
        claim_id=claim_id,
        workflow_stage=workflow_stage,
    )


@router.get("/sessions", response_model=list[ChatSessionListItem])
async def list_chat_sessions(
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[ChatSessionListItem]:
    """Get list of user's chat sessions"""
    sessions = await db["chat_sessions"].find(
        {"user_id": ObjectId(user.id)}
    ).sort("updated_at", -1).to_list(None)
    
    return [
        ChatSessionListItem(
            id=str(s["_id"]),
            title=s.get("title", "New Chat"),
            updated_at=s.get("updated_at", s.get("created_at")).isoformat(),
            claim_id=s.get("claim_id"),
            workflow_stage=s.get("workflow_stage"),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_chat_session(
    session_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ChatSessionDetail:
    """Get a specific chat session with all messages"""
    try:
        session_obj_id = ObjectId(session_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
    
    session = await db["chat_sessions"].find_one(
        {"_id": session_obj_id, "user_id": ObjectId(user.id)}
    )
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    messages = [
        ChatResponse(
            id=str(i),
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            created_at=msg.get("created_at", "").isoformat() if isinstance(msg.get("created_at"), datetime) else msg.get("created_at", ""),
        )
        for i, msg in enumerate(session.get("messages", []))
    ]
    
    return ChatSessionDetail(
        id=str(session["_id"]),
        title=session.get("title", "Chat"),
        claim_id=session.get("claim_id"),
        workflow_stage=session.get("workflow_stage"),
        messages=messages,
        created_at=session.get("created_at", "").isoformat() if isinstance(session.get("created_at"), datetime) else session.get("created_at", ""),
        updated_at=session.get("updated_at", "").isoformat() if isinstance(session.get("updated_at"), datetime) else session.get("updated_at", ""),
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatSessionDetail)
async def send_message(
    session_id: str,
    payload: ChatMessageRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ChatSessionDetail:
    """Send a message and get LLM response"""
    client = _get_openai_client()

    try:
        session_obj_id = ObjectId(session_id)
        user_obj_id = ObjectId(user.id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
    
    session = await db["chat_sessions"].find_one(
        {"_id": session_obj_id, "user_id": user_obj_id}
    )
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Add user message
    now = datetime.now(timezone.utc)
    user_message = {
        "role": "user",
        "content": payload.content,
        "created_at": now,
    }
    
    messages = session.get("messages", [])
    messages.append(user_message)
    
    # Generate LLM response
    try:
        llm_messages = []
        context_seed = session.get("context_seed")
        if context_seed:
            llm_messages.append({"role": "system", "content": context_seed})
        llm_messages.extend(
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in messages
        )

        response = client.chat.completions.create(
            model=os.getenv("CHAT_LLM_MODEL", "gpt-4o-mini"),
            messages=llm_messages,
            temperature=0.7,
        )

        assistant_content = response.choices[0].message.content or ""
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )
    
    # Add assistant message
    assistant_message = {
        "role": "assistant",
        "content": assistant_content,
        "created_at": datetime.now(timezone.utc),
    }
    messages.append(assistant_message)
    
    # Update session with new messages and title if first message
    update_data = {
        "messages": messages,
        "updated_at": datetime.now(timezone.utc),
    }
    
    if len(messages) == 2:  # First exchange
        update_data["title"] = await generate_session_title(payload.content)
    
    await db["chat_sessions"].update_one(
        {"_id": session_obj_id, "user_id": user_obj_id},
        {"$set": update_data},
    )
    
    # Return updated session
    updated_session = await db["chat_sessions"].find_one(
        {"_id": session_obj_id, "user_id": user_obj_id}
    )
    
    msg_list = [
        ChatResponse(
            id=str(i),
            role=msg.get("role", "user"),
            content=msg.get("content", ""),
            created_at=msg.get("created_at", "").isoformat() if isinstance(msg.get("created_at"), datetime) else msg.get("created_at", ""),
        )
        for i, msg in enumerate(updated_session.get("messages", []))
    ]
    
    return ChatSessionDetail(
        id=str(updated_session["_id"]),
        title=updated_session.get("title", "Chat"),
        claim_id=updated_session.get("claim_id"),
        workflow_stage=updated_session.get("workflow_stage"),
        messages=msg_list,
        created_at=updated_session.get("created_at", "").isoformat() if isinstance(updated_session.get("created_at"), datetime) else updated_session.get("created_at", ""),
        updated_at=updated_session.get("updated_at", "").isoformat() if isinstance(updated_session.get("updated_at"), datetime) else updated_session.get("updated_at", ""),
    )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> dict:
    """Delete a chat session"""
    try:
        session_obj_id = ObjectId(session_id)
        user_obj_id = ObjectId(user.id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session id")
    
    result = await db["chat_sessions"].delete_one(
        {"_id": session_obj_id, "user_id": user_obj_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    return {"ok": True}
