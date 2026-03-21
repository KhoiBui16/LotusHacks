from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class VehicleInDB(BaseModel):
    id: str = Field(alias="_id")
    user_id: str

    no_plate_yet: bool = False
    plate: str | None = None
    model: str
    year: int
    color: str
    vehicle_type: str
    seats: int | None = None
    weight_tons: float | None = None
    chassis_number: str | None = None
    engine_number: str | None = None
    usage: Literal["personal", "commercial"] = "personal"

    buyer_type: Literal["individual", "business"] = "individual"
    buyer_name: str | None = None
    buyer_dob: str | None = None
    buyer_age: int | None = None
    buyer_gender: str | None = None
    buyer_phone: str | None = None
    buyer_email: str | None = None
    buyer_id_number: str | None = None
    buyer_address: str | None = None

    owner_same_as_buyer: bool = True
    owner_name: str | None = None
    owner_phone: str | None = None
    owner_email: str | None = None
    owner_address: str | None = None

    policy_linked: bool = False
    policy_id: str | None = None
    insurer: str | None = None
    effective_date: str | None = None
    expiry: str | None = None
    insurance_years: int | None = None
    premium_amount: float | None = None
    premium_currency: str | None = None
    additional_benefits: list[str] = []

    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> "VehicleInDB":
        doc = {**doc}
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        return cls.model_validate(doc)


class VehicleSummary(BaseModel):
    id: str
    plate: str | None
    model: str
    year: int
    color: str
    vehicle_type: str
    policy_linked: bool
    insurer: str | None = None
    policy_id: str | None = None
    expiry: str | None = None
    claims_count: int = 0
    created_at: datetime

