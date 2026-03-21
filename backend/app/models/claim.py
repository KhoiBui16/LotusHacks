from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ClaimStatus = Literal["draft", "processing", "needs-docs", "approved", "rejected", "closed"]
IncidentType = Literal["collision", "scratch", "glass", "flood", "theft", "other"]


class ClaimIncident(BaseModel):
    type: IncidentType
    date: str
    time: str | None = None
    location_text: str
    description: str | None = None
    has_third_party: bool = False
    third_party_info: str | None = None
    can_drive: bool = True
    needs_towing: bool = False
    has_injury: bool = False


class ClaimTimelineItem(BaseModel):
    at: datetime
    label: str
    status: Literal["done", "current", "pending"] = "pending"


class ClaimInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    vehicle_id: str

    insurer: str | None = None
    policy_id: str | None = None

    status: ClaimStatus = "draft"
    amount_value: float | None = None
    amount_currency: str | None = None

    incident: ClaimIncident | None = None
    timeline: list[ClaimTimelineItem] = []

    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "ClaimInDB":
        doc = {**doc}
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        doc["vehicle_id"] = str(doc["vehicle_id"])
        return cls.model_validate(doc)


class ClaimListItem(BaseModel):
    id: str
    type: str
    date: str
    vehicle_plate: str | None = None
    vehicle_id: str
    insurer: str | None = None
    status: ClaimStatus
    amount_value: float | None = None
    amount_currency: str | None = None
    updated_at: datetime

