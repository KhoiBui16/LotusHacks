from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.models.user import UserInDB, UserPublic
from app.schemas.me import ChangePasswordRequest, OkResponse, UpdateMeRequest
from app.security.deps import get_current_user
from app.security.passwords import hash_password, verify_password

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserPublic)
async def get_me(user: Annotated[UserInDB, Depends(get_current_user)]) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        role=user.role,
        created_at=user.created_at,
    )


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UpdateMeRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> UserPublic:
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin profile editing is disabled")

    updates: dict = {}
    if payload.full_name is not None:
        updates["full_name"] = payload.full_name
    if payload.phone is not None:
        updates["phone"] = payload.phone
    if payload.avatar_url is not None:
        updates["avatar_url"] = payload.avatar_url

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        await db["users"].update_one({"_id": ObjectId(user.id)}, {"$set": updates})
        refreshed = await db["users"].find_one({"_id": ObjectId(user.id)})
        if not refreshed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user = UserInDB.from_mongo(refreshed)

    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/me/change-password", response_model=OkResponse)
async def change_password(
    payload: ChangePasswordRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password auth is not enabled for this account",
        )
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    await db["users"].update_one(
        {"_id": ObjectId(user.id)},
        {
            "$set": {
                "password_hash": hash_password(payload.new_password),
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return OkResponse()



