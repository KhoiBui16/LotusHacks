from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.settings import settings


def verify_google_id_token(token: str) -> dict:
    if not settings.google_client_ids:
        raise ValueError("GOOGLE_CLIENT_ID is not configured")
    req = google_requests.Request()
    last_exc: Exception | None = None
    for client_id in settings.google_client_ids:
        try:
            return id_token.verify_oauth2_token(token, req, client_id)
        except Exception as exc:
            last_exc = exc
    if last_exc:
        raise last_exc
    raise ValueError("Invalid Google token")
