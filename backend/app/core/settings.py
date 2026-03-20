import os


class Settings:
    def __init__(self) -> None:
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.mongodb_db_name = os.getenv("MONGODB_DB_NAME", "lotushacks")
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-me")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expires_minutes = int(os.getenv("JWT_EXPIRES_MINUTES", "10080"))
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")


settings = Settings()

