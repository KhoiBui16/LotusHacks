from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserInDB(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    password_hash: str | None = None
    google_sub: str | None = None
    role: str = "user"
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "UserInDB":
        doc = {**doc}
        doc["_id"] = str(doc["_id"])
        doc.setdefault("role", "user")
        return cls.model_validate(doc)


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    role: str = "user"
    created_at: datetime
