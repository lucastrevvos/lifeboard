import os

import pytest
from fastapi.testclient import TestClient

from app.database.connection import get_connection
from app.main import app
from app.security.passwords import verify_password
from scripts.migrate import run_migrations


client = TestClient(app)

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_register_user(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE users
            RESTART IDENTITY CASCADE;
            """
        )

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "Lucas@Example.COM",
            "password": "secret123",
        },
    )

    assert response.status_code == 201

    assert response.json() == {
        "id": 1,
        "name": "Lucas Amaral",
        "email": "lucas@example.com",
    }

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT email, password_hash
            FROM users
            WHERE id = 1;
            """
        ).fetchone()

    assert row is not None
    assert row[0] == "lucas@example.com"
    assert row[1] != "secret123"
    assert verify_password("secret123", row[1]) is True


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_register_rejects_duplicate_email(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE users
            RESTART IDENTITY CASCADE;
            """
        )

    first = client.post(
        "/api/auth/register",
        json={
            "name": "Lucas",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    second = client.post(
        "/api/auth/register",
        json={
            "name": "Outro Lucas",
            "email": "LUCAS@EXAMPLE.COM",
            "password": "another123",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 409

    assert second.json() == {
        "detail": "Email already registered"
    }
