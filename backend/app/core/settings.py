import os
from pathlib import Path

from dotenv import load_dotenv


def _load_env_files() -> None:
    # backend/app/core/settings.py -> backend/
    backend_dir = Path(__file__).resolve().parents[2]
    backend_env = backend_dir / ".env"

    # Keep existing process env as highest priority.
    if backend_env.exists():
        load_dotenv(backend_env, override=False)


_load_env_files()


class Settings:
    def __init__(self) -> None:
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", "lotushacks")
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-me")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expires_minutes = int(os.getenv("JWT_EXPIRES_MINUTES", "10080"))
        raw_google_client_ids = os.getenv("GOOGLE_CLIENT_ID", "")
        self.google_client_ids = [v.strip() for v in raw_google_client_ids.split(",") if v.strip()]


settings = Settings()
