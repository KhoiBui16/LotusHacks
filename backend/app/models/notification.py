from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


NotificationType = Literal["status", "docs", "decision", "info"]


class NotificationInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    type: NotificationType = "info"
    title: str
    message: str
    claim_id: str | None = None
    read: bool = False
    created_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "NotificationInDB":
        doc = {**doc}
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        if doc.get("claim_id") is not None:
            doc["claim_id"] = str(doc["claim_id"])
        return cls.model_validate(doc)


class NotificationPublic(BaseModel):
    id: str
    type: NotificationType
    title: str
    message: str
    claim_id: str | None = None
    read: bool
    created_at: datetime

