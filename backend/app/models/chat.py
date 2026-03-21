from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        arbitrary_types_allowed = True


class ChatSession(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    title: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True

    @staticmethod
    def from_mongo(doc: dict) -> "ChatSession":
        if doc is None:
            return None
        doc["id"] = str(doc.get("_id", ""))
        return ChatSession(**doc)


class ChatSessionInDB(ChatSession):
    pass


class ChatMessageRequest(BaseModel):
    content: str


class ChatResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ChatSessionListItem(BaseModel):
    id: str
    title: str
    updated_at: str


class ChatSessionDetail(BaseModel):
    id: str
    title: str
    messages: list[ChatResponse]
    created_at: str
    updated_at: str
