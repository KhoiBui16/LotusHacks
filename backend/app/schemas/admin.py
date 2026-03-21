from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminClaimListItem(BaseModel):
    id: str
    type: str
    date: str
    vehicle_plate: str | None = None
    vehicle_id: str
    insurer: str | None = None
    status: str
    amount_value: float | None = None
    amount_currency: str | None = None
    updated_at: datetime
    user_id: str
    user_email: EmailStr
    user_name: str


class AdminClaimStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=3, max_length=32)
    note: str | None = Field(default=None, max_length=500)


class AdminUserPasswordChangeRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8, max_length=128)
