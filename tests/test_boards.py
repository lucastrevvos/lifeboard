import os

import psycopg
import pytest

from app.boards.repository import create_board
from app.database.connection import get_connection
from scripts.migrate import run_migrations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


pytestmark = pytest.mark.integration

def test_create_board_requires_authentication() -> None:
    client.cookies.clear()

    response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Not authenticated",
    }


def prepare_user(monkeypatch) -> int:
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

        row = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash
            )
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                "Lucas Amaral",
                "lucas@example.com",
                "not-used-in-this-test",
            ),
        ).fetchone()

    assert row is not None

    return row[0]

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_create_board_adds_creator_as_owner(monkeypatch) -> None:
    user_id = prepare_user(monkeypatch)

    board = create_board(
        name="Casa",
        user_id=user_id,
    )

    assert board["name"] == "Casa"
    assert board["role"] == "owner"

    with get_connection() as connection:
        board_row = connection.execute(
            """
            SELECT
                id,
                name,
                created_by_user_id
            FROM boards
            WHERE id = %s;
            """,
            (board["id"],),
        ).fetchone()

        member_row = connection.execute(
            """
            SELECT
                board_id,
                user_id,
                role
            FROM board_members
            WHERE board_id = %s
              AND user_id = %s;
            """,
            (
                board["id"],
                user_id,
            ),
        ).fetchone()

    assert board_row == (
        board["id"],
        "Casa",
        user_id,
    )

    assert member_row == (
        board["id"],
        user_id,
        "owner",
    )

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_create_board_rolls_back_if_membership_fails(
    monkeypatch,
) -> None:
    user_id = prepare_user(monkeypatch)

    with get_connection() as connection:
        connection.execute(
            """
            ALTER TABLE board_members
            ADD CONSTRAINT test_reject_owner
            CHECK (role <> 'owner');
            """
        )

    try:
        with pytest.raises(psycopg.errors.CheckViolation):
            create_board(
                name="Casa",
                user_id=user_id,
            )

        with get_connection() as connection:
            board_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM boards
                WHERE name = 'Casa';
                """
            ).fetchone()

        assert board_count is not None
        assert board_count[0] == 0

    finally:
        with get_connection() as connection:
            connection.execute(
                """
                ALTER TABLE board_members
                DROP CONSTRAINT IF EXISTS test_reject_owner;
                """
            )

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_authenticated_user_can_create_board(
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

    client.cookies.clear()

    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200

    response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    assert response.status_code == 201

    assert response.json() == {
        "id": 1,
        "name": "Casa",
        "role": "owner",
    }

def test_list_boards_requires_authentication() -> None:
    client.cookies.clear()

    response = client.get("/api/boards")

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Not authenticated",
    }

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_list_boards_returns_only_user_memberships(
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

    client.cookies.clear()

    # Lucas
    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    lucas_board = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    assert lucas_board.status_code == 201

    # Criamos Laís diretamente no banco para montar
    # um board que Lucas NÃO pertence.
    with get_connection() as connection:
        lais = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash
            )
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                "Laís",
                "lais@example.com",
                "not-used",
            ),
        ).fetchone()

        assert lais is not None

        lais_board = connection.execute(
            """
            INSERT INTO boards (
                name,
                created_by_user_id
            )
            VALUES (%s, %s)
            RETURNING id;
            """,
            (
                "Board secreto da Laís",
                lais[0],
            ),
        ).fetchone()

        assert lais_board is not None

        connection.execute(
            """
            INSERT INTO board_members (
                board_id,
                user_id,
                role
            )
            VALUES (%s, %s, 'owner');
            """,
            (
                lais_board[0],
                lais[0],
            ),
        )

    response = client.get("/api/boards")

    assert response.status_code == 200

    assert response.json() == [
        {
            "id": 1,
            "name": "Casa",
            "role": "owner",
        }
    ]
