from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.models.settings import SettingsInDB
from app.models.user import UserInDB
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest
from app.security.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


async def get_or_create_settings(db: AsyncIOMotorDatabase, user_id: str) -> SettingsInDB:
    existing = await db["settings"].find_one({"user_id": ObjectId(user_id)})
    if existing:
        return SettingsInDB.from_mongo(existing)

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": ObjectId(user_id),
        "push_notif": True,
        "email_notif": True,
        "in_app_notif": True,
        "claim_updates": True,
        "doc_reminders": True,
        "marketing_emails": False,
        "preferred_contact": "email",
        "language": "en",
        "created_at": now,
        "updated_at": now,
    }
    result = await db["settings"].insert_one(doc)
    saved = await db["settings"].find_one({"_id": result.inserted_id})
    return SettingsInDB.from_mongo(saved)


@router.get("", response_model=SettingsResponse)
async def get_settings(
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> SettingsResponse:
    s = await get_or_create_settings(db, user.id)
    return SettingsResponse.model_validate(s.model_dump(exclude={"id", "user_id", "created_at", "updated_at"}))


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    payload: SettingsUpdateRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> SettingsResponse:
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    updates["updated_at"] = datetime.now(timezone.utc)
    await db["settings"].update_one({"user_id": ObjectId(user.id)}, {"$set": updates}, upsert=True)
    s = await get_or_create_settings(db, user.id)
    return SettingsResponse.model_validate(s.model_dump(exclude={"id", "user_id", "created_at", "updated_at"}))

