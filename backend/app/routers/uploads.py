import os
import secrets
from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.models.upload import UploadInDB, UploadPurpose
from app.models.user import UserInDB
from app.schemas.uploads import UploadResponse
from app.security.deps import get_current_user

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    purpose: UploadPurpose = "other",
) -> UploadResponse:
    data = await file.read()
    if data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload")

    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    uploads_dir = os.path.abspath(uploads_dir)
    os.makedirs(uploads_dir, exist_ok=True)

    token = secrets.token_urlsafe(12)
    safe_name = (file.filename or "upload").replace("/", "_").replace("\\", "_")
    stored_name = f"{token}-{safe_name}"
    path = os.path.join(uploads_dir, stored_name)
    with open(path, "wb") as f:
        f.write(data)

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": ObjectId(user.id),
        "filename": safe_name,
        "content_type": file.content_type or "application/octet-stream",
        "size_bytes": len(data),
        "purpose": purpose,
        "url": f"file://{path}",
        "created_at": now,
    }
    result = await db["uploads"].insert_one(doc)
    saved = await db["uploads"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Upload failed")
    upload = UploadInDB.from_mongo(saved)
    return UploadResponse(
        upload_id=upload.id,
        filename=upload.filename,
        content_type=upload.content_type,
        size_bytes=upload.size_bytes,
        purpose=upload.purpose,
        url=upload.url,
    )
