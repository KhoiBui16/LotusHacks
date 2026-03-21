import os
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.settings import settings
from app.security.passwords import hash_password


async def main() -> None:
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    full_name = os.getenv("ADMIN_FULL_NAME", "Admin").strip() or "Admin"

    if not email or not password:
        raise SystemExit("ADMIN_EMAIL and ADMIN_PASSWORD are required")

    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    users = db["users"]

    now = datetime.now(timezone.utc)
    existing = await users.find_one({"email": email})

    doc = {
        "email": email,
        "full_name": full_name,
        "phone": None,
        "avatar_url": None,
        "password_hash": hash_password(password),
        "google_sub": None,
        "role": "admin",
        "created_at": now,
        "updated_at": now,
    }

    if existing:
        await users.update_one({"_id": existing["_id"]}, {"$set": {**doc, "created_at": existing.get("created_at", now)}})
        user_id = str(existing["_id"])
    else:
        result = await users.insert_one(doc)
        user_id = str(result.inserted_id)

    client.close()
    print(user_id)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

