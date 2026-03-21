from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


DocStatus = Literal["pending", "uploaded", "error", "valid", "invalid", "missing"]


class ClaimDocumentInDB(BaseModel):
    id: str = Field(alias="_id")
    claim_id: str
    doc_type: str
    required: bool = True
    status: DocStatus = "pending"
    note: str | None = None
    upload_id: str | None = None
    url: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "ClaimDocumentInDB":
        doc = {**doc}
        doc["_id"] = str(doc["_id"])
        doc["claim_id"] = str(doc["claim_id"])
        return cls.model_validate(doc)

