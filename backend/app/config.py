import os
from functools import lru_cache


class Settings:
    jwt_secret_key: str = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 30
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./conduit.db")


@lru_cache
def get_settings() -> Settings:
    return Settings()
