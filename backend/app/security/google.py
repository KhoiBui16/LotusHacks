from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.settings import settings


def verify_google_id_token(token: str) -> dict:
    if not settings.google_client_id:
        raise ValueError("GOOGLE_CLIENT_ID is not configured")
    req = google_requests.Request()
    claims = id_token.verify_oauth2_token(token, req, settings.google_client_id)
    return claims

