from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.models.notification import NotificationInDB, NotificationPublic
from app.models.user import UserInDB
from app.schemas.me import OkResponse
from app.security.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationPublic])
async def list_notifications(
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    tab: str | None = Query(default=None, alias="tab"),
) -> list[NotificationPublic]:
    query: dict = {"user_id": ObjectId(user.id)}
    if tab == "unread":
        query["read"] = False

    cursor = db["notifications"].find(query).sort("created_at", -1)
    out: list[NotificationPublic] = []
    async for doc in cursor:
        n = NotificationInDB.from_mongo(doc)
        out.append(
            NotificationPublic(
                id=n.id,
                type=n.type,
                title=n.title,
                message=n.message,
                claim_id=n.claim_id,
                read=n.read,
                created_at=n.created_at,
            )
        )
    return out


@router.post("/{notification_id}/read", response_model=OkResponse)
async def mark_read(
    notification_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    res = await db["notifications"].update_one(
        {"_id": ObjectId(notification_id), "user_id": ObjectId(user.id)},
        {"$set": {"read": True}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return OkResponse()


@router.post("/read-all", response_model=OkResponse)
async def read_all(
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    await db["notifications"].update_many({"user_id": ObjectId(user.id), "read": False}, {"$set": {"read": True}})
    return OkResponse()


@router.delete("/{notification_id}", response_model=OkResponse)
async def delete_notification(
    notification_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    res = await db["notifications"].delete_one({"_id": ObjectId(notification_id), "user_id": ObjectId(user.id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return OkResponse()

