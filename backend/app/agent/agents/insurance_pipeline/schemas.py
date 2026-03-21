from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class PolicyInfo(BaseModel):
    policy_number: Optional[str] = None
    insurer: Optional[str] = None
    claimant_name: Optional[str] = None
    vehicle_type: Optional[str] = None
    plate_number: Optional[str] = None
    coverage_start: Optional[str] = None
    coverage_end: Optional[str] = None


class ClaimInfo(BaseModel):
    incident_type: str = "unknown"
    incident_time: Optional[str] = None
    incident_location: Optional[str] = None
    claimed_damage: List[str] = Field(default_factory=list)
    narrative: Optional[str] = None
    driver_has_license: Optional[bool] = None
    attachments_listed: List[str] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    file_name: str
    file_type: str
    num_chars: int
    cleaned_text: str
    policy: PolicyInfo
    claim: ClaimInfo


class Detection(BaseModel):
    label: str
    confidence: float
    bbox: List[float] = Field(default_factory=list)


class ImageAnalysis(BaseModel):
    image_path: str
    ran_model: bool = False
    model_name: Optional[str] = None

    vehicle_present: Optional[bool] = None
    vehicle_type: Optional[str] = None

    is_damage_visible: Optional[bool] = None
    damaged_parts: List[str] = Field(default_factory=list)
    severity: Optional[str] = None
    confidence: float = 0.0

    accident_scene_label: Optional[str] = None
    accident_scene_confidence: float = 0.0

    vehicle_labels: List[str] = Field(default_factory=list)
    detections: List[Detection] = Field(default_factory=list)

    crop_path: Optional[str] = None
    notes: List[str] = Field(default_factory=list)

class VerificationResult(BaseModel):
    decision: str
    reasons: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    score: float = 0.0

class DriverLicenseAnalysis(BaseModel):
    ran_ocr: bool = False
    full_name: Optional[str] = None
    license_class: Optional[str] = None
    is_expired: Optional[bool] = None
    notes: List[str] = Field(default_factory=list)