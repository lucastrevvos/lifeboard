import os

from dotenv import load_dotenv

load_dotenv()

def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return database_url

def get_session_secret_key() -> str:
    secret_key = os.getenv("SESSION_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("SESSION_SECRET_KEY is not configured")

    return secret_key

def is_production() -> bool:
    return os.getenv("APP_ENV", "development").lower() == "production"


def get_frontend_origins() -> list[str]:
    configured_origins = os.getenv("FRONTEND_ORIGINS")

    if configured_origins is None:
        if is_production():
            return []

        return ["http://localhost:3000"]

    origins = [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ]

    if "*" in origins:
        raise RuntimeError(
            "FRONTEND_ORIGINS cannot contain '*' when cookies are enabled"
        )

    return origins
