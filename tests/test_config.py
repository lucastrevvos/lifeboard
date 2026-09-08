import pytest

from app.config import get_database_url

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
