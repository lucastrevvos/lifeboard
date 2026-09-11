import os

import pytest
from fastapi.testclient import TestClient

from app.database.connection import get_connection
from app.main import app
from app.security.passwords import verify_password
from scripts.migrate import run_migrations

from app.auth.schemas import LoginRequest
from app.auth.service import (
    InvalidCredentialsError,
    authenticate_user
)


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

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_authenticate_user(monkeypatch) -> None:
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

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    user = authenticate_user(
        LoginRequest(
            email="LUCAS@EXAMPLE.COM",
            password="secret123",
        )
    )

    assert user.name == "Lucas Amaral"
    assert user.email == "lucas@example.com"

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_authenticate_user_rejects_wrong_password(
    monkeypatch,
) -> None:
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

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(
            LoginRequest(
                email="lucas@example.com",
                password="senha-errada",
            )
        )

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_login(monkeypatch) -> None:
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

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    client.cookies.clear()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "LUCAS@EXAMPLE.COM",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    assert "lifeboard_session" in client.cookies

    assert response.json() == {
        "id": 1,
        "name": "Lucas Amaral",
        "email": "lucas@example.com",
    }

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_login_rejects_invalid_credentials(monkeypatch) -> None:
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

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "errada",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid email or password"
    }

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_authenticated_session_and_logout(monkeypatch) -> None:
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

    client.cookies.clear()

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    before_login = client.get("/api/auth/me")

    assert before_login.status_code == 401

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200
    assert "lifeboard_session" in client.cookies

    me_response = client.get("/api/auth/me")

    assert me_response.status_code == 200

    assert me_response.json() == {
        "id": 1,
        "name": "Lucas Amaral",
        "email": "lucas@example.com",
    }

    logout_response = client.post("/api/auth/logout")

    assert logout_response.status_code == 204

    after_logout = client.get("/api/auth/me")

    assert after_logout.status_code == 401
