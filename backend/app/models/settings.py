from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


PreferredContact = Literal["email", "phone", "chat"]


class SettingsInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    push_notif: bool = True
    email_notif: bool = True
    in_app_notif: bool = True
    claim_updates: bool = True
    doc_reminders: bool = True
    marketing_emails: bool = False
    preferred_contact: PreferredContact = "email"
    language: str = "en"
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "SettingsInDB":
        doc = {**doc}
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        return cls.model_validate(doc)


class SettingsPublic(BaseModel):
    push_notif: bool
    email_notif: bool
    in_app_notif: bool
    claim_updates: bool
    doc_reminders: bool
    marketing_emails: bool
    preferred_contact: PreferredContact
    language: str

