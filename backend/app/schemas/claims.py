from typing import Literal

from pydantic import BaseModel, Field

from app.models.claim import ClaimIncident, ClaimStatus


class ClaimCreateRequest(BaseModel):
    vehicle_id: str
    policy_id: str | None = Field(default=None, max_length=64)
    insurer: str | None = Field(default=None, max_length=120)


class ClaimUpdateRequest(BaseModel):
    insurer: str | None = Field(default=None, max_length=120)
    policy_id: str | None = Field(default=None, max_length=64)
    status: ClaimStatus | None = None
    incident: ClaimIncident | None = None


class ClaimSubmitRequest(BaseModel):
    consent: bool = True


class RequiredDoc(BaseModel):
    doc_type: str
    required: bool = True
    title: str
    mime_allowed: list[str] = []
    max_size_mb: int = 20


class AttachDocumentRequest(BaseModel):
    doc_type: str = Field(min_length=2, max_length=64)
    upload_id: str = Field(min_length=6, max_length=64)


DocStatus = Literal["pending", "uploaded", "error", "valid", "invalid", "missing"]


class ClaimDocumentResponse(BaseModel):
    id: str
    claim_id: str
    doc_type: str
    required: bool
    status: Literal["pending", "uploaded", "error", "valid", "invalid", "missing"]
    note: str | None = None
    upload_id: str | None = None
    url: str | None = None


class ValidationResultItem(BaseModel):
    doc_type: str
    status: Literal["valid", "invalid", "missing"]
    note: str | None = None


class ValidationResponse(BaseModel):
    overall: Literal["ok", "issues"]
    results: list[ValidationResultItem]
