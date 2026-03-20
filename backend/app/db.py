from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.settings import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def init_db() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_db_name]


def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        init_db()
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db

