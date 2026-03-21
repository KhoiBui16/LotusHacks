from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.models.claim_document import ClaimDocumentInDB
from app.models.claim import ClaimInDB, ClaimTimelineItem
from app.models.user import UserInDB
from app.schemas.admin import (
    AdminClaimListItem,
    AdminClaimStatusUpdateRequest,
    AdminUserPasswordChangeRequest,
)
from app.schemas.claims import ClaimDocumentResponse
from app.schemas.me import OkResponse
from app.security.deps import get_current_admin
from app.security.passwords import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])

_ALLOWED_STATUSES = {"draft", "processing", "needs-docs", "approved", "rejected", "closed"}


@router.get("/claims", response_model=list[AdminClaimListItem])
async def admin_list_claims(
    admin: Annotated[UserInDB, Depends(get_current_admin)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, alias="q"),
) -> list[AdminClaimListItem]:
    del admin
    query: dict = {}
    if status_filter:
        query["status"] = status_filter

    cursor = db["claims"].find(query).sort("updated_at", -1)
    items: list[AdminClaimListItem] = []
    async for doc in cursor:
        claim = ClaimInDB.from_mongo(doc)
        user_doc = await db["users"].find_one({"_id": ObjectId(claim.user_id)})
        if not user_doc:
            continue
        vehicle_doc = await db["vehicles"].find_one({"_id": ObjectId(claim.vehicle_id)})
        plate = vehicle_doc.get("plate") if vehicle_doc else None
        claim_type = claim.incident.type if claim.incident else "claim"
        claim_date = claim.incident.date if claim.incident else claim.created_at.date().isoformat()

        item = AdminClaimListItem(
            id=claim.id,
            type=str(claim_type),
            date=str(claim_date),
            vehicle_plate=plate,
            vehicle_id=claim.vehicle_id,
            insurer=claim.insurer,
            status=claim.status,
            amount_value=claim.amount_value,
            amount_currency=claim.amount_currency,
            updated_at=claim.updated_at,
            user_id=claim.user_id,
            user_email=user_doc.get("email", "unknown@example.com"),
            user_name=user_doc.get("full_name", "Unknown user"),
        )
        if q:
            hay = f"{item.id} {item.user_email} {item.user_name} {item.type} {item.vehicle_plate or ''} {item.insurer or ''}".lower()
            if q.lower() not in hay:
                continue
        items.append(item)
    return items


@router.get("/claims/{claim_id}", response_model=ClaimInDB)
async def admin_get_claim(
    claim_id: str,
    admin: Annotated[UserInDB, Depends(get_current_admin)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    del admin
    try:
        claim_oid = ObjectId(claim_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    doc = await db["claims"].find_one({"_id": claim_oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return ClaimInDB.from_mongo(doc)


@router.get("/claims/{claim_id}/timeline", response_model=list[ClaimTimelineItem])
async def admin_get_claim_timeline(
    claim_id: str,
    admin: Annotated[UserInDB, Depends(get_current_admin)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[ClaimTimelineItem]:
    del admin
    try:
        claim_oid = ObjectId(claim_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    doc = await db["claims"].find_one({"_id": claim_oid}, {"timeline": 1})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return [ClaimTimelineItem.model_validate(i) for i in doc.get("timeline", [])]


@router.get("/claims/{claim_id}/documents", response_model=list[ClaimDocumentResponse])
async def admin_get_claim_documents(
    claim_id: str,
    admin: Annotated[UserInDB, Depends(get_current_admin)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[ClaimDocumentResponse]:
    del admin
    try:
        claim_oid = ObjectId(claim_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    claim = await db["claims"].find_one({"_id": claim_oid}, {"_id": 1})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    out: list[ClaimDocumentResponse] = []
    async for doc in db["claim_documents"].find({"claim_id": claim_oid}).sort("doc_type", 1):
        d = ClaimDocumentInDB.from_mongo(doc)
        out.append(
            ClaimDocumentResponse(
                id=d.id,
                claim_id=d.claim_id,
                doc_type=d.doc_type,
                required=d.required,
                status=d.status,
                note=d.note,
                upload_id=d.upload_id,
                url=d.url,
            )
        )
    return out


@router.post("/claims/{claim_id}/status", response_model=OkResponse)
async def admin_update_claim_status(
    claim_id: str,
    payload: AdminClaimStatusUpdateRequest,
    admin: Annotated[UserInDB, Depends(get_current_admin)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    if payload.status not in _ALLOWED_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim status")

    try:
        claim_oid = ObjectId(claim_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    claim_doc = await db["claims"].find_one({"_id": claim_oid})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = ClaimInDB.from_mongo(claim_doc)
    now = datetime.now(timezone.utc)
    timeline = [ClaimTimelineItem.model_validate(i).model_dump() for i in claim.timeline]
    for i in timeline:
        if i.get("status") == "current":
            i["status"] = "done"
    note_suffix = f" ({payload.note})" if payload.note else ""
    timeline.append(
        {
            "at": now,
            "label": f"Admin {admin.full_name} set status to {payload.status}{note_suffix}",
            "status": "current",
        }
    )

    await db["claims"].update_one(
        {"_id": claim_oid},
        {"$set": {"status": payload.status, "timeline": timeline, "updated_at": now}},
    )

    await db["notifications"].insert_one(
        {
            "user_id": ObjectId(claim.user_id),
            "type": "status",
            "title": "Claim status updated",
            "message": f"Your claim {claim.id[-8:]} is now '{payload.status}'.",
            "claim_id": claim_oid,
            "read": False,
            "created_at": now,
        }
    )
    return OkResponse()


@router.delete("/claims/{claim_id}", response_model=OkResponse)
async def admin_delete_claim(
    claim_id: str,
    admin: Annotated[UserInDB, Depends(get_current_admin)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    del admin
    try:
        claim_oid = ObjectId(claim_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    claim_doc = await db["claims"].find_one({"_id": claim_oid}, {"_id": 1})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    await db["claim_documents"].delete_many({"claim_id": claim_oid})
    await db["notifications"].delete_many({"claim_id": claim_oid})
    await db["claims"].delete_one({"_id": claim_oid})
    return OkResponse()


@router.post("/users/change-password", response_model=OkResponse)
async def admin_change_user_password(
    payload: AdminUserPasswordChangeRequest,
    admin: Annotated[UserInDB, Depends(get_current_admin)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    del admin
    user_doc = await db["users"].find_one({"email": payload.email.lower()})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db["users"].update_one(
        {"_id": user_doc["_id"]},
        {"$set": {"password_hash": hash_password(payload.new_password), "updated_at": datetime.now(timezone.utc)}},
    )
    return OkResponse()
