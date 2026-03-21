from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


UploadPurpose = Literal["claim_doc", "policy_doc", "avatar", "other"]


class UploadInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    filename: str
    content_type: str
    size_bytes: int
    purpose: UploadPurpose = "other"
    url: str
    created_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "UploadInDB":
        doc = {**doc}
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        return cls.model_validate(doc)

