from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.models.user import UserInDB
from app.models.vehicle import VehicleInDB, VehicleSummary
from app.schemas.me import OkResponse
from app.schemas.vehicles import PolicyLinkRequest, VehicleCreateRequest, VehicleUpdateRequest
from app.security.deps import get_current_user

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _to_object_id(raw_id: str, label: str) -> ObjectId:
    try:
        return ObjectId(raw_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label} id")


def _assert_vehicle_access_allowed(user: UserInDB) -> None:
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vehicle management is disabled for admin accounts")


@router.get("", response_model=list[VehicleSummary])
async def list_vehicles(
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[VehicleSummary]:
    _assert_vehicle_access_allowed(user)
    vehicles = db["vehicles"]
    claims = db["claims"]

    cursor = vehicles.find({"user_id": ObjectId(user.id)}).sort("created_at", -1)
    items: list[VehicleSummary] = []
    async for doc in cursor:
        v = VehicleInDB.from_mongo(doc)
        count = await claims.count_documents({"user_id": ObjectId(user.id), "vehicle_id": ObjectId(v.id)})
        items.append(
            VehicleSummary(
                id=v.id,
                plate=v.plate,
                model=v.model,
                year=v.year,
                color=v.color,
                vehicle_type=v.vehicle_type,
                policy_linked=v.policy_linked,
                insurer=v.insurer,
                policy_id=v.policy_id,
                expiry=v.expiry,
                claims_count=count,
                created_at=v.created_at,
            )
        )
    return items


@router.post("", response_model=VehicleInDB, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreateRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> VehicleInDB:
    _assert_vehicle_access_allowed(user)
    if not payload.no_plate_yet and not payload.plate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="plate is required")
    if payload.no_plate_yet:
        plate = None
    else:
        plate = payload.plate

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": ObjectId(user.id),
        "no_plate_yet": payload.no_plate_yet,
        "plate": plate,
        "model": payload.model,
        "year": payload.year,
        "color": payload.color,
        "vehicle_type": payload.vehicle_type,
        "seats": payload.seats,
        "weight_tons": payload.weight_tons,
        "chassis_number": payload.chassis_number,
        "engine_number": payload.engine_number,
        "usage": payload.usage,
        "buyer_type": payload.buyer_type,
        "buyer_name": payload.buyer_name,
        "buyer_dob": payload.buyer_dob,
        "buyer_age": payload.buyer_age,
        "buyer_gender": payload.buyer_gender,
        "buyer_phone": payload.buyer_phone,
        "buyer_email": payload.buyer_email,
        "buyer_id_number": payload.buyer_id_number,
        "buyer_address": payload.buyer_address,
        "owner_same_as_buyer": payload.owner_same_as_buyer,
        "owner_name": payload.owner_name,
        "owner_phone": payload.owner_phone,
        "owner_email": payload.owner_email,
        "owner_address": payload.owner_address,
        "policy_linked": False,
        "policy_id": None,
        "insurer": None,
        "effective_date": None,
        "expiry": None,
        "insurance_years": None,
        "premium_amount": None,
        "premium_currency": None,
        "additional_benefits": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db["vehicles"].insert_one(doc)
    saved = await db["vehicles"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create vehicle")
    return VehicleInDB.from_mongo(saved)


@router.get("/{vehicle_id}", response_model=VehicleInDB)
async def get_vehicle(
    vehicle_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> VehicleInDB:
    _assert_vehicle_access_allowed(user)
    vehicle_oid = _to_object_id(vehicle_id, "vehicle")
    doc = await db["vehicles"].find_one({"_id": vehicle_oid, "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return VehicleInDB.from_mongo(doc)


@router.patch("/{vehicle_id}", response_model=VehicleInDB)
async def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdateRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> VehicleInDB:
    _assert_vehicle_access_allowed(user)
    vehicle_oid = _to_object_id(vehicle_id, "vehicle")
    current = await db["vehicles"].find_one({"_id": vehicle_oid, "user_id": ObjectId(user.id)})
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if "no_plate_yet" in updates and updates["no_plate_yet"] is True:
        updates["plate"] = None
    if "plate" in updates and updates["plate"] is not None:
        updates["plate"] = updates["plate"].strip()

    if updates.get("no_plate_yet") is False:
        candidate_plate = updates.get("plate", current.get("plate"))
        if not candidate_plate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="plate is required when no_plate_yet is false")
    elif updates.get("no_plate_yet") is not True and "plate" in updates:
        existing_no_plate = bool(current.get("no_plate_yet", False))
        if not existing_no_plate and not updates["plate"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="plate is required")

    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        res = await db["vehicles"].update_one(
            {"_id": vehicle_oid, "user_id": ObjectId(user.id)},
            {"$set": updates},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    doc = await db["vehicles"].find_one({"_id": vehicle_oid, "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return VehicleInDB.from_mongo(doc)


@router.delete("/{vehicle_id}", response_model=OkResponse)
async def delete_vehicle(
    vehicle_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    _assert_vehicle_access_allowed(user)
    vehicle_oid = _to_object_id(vehicle_id, "vehicle")
    user_oid = ObjectId(user.id)

    claims_cursor = db["claims"].find(
        {"user_id": user_oid, "vehicle_id": vehicle_oid},
        {"_id": 1},
    )
    claim_ids: list[ObjectId] = [doc["_id"] async for doc in claims_cursor]

    res = await db["vehicles"].delete_one({"_id": vehicle_oid, "user_id": user_oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    if claim_ids:
                await db["claims"].delete_many({"_id": {"$in": claim_ids}, "user_id": user_oid})
                await db["claim_documents"].delete_many({"claim_id": {"$in": claim_ids}})
                await db["notifications"].delete_many({"user_id": user_oid, "claim_id": {"$in": claim_ids}})

    return OkResponse()


@router.post("/{vehicle_id}/policy/link", response_model=VehicleInDB)
async def link_policy(
    vehicle_id: str,
    payload: PolicyLinkRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> VehicleInDB:
    _assert_vehicle_access_allowed(user)
    vehicle_oid = _to_object_id(vehicle_id, "vehicle")
    updates = {
        "policy_linked": True,
        "policy_id": payload.policy_id,
        "insurer": payload.insurer,
        "effective_date": payload.effective_date,
        "expiry": payload.expiry,
        "updated_at": datetime.now(timezone.utc),
    }
    res = await db["vehicles"].update_one(
        {"_id": vehicle_oid, "user_id": ObjectId(user.id)},
        {"$set": updates},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    doc = await db["vehicles"].find_one({"_id": vehicle_oid, "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return VehicleInDB.from_mongo(doc)


@router.delete("/{vehicle_id}/policy/unlink", response_model=VehicleInDB)
async def unlink_policy(
    vehicle_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> VehicleInDB:
    _assert_vehicle_access_allowed(user)
    vehicle_oid = _to_object_id(vehicle_id, "vehicle")
    updates = {
        "policy_linked": False,
        "policy_id": None,
        "insurer": None,
        "effective_date": None,
        "expiry": None,
        "updated_at": datetime.now(timezone.utc),
    }
    res = await db["vehicles"].update_one(
        {"_id": vehicle_oid, "user_id": ObjectId(user.id)},
        {"$set": updates},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    doc = await db["vehicles"].find_one({"_id": vehicle_oid, "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return VehicleInDB.from_mongo(doc)

