from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.settings import settings


def create_access_token(*, subject: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

