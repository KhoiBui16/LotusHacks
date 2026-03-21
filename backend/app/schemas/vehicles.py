from typing import Literal

from pydantic import BaseModel, Field


class VehicleCreateRequest(BaseModel):
    no_plate_yet: bool = False
    plate: str | None = Field(default=None, max_length=32)
    model: str = Field(min_length=1, max_length=120)
    year: int = Field(ge=1900, le=2100)
    color: str = Field(min_length=1, max_length=60)
    vehicle_type: str = Field(min_length=1, max_length=80)
    seats: int | None = Field(default=None, ge=1, le=200)
    weight_tons: float | None = Field(default=None, ge=0)
    chassis_number: str | None = Field(default=None, max_length=80)
    engine_number: str | None = Field(default=None, max_length=80)
    usage: Literal["personal", "commercial"] = "personal"

    buyer_type: Literal["individual", "business"] = "individual"
    buyer_name: str | None = Field(default=None, max_length=120)
    buyer_dob: str | None = Field(default=None, max_length=32)
    buyer_age: int | None = Field(default=None, ge=0, le=150)
    buyer_gender: str | None = Field(default=None, max_length=32)
    buyer_phone: str | None = Field(default=None, max_length=32)
    buyer_email: str | None = Field(default=None, max_length=254)
    buyer_id_number: str | None = Field(default=None, max_length=64)
    buyer_address: str | None = Field(default=None, max_length=255)

    owner_same_as_buyer: bool = True
    owner_name: str | None = Field(default=None, max_length=120)
    owner_phone: str | None = Field(default=None, max_length=32)
    owner_email: str | None = Field(default=None, max_length=254)
    owner_address: str | None = Field(default=None, max_length=255)


class VehicleUpdateRequest(BaseModel):
    no_plate_yet: bool | None = None
    plate: str | None = Field(default=None, max_length=32)
    model: str | None = Field(default=None, max_length=120)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=60)
    vehicle_type: str | None = Field(default=None, max_length=80)
    seats: int | None = Field(default=None, ge=1, le=200)
    weight_tons: float | None = Field(default=None, ge=0)
    chassis_number: str | None = Field(default=None, max_length=80)
    engine_number: str | None = Field(default=None, max_length=80)
    usage: Literal["personal", "commercial"] | None = None

    buyer_type: Literal["individual", "business"] | None = None
    buyer_name: str | None = Field(default=None, max_length=120)
    buyer_dob: str | None = Field(default=None, max_length=32)
    buyer_age: int | None = Field(default=None, ge=0, le=150)
    buyer_gender: str | None = Field(default=None, max_length=32)
    buyer_phone: str | None = Field(default=None, max_length=32)
    buyer_email: str | None = Field(default=None, max_length=254)
    buyer_id_number: str | None = Field(default=None, max_length=64)
    buyer_address: str | None = Field(default=None, max_length=255)

    owner_same_as_buyer: bool | None = None
    owner_name: str | None = Field(default=None, max_length=120)
    owner_phone: str | None = Field(default=None, max_length=32)
    owner_email: str | None = Field(default=None, max_length=254)
    owner_address: str | None = Field(default=None, max_length=255)

    policy_linked: bool | None = None
    policy_id: str | None = Field(default=None, max_length=64)
    insurer: str | None = Field(default=None, max_length=120)
    effective_date: str | None = Field(default=None, max_length=32)
    expiry: str | None = Field(default=None, max_length=32)
    insurance_years: int | None = Field(default=None, ge=0, le=50)
    premium_amount: float | None = Field(default=None, ge=0)
    premium_currency: str | None = Field(default=None, max_length=8)
    additional_benefits: list[str] | None = None


class PolicyLinkRequest(BaseModel):
    policy_id: str | None = Field(default=None, max_length=64)
    insurer: str | None = Field(default=None, max_length=120)
    effective_date: str | None = Field(default=None, max_length=32)
    expiry: str | None = Field(default=None, max_length=32)

