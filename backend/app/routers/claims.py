from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.models.claim import ClaimInDB, ClaimListItem, ClaimTimelineItem
from app.models.claim_document import ClaimDocumentInDB
from app.models.user import UserInDB
from app.schemas.claims import (
    AttachDocumentRequest,
    ClaimCreateRequest,
    ClaimDocumentResponse,
    ClaimSubmitRequest,
    ClaimUpdateRequest,
    RequiredDoc,
    ValidationResponse,
    ValidationResultItem,
)
from app.schemas.me import OkResponse
from app.security.deps import get_current_user

router = APIRouter(prefix="/claims", tags=["claims"])


def required_docs() -> list[RequiredDoc]:
    return [
        RequiredDoc(
            doc_type="vehicle-overall",
            title="Vehicle overall",
            mime_allowed=["image/jpeg", "image/png"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="damage-closeup",
            title="Damage close-up",
            mime_allowed=["image/jpeg", "image/png"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="scene",
            title="Scene photo",
            mime_allowed=["image/jpeg", "image/png"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="registration",
            title="Vehicle registration",
            mime_allowed=["image/jpeg", "image/png", "application/pdf"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="driver-license",
            title="Driver license",
            mime_allowed=["image/jpeg", "image/png", "application/pdf"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="insurance-cert",
            title="Insurance certificate",
            mime_allowed=["image/jpeg", "image/png", "application/pdf"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="police-report",
            title="Police report",
            mime_allowed=["image/jpeg", "image/png", "application/pdf"],
            max_size_mb=20,
        ),
    ]


async def ensure_required_doc_stubs(db: AsyncIOMotorDatabase, claim_id: ObjectId) -> None:
    now = datetime.now(timezone.utc)
    for d in required_docs():
        await db["claim_documents"].update_one(
            {"claim_id": claim_id, "doc_type": d.doc_type},
            {
                "$setOnInsert": {
                    "required": d.required,
                    "status": "missing",
                    "note": None,
                    "upload_id": None,
                    "url": None,
                    "created_at": now,
                },
                "$set": {"updated_at": now},
            },
            upsert=True,
        )


@router.get("", response_model=list[ClaimListItem])
async def list_claims(
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    status_filter: str | None = Query(default=None, alias="status"),
    vehicle_id: str | None = Query(default=None, alias="vehicle_id"),
    q: str | None = Query(default=None, alias="q"),
) -> list[ClaimListItem]:
    query: dict = {"user_id": ObjectId(user.id)}
    if status_filter:
        query["status"] = status_filter
    if vehicle_id:
        query["vehicle_id"] = ObjectId(vehicle_id)

    cursor = db["claims"].find(query).sort("updated_at", -1)
    vehicles = db["vehicles"]
    items: list[ClaimListItem] = []
    async for doc in cursor:
        c = ClaimInDB.from_mongo(doc)
        v = await vehicles.find_one({"_id": ObjectId(c.vehicle_id), "user_id": ObjectId(user.id)})
        plate = v.get("plate") if v else None
        claim_type = c.incident.type if c.incident else "claim"
        claim_date = c.incident.date if c.incident else c.created_at.date().isoformat()
        item = ClaimListItem(
            id=c.id,
            type=str(claim_type),
            date=str(claim_date),
            vehicle_plate=plate,
            vehicle_id=c.vehicle_id,
            insurer=c.insurer,
            status=c.status,
            amount_value=c.amount_value,
            amount_currency=c.amount_currency,
            updated_at=c.updated_at,
        )
        if q:
            hay = f"{item.type} {item.date} {item.vehicle_plate or ''} {item.insurer or ''}".lower()
            if q.lower() not in hay:
                continue
        items.append(item)
    return items


@router.post("", response_model=ClaimInDB, status_code=status.HTTP_201_CREATED)
async def create_claim(
    payload: ClaimCreateRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    vehicle = await db["vehicles"].find_one({"_id": ObjectId(payload.vehicle_id), "user_id": ObjectId(user.id)})
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": ObjectId(user.id),
        "vehicle_id": ObjectId(payload.vehicle_id),
        "insurer": payload.insurer,
        "policy_id": payload.policy_id,
        "status": "draft",
        "amount_value": None,
        "amount_currency": None,
        "incident": None,
        "timeline": [
            {"at": now, "label": "Draft created", "status": "current"},
        ],
        "created_at": now,
        "updated_at": now,
        "submitted_at": None,
    }
    result = await db["claims"].insert_one(doc)
    saved = await db["claims"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create claim")
    await ensure_required_doc_stubs(db, result.inserted_id)
    return ClaimInDB.from_mongo(saved)


@router.get("/{claim_id}", response_model=ClaimInDB)
async def get_claim(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    await ensure_required_doc_stubs(db, ObjectId(claim_id))
    return ClaimInDB.from_mongo(doc)


@router.patch("/{claim_id}", response_model=ClaimInDB)
async def update_claim(
    claim_id: str,
    payload: ClaimUpdateRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        res = await db["claims"].update_one(
            {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
            {"$set": updates},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return ClaimInDB.from_mongo(doc)


@router.post("/{claim_id}/submit", response_model=ClaimInDB)
async def submit_claim(
    claim_id: str,
    payload: ClaimSubmitRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    if not payload.consent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consent required")

    now = datetime.now(timezone.utc)
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = ClaimInDB.from_mongo(doc)
    timeline = [ClaimTimelineItem.model_validate(i).model_dump() for i in claim.timeline]
    for i in timeline:
        if i.get("status") == "current":
            i["status"] = "done"
    timeline.append({"at": now, "label": "Submitted", "status": "current"})

    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "status": "processing",
                "submitted_at": now,
                "timeline": timeline,
                "updated_at": now,
            }
        },
    )

    await db["notifications"].insert_one(
        {
            "user_id": ObjectId(user.id),
            "type": "status",
            "title": "Claim submitted",
            "message": "Your claim has been submitted and is now being processed.",
            "claim_id": ObjectId(claim_id),
            "read": False,
            "created_at": now,
        }
    )

    updated = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return ClaimInDB.from_mongo(updated)


@router.get("/{claim_id}/timeline", response_model=list[ClaimTimelineItem])
async def get_claim_timeline(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[ClaimTimelineItem]:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"timeline": 1})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return [ClaimTimelineItem.model_validate(i) for i in doc.get("timeline", [])]


@router.get("/{claim_id}/required-docs", response_model=list[RequiredDoc])
async def get_required_docs(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[RequiredDoc]:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"_id": 1})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return required_docs()


@router.get("/{claim_id}/documents", response_model=list[ClaimDocumentResponse])
async def list_documents(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[ClaimDocumentResponse]:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"_id": 1})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    await ensure_required_doc_stubs(db, ObjectId(claim_id))
    cursor = db["claim_documents"].find({"claim_id": ObjectId(claim_id)}).sort("doc_type", 1)
    out: list[ClaimDocumentResponse] = []
    async for doc in cursor:
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


@router.post("/{claim_id}/documents", response_model=ClaimDocumentResponse)
async def attach_document(
    claim_id: str,
    payload: AttachDocumentRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimDocumentResponse:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"_id": 1})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    upload = await db["uploads"].find_one({"_id": ObjectId(payload.upload_id), "user_id": ObjectId(user.id)})
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")

    now = datetime.now(timezone.utc)
    await db["claim_documents"].update_one(
        {"claim_id": ObjectId(claim_id), "doc_type": payload.doc_type},
        {
            "$set": {
                "upload_id": payload.upload_id,
                "url": upload.get("url"),
                "status": "uploaded",
                "updated_at": now,
            },
            "$setOnInsert": {"required": True, "created_at": now, "note": None},
        },
        upsert=True,
    )
    doc = await db["claim_documents"].find_one({"claim_id": ObjectId(claim_id), "doc_type": payload.doc_type})
    if not doc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to attach document")
    d = ClaimDocumentInDB.from_mongo(doc)
    return ClaimDocumentResponse(
        id=d.id,
        claim_id=d.claim_id,
        doc_type=d.doc_type,
        required=d.required,
        status=d.status,
        note=d.note,
        upload_id=d.upload_id,
        url=d.url,
    )


@router.post("/{claim_id}/validate", response_model=ValidationResponse)
async def validate_claim_documents(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ValidationResponse:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"_id": 1})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    await ensure_required_doc_stubs(db, ObjectId(claim_id))
    docs_map = {}
    async for doc in db["claim_documents"].find({"claim_id": ObjectId(claim_id)}):
        d = ClaimDocumentInDB.from_mongo(doc)
        docs_map[d.doc_type] = d

    now = datetime.now(timezone.utc)
    results: list[ValidationResultItem] = []
    overall = "ok"
    for req in required_docs():
        d = docs_map.get(req.doc_type)
        if d and d.upload_id:
            results.append(ValidationResultItem(doc_type=req.doc_type, status="valid", note="OK"))
            await db["claim_documents"].update_one(
                {"_id": ObjectId(d.id)},
                {"$set": {"status": "valid", "note": "OK", "updated_at": now}},
            )
        else:
            overall = "issues"
            results.append(ValidationResultItem(doc_type=req.doc_type, status="missing", note="Missing"))
            await db["claim_documents"].update_one(
                {"claim_id": ObjectId(claim_id), "doc_type": req.doc_type},
                {"$set": {"status": "missing", "note": "Missing", "updated_at": now}},
            )

    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {"$set": {"updated_at": now}},
    )
    return ValidationResponse(overall=overall, results=results)


@router.delete("/{claim_id}", response_model=OkResponse)
async def delete_claim(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    res = await db["claims"].delete_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    await db["claim_documents"].delete_many({"claim_id": ObjectId(claim_id)})
    return OkResponse()

