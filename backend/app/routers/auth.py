from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.db import get_db
from app.models.user import UserInDB, UserPublic
from app.schemas.auth import AuthResponse, GoogleAuthRequest, SignInRequest, SignUpRequest
from app.security.google import verify_google_id_token
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def signup(payload: SignUpRequest) -> AuthResponse:
    db = get_db()
    users = db["users"]

    existing = await users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    now = datetime.now(timezone.utc)
    doc = {
        "email": payload.email.lower(),
        "full_name": payload.full_name,
        "password_hash": hash_password(payload.password),
        "google_sub": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await users.insert_one(doc)
    user_db = UserInDB.from_mongo({**doc, "_id": result.inserted_id})
    token = create_access_token(subject=user_db.id)
    return AuthResponse(
        access_token=token,
        user=UserPublic(
            id=user_db.id,
            email=user_db.email,
            full_name=user_db.full_name,
            created_at=user_db.created_at,
        ),
    )


@router.post("/signin", response_model=AuthResponse)
async def signin(payload: SignInRequest) -> AuthResponse:
    db = get_db()
    users = db["users"]

    doc = await users.find_one({"email": payload.email.lower()})
    if not doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user_db = UserInDB.from_mongo(doc)
    if not user_db.password_hash or not verify_password(payload.password, user_db.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user_db.id)
    return AuthResponse(
        access_token=token,
        user=UserPublic(
            id=user_db.id,
            email=user_db.email,
            full_name=user_db.full_name,
            created_at=user_db.created_at,
        ),
    )


@router.post("/google", response_model=AuthResponse)
async def google_auth(payload: GoogleAuthRequest) -> AuthResponse:
    try:
        claims = verify_google_id_token(payload.id_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    email = (claims.get("email") or "").lower()
    sub = claims.get("sub")
    name = claims.get("name") or ""
    if not email or not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    db = get_db()
    users = db["users"]

    now = datetime.now(timezone.utc)
    doc = await users.find_one({"$or": [{"google_sub": sub}, {"email": email}]})
    if doc:
        user_db = UserInDB.from_mongo(doc)
        updates = {}
        if not user_db.google_sub:
            updates["google_sub"] = sub
        if name and user_db.full_name != name:
            updates["full_name"] = name
        if updates:
            updates["updated_at"] = now
            await users.update_one({"_id": ObjectId(user_db.id)}, {"$set": updates})
            user_db = UserInDB.from_mongo({**doc, **updates})
    else:
        insert_doc = {
            "email": email,
            "full_name": name or email.split("@")[0],
            "password_hash": None,
            "google_sub": sub,
            "created_at": now,
            "updated_at": now,
        }
        result = await users.insert_one(insert_doc)
        user_db = UserInDB.from_mongo({**insert_doc, "_id": result.inserted_id})

    token = create_access_token(subject=user_db.id)
    return AuthResponse(
        access_token=token,
        user=UserPublic(
            id=user_db.id,
            email=user_db.email,
            full_name=user_db.full_name,
            created_at=user_db.created_at,
        ),
    )

