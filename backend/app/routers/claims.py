from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.models.claim import ClaimInDB, ClaimListItem, ClaimTimelineItem
from app.models.claim_document import ClaimDocumentInDB
from app.models.user import UserInDB
from app.schemas.claims import (
    AttachDocumentRequest,
    ClaimAppealRequest,
    ClaimAppealResponse,
    CoverageCheckResponse,
    ClaimCreateRequest,
    ClaimDocumentResponse,
    ClaimSubmitRequest,
    ClaimUpdateRequest,
    DossierResponse,
    EligibilityResponse,
    FirstNoticeRequest,
    FirstNoticeResponse,
    PolicyImportRequest,
    PolicyImportResponse,
    RequiredDoc,
    SubmitRouterRequest,
    SubmitRouterResponse,
    TriageResponse,
    ValidationResponse,
    ValidationResultItem,
)
from app.schemas.me import OkResponse
from app.security.deps import get_current_user

router = APIRouter(prefix="/claims", tags=["claims"])


async def notify_admins_about_claim(
    db: AsyncIOMotorDatabase,
    *,
    claim_id: str,
    claim_short_id: str,
    creator_name: str,
    creator_email: str,
    message: str,
    now: datetime,
) -> None:
    admin_ids: list[ObjectId] = []
    async for admin in db["users"].find({"role": "admin"}, {"_id": 1}):
        admin_ids.append(admin["_id"])
    if not admin_ids:
        return

    docs = [
        {
            "user_id": admin_id,
            "type": "info",
            "title": f"New claim update: {claim_short_id}",
            "message": f"{creator_name} ({creator_email}) {message}",
            "claim_id": ObjectId(claim_id),
            "read": False,
            "created_at": now,
        }
        for admin_id in admin_ids
    ]
    await db["notifications"].insert_many(docs)


def required_docs(*, police_report_required: bool) -> list[RequiredDoc]:
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
            required=police_report_required,
        ),
    ]


def is_complex_case(claim: ClaimInDB) -> tuple[bool, list[str]]:
    incident = claim.incident
    if not incident:
        return False, []
    reasons: list[str] = []
    if incident.has_injury:
        reasons.append("injury")
    if incident.has_third_party:
        reasons.append("third_party")
    if incident.needs_towing:
        reasons.append("needs_towing")
    return len(reasons) > 0, reasons


def required_docs_for_claim(claim: ClaimInDB) -> list[RequiredDoc]:
    police_required = False
    if claim.incident and (claim.incident.has_injury or claim.incident.has_third_party):
        police_required = True
    return required_docs(police_report_required=police_required)


async def ensure_required_doc_stubs(db: AsyncIOMotorDatabase, claim: ClaimInDB) -> None:
    now = datetime.now(timezone.utc)
    for d in required_docs_for_claim(claim):
        await db["claim_documents"].update_one(
            {"claim_id": ObjectId(claim.id), "doc_type": d.doc_type},
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


def coverage_check(claim: ClaimInDB) -> CoverageCheckResponse:
    has_policy = bool(claim.policy_id and claim.insurer)
    policy_active = has_policy
    likely_excluded = bool(claim.incident and claim.incident.type == "other")
    deductible_notice = "Standard deductible may apply"
    return CoverageCheckResponse(
        policy_active=policy_active,
        has_policy=has_policy,
        likely_excluded=likely_excluded,
        deductible_notice=deductible_notice,
    )


def eligibility_for_claim(claim: ClaimInDB) -> EligibilityResponse:
    complex_case, _ = is_complex_case(claim)
    coverage = coverage_check(claim)
    notes: list[str] = []
    if not coverage.has_policy:
        notes.append("No linked policy found")
        return EligibilityResponse(
            claim_id=claim.id,
            outcome="low_value_or_excluded",
            coverage=coverage,
            next_action="exit",
            notes=notes,
        )

    if coverage.likely_excluded:
        notes.append("Incident type may be excluded by policy terms")
        return EligibilityResponse(
            claim_id=claim.id,
            outcome="low_value_or_excluded",
            coverage=coverage,
            next_action="exit",
            notes=notes,
        )

    if complex_case:
        notes.append("Complex case requires assisted handling")
        return EligibilityResponse(
            claim_id=claim.id,
            outcome="likely_covered",
            coverage=coverage,
            next_action="assisted",
            notes=notes,
        )

    notes.append("Likely covered based on initial intake")
    return EligibilityResponse(
        claim_id=claim.id,
        outcome="likely_covered",
        coverage=coverage,
        next_action="chat",
        notes=notes,
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
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Claim creation is disabled for admin accounts")

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
    claim = ClaimInDB.from_mongo(saved)
    await ensure_required_doc_stubs(db, claim)
    await notify_admins_about_claim(
        db,
        claim_id=claim.id,
        claim_short_id=claim.id[-8:],
        creator_name=user.full_name,
        creator_email=user.email,
        message="created a new claim draft.",
        now=now,
    )
    return claim


@router.get("/{claim_id}", response_model=ClaimInDB)
async def get_claim(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim = ClaimInDB.from_mongo(doc)
    await ensure_required_doc_stubs(db, claim)
    return claim


@router.patch("/{claim_id}", response_model=ClaimInDB)
async def update_claim(
    claim_id: str,
    payload: ClaimUpdateRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    try:
        claim_obj_id = ObjectId(claim_id)
        user_obj_id = ObjectId(user.id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        res = await db["claims"].update_one(
            {"_id": claim_obj_id, "user_id": user_obj_id},
            {"$set": updates},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    doc = await db["claims"].find_one({"_id": claim_obj_id, "user_id": user_obj_id})
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
    await notify_admins_about_claim(
        db,
        claim_id=claim_id,
        claim_short_id=claim_id[-8:],
        creator_name=user.full_name,
        creator_email=user.email,
        message="submitted a claim for processing.",
        now=now,
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
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim = ClaimInDB.from_mongo(doc)
    return required_docs_for_claim(claim)


@router.get("/{claim_id}/documents", response_model=list[ClaimDocumentResponse])
async def list_documents(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[ClaimDocumentResponse]:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"_id": 1})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim_full_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_full_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim_obj = ClaimInDB.from_mongo(claim_full_doc)
    await ensure_required_doc_stubs(db, claim_obj)
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

    claim_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim_obj = ClaimInDB.from_mongo(claim_doc)
    await ensure_required_doc_stubs(db, claim_obj)
    docs_map = {}
    async for doc in db["claim_documents"].find({"claim_id": ObjectId(claim_id)}):
        d = ClaimDocumentInDB.from_mongo(doc)
        docs_map[d.doc_type] = d

    now = datetime.now(timezone.utc)
    results: list[ValidationResultItem] = []
    overall = "ok"
    for req in required_docs_for_claim(claim_obj):
        d = docs_map.get(req.doc_type)
        if not req.required:
            results.append(ValidationResultItem(doc_type=req.doc_type, status="valid", note="Optional"))
            await db["claim_documents"].update_one(
                {"claim_id": ObjectId(claim_id), "doc_type": req.doc_type},
                {"$set": {"status": "valid", "note": "Optional", "updated_at": now}},
            )
            continue
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


@router.post("/{claim_id}/policy-import", response_model=PolicyImportResponse)
async def import_policy_for_claim(
    claim_id: str,
    payload: PolicyImportRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> PolicyImportResponse:
    try:
        claim_oid = ObjectId(claim_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    claim = await db["claims"].find_one({"_id": claim_oid, "user_id": ObjectId(user.id)})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    now = datetime.now(timezone.utc)
    await db["claims"].update_one(
        {"_id": claim_oid, "user_id": ObjectId(user.id)},
        {
            "$set": {
                "policy_id": payload.policy_id,
                "insurer": payload.insurer,
                "policy_import": {
                    "source": payload.source,
                    "effective_date": payload.effective_date,
                    "expiry": payload.expiry,
                    "updated_at": now,
                },
                "updated_at": now,
            }
        },
    )

    await db["vehicles"].update_one(
        {"_id": claim.get("vehicle_id"), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "policy_linked": True,
                "policy_id": payload.policy_id,
                "insurer": payload.insurer,
                "effective_date": payload.effective_date,
                "expiry": payload.expiry,
                "updated_at": now,
            }
        },
    )

    return PolicyImportResponse(
        claim_id=claim_id,
        policy_linked=True,
        policy_id=payload.policy_id,
        insurer=payload.insurer,
        source=payload.source,
    )


@router.post("/{claim_id}/triage", response_model=TriageResponse)
async def triage_claim(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> TriageResponse:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim = ClaimInDB.from_mongo(doc)
    assisted, reasons = is_complex_case(claim)
    risk_level = "high" if assisted else "low"
    if claim.incident and not assisted and claim.incident.type in {"flood", "theft"}:
        risk_level = "medium"

    now = datetime.now(timezone.utc)
    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "triage": {
                    "risk_level": risk_level,
                    "assisted_mode": assisted,
                    "reasons": reasons,
                    "at": now,
                },
                "updated_at": now,
            }
        },
    )

    return TriageResponse(claim_id=claim_id, risk_level=risk_level, assisted_mode=assisted, reasons=reasons)


@router.get("/{claim_id}/eligibility", response_model=EligibilityResponse)
async def get_eligibility(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> EligibilityResponse:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim = ClaimInDB.from_mongo(doc)
    result = eligibility_for_claim(claim)
    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {"$set": {"eligibility": result.model_dump(), "updated_at": datetime.now(timezone.utc)}},
    )
    return result


@router.post("/{claim_id}/first-notice", response_model=FirstNoticeResponse)
async def create_first_notice(
    claim_id: str,
    payload: FirstNoticeRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> FirstNoticeResponse:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    now = datetime.now(timezone.utc)
    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "first_notice": {**payload.model_dump(), "at": now},
                "status": "needs-docs",
                "updated_at": now,
            }
        },
    )
    return FirstNoticeResponse(
        claim_id=claim_id,
        captured=True,
        message="First notice captured. Continue to evidence upload.",
    )


@router.get("/{claim_id}/dossier", response_model=DossierResponse)
async def build_dossier(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> DossierResponse:
    claim_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim = ClaimInDB.from_mongo(claim_doc)

    docs = await db["claim_documents"].find({"claim_id": ObjectId(claim_id)}).to_list(length=200)
    attachments_count = len([d for d in docs if d.get("upload_id")])
    required_map = {r.doc_type: r for r in required_docs_for_claim(claim)}
    completeness = "complete"
    for d in docs:
        r = required_map.get(d.get("doc_type"))
        if r and r.required and not d.get("upload_id"):
            completeness = "partial"
            break

    summary = f"Incident {claim.incident.type if claim.incident else 'unknown'} for vehicle {claim.vehicle_id}."
    timeline_items = [
        ValidationResultItem(doc_type=i.get("label", "timeline"), status="valid", note=i.get("status", ""))
        for i in claim_doc.get("timeline", [])
    ]
    return DossierResponse(
        claim_id=claim_id,
        summary=summary,
        timeline=timeline_items,
        attachments_count=attachments_count,
        completeness=completeness,
    )


@router.post("/{claim_id}/submit-router", response_model=SubmitRouterResponse)
async def submit_router(
    claim_id: str,
    payload: SubmitRouterRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> SubmitRouterResponse:
    claim_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    external_ref = f"SUB-{claim_id[-6:]}-{payload.channel.upper()}"
    now = datetime.now(timezone.utc)
    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "submission": {
                    "channel": payload.channel,
                    "external_ref": external_ref,
                    "status": "received",
                    "at": now,
                },
                "status": "processing",
                "updated_at": now,
            }
        },
    )
    return SubmitRouterResponse(
        claim_id=claim_id,
        channel=payload.channel,
        external_ref=external_ref,
        status="received",
    )


@router.post("/{claim_id}/appeal", response_model=ClaimAppealResponse)
async def appeal_claim(
    claim_id: str,
    payload: ClaimAppealRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimAppealResponse:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = ClaimInDB.from_mongo(doc)
    timeline = [ClaimTimelineItem.model_validate(i).model_dump() for i in claim.timeline]
    now = datetime.now(timezone.utc)
    for i in timeline:
        if i.get("status") == "current":
            i["status"] = "done"
    timeline.append({"at": now, "label": "Appeal submitted", "status": "current"})

    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "appeal": {"reason": payload.reason, "at": now},
                "status": "processing",
                "timeline": timeline,
                "updated_at": now,
            }
        },
    )

    await db["notifications"].insert_one(
        {
            "user_id": ObjectId(user.id),
            "type": "info",
            "title": "Claim appeal submitted",
            "message": "Your appeal has been submitted and is under review.",
            "claim_id": ObjectId(claim_id),
            "read": False,
            "created_at": now,
        }
    )
    return ClaimAppealResponse(claim_id=claim_id, appealed=True, message="Appeal submitted")


@router.delete("/{claim_id}", response_model=OkResponse)
async def delete_claim(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    try:
        claim_obj_id = ObjectId(claim_id)
        user_obj_id = ObjectId(user.id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")
    
    doc = await db["claims"].find_one({"_id": claim_obj_id, "user_id": user_obj_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    if doc.get("status") != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft claims can be deleted")
    
    res = await db["claims"].delete_one({"_id": claim_obj_id, "user_id": user_obj_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    await db["claim_documents"].delete_many({"claim_id": claim_obj_id})
    return OkResponse()

