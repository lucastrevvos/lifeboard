import pytest

from app.config import get_database_url, get_frontend_origins

def test_get_database_url_returns_environment_value(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@example.com/database"
    )

    assert (
        get_database_url()
        == "postgresql://user:password@example.com/database"
    )

def test_get_database_url_raises_when_missing(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(
        RuntimeError,
        match="DATABASE_URL is not configured"
    ):
        get_database_url()


def test_frontend_origins_default_to_nextjs_in_development(monkeypatch) -> None:
    monkeypatch.delenv("FRONTEND_ORIGINS", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    assert get_frontend_origins() == ["http://localhost:3000"]


def test_frontend_origins_are_normalized(monkeypatch) -> None:
    monkeypatch.setenv(
        "FRONTEND_ORIGINS",
        "https://app.example.com/, http://localhost:3000",
    )

    assert get_frontend_origins() == [
        "https://app.example.com",
        "http://localhost:3000",
    ]


def test_frontend_origins_reject_wildcard(monkeypatch) -> None:
    monkeypatch.setenv("FRONTEND_ORIGINS", "*")

    with pytest.raises(RuntimeError, match="cannot contain"):
        get_frontend_origins()
