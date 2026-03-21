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


class PolicyImportRequest(BaseModel):
    policy_id: str = Field(min_length=3, max_length=64)
    insurer: str = Field(min_length=2, max_length=120)
    effective_date: str | None = None
    expiry: str | None = None
    source: Literal["ocr", "manual", "upload"] = "manual"


class PolicyImportResponse(BaseModel):
    claim_id: str
    policy_linked: bool
    policy_id: str | None = None
    insurer: str | None = None
    source: str


class TriageResponse(BaseModel):
    claim_id: str
    risk_level: Literal["low", "medium", "high"]
    assisted_mode: bool
    reasons: list[str] = []


class CoverageCheckResponse(BaseModel):
    policy_active: bool
    has_policy: bool
    likely_excluded: bool
    deductible_notice: str | None = None


class EligibilityResponse(BaseModel):
    claim_id: str
    outcome: Literal["assisted_required", "likely_covered", "low_value_or_excluded"]
    coverage: CoverageCheckResponse
    next_action: Literal["assisted", "chat", "review", "exit"]
    notes: list[str] = []
    advice_text: str | None = None
    recommended_actions: list[str] = []
    save_draft_available: bool = False
    end_flow_available: bool = False


class FirstNoticeRequest(BaseModel):
    emergency_contacted: bool = False
    kept_scene: bool = False
    initial_evidence_collected: bool = False
    notes: str | None = Field(default=None, max_length=2000)


class FirstNoticeResponse(BaseModel):
    claim_id: str
    captured: bool
    message: str


class DossierResponse(BaseModel):
    claim_id: str
    summary: str
    timeline: list[ValidationResultItem] = []
    attachments_count: int
    completeness: Literal["complete", "partial"]


class SubmitRouterRequest(BaseModel):
    channel: Literal["api", "email", "portal"] = "api"


class SubmitRouterResponse(BaseModel):
    claim_id: str
    channel: Literal["api", "email", "portal"]
    external_ref: str
    status: Literal["received", "queued"]


class ClaimAppealRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)


class ClaimAppealResponse(BaseModel):
    claim_id: str
    appealed: bool
    message: str


class ClaimChatBootstrapResponse(BaseModel):
    claim_id: str
    session_id: str
    title: str
    reused: bool = False


class ClaimAdviceActionRequest(BaseModel):
    action: Literal["save_draft", "end_flow"]


class ClaimAdviceActionResponse(BaseModel):
    claim_id: str
    status: ClaimStatus
    message: str
