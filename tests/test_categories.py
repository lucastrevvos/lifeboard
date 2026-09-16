import os

import pytest

from app.categories.schemas import CreateCategoryRequest
from app.categories.service import (
    CategoryPermissionError,
    CategoryVisibilityError,
    create_category_for_board,
    get_categories_for_board,
)
from app.database.connection import get_connection
from scripts.migrate import run_migrations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


pytestmark = pytest.mark.integration

def prepare_category_context(
    monkeypatch,
) -> tuple[int, int, int, int]:
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

        lucas = connection.execute(
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
                "Lucas",
                "lucas@example.com",
                "not-used",
            ),
        ).fetchone()

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

        patrick = connection.execute(
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
                "Patrick",
                "patrick@example.com",
                "not-used",
            ),
        ).fetchone()

        assert lucas is not None
        assert lais is not None
        assert patrick is not None

        board = connection.execute(
            """
            INSERT INTO boards (
                name,
                created_by_user_id
            )
            VALUES (%s, %s)
            RETURNING id;
            """,
            (
                "Casa",
                lucas[0],
            ),
        ).fetchone()

        assert board is not None

        connection.execute(
            """
            INSERT INTO board_members (
                board_id,
                user_id,
                role
            )
            VALUES
                (%s, %s, 'owner'),
                (%s, %s, 'member');
            """,
            (
                board[0],
                lucas[0],
                board[0],
                lais[0],
            ),
        )

    return (
        lucas[0],
        lais[0],
        patrick[0],
        board[0],
    )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_owner_can_create_category(
    monkeypatch,
) -> None:
    lucas_id, _, _, board_id = prepare_category_context(
        monkeypatch
    )

    category = create_category_for_board(
        board_id=board_id,
        user_id=lucas_id,
        data=CreateCategoryRequest(
            name="  Treino  ",
            kind="individual",
            position=1,
        ),
    )

    assert category.name == "Treino"
    assert category.kind == "individual"
    assert category.position == 1
    assert category.board_id == board_id


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_member_cannot_create_category(
    monkeypatch,
) -> None:
    _, lais_id, _, board_id = prepare_category_context(
        monkeypatch
    )

    with pytest.raises(
        CategoryPermissionError
    ):
        create_category_for_board(
            board_id=board_id,
            user_id=lais_id,
            data=CreateCategoryRequest(
                name="Treino",
                kind="individual",
                position=1,
            ),
        )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_member_can_list_active_categories_in_position_order(
    monkeypatch,
) -> None:
    lucas_id, lais_id, _, board_id = (
        prepare_category_context(
            monkeypatch
        )
    )

    create_category_for_board(
        board_id=board_id,
        user_id=lucas_id,
        data=CreateCategoryRequest(
            name="Amor",
            kind="shared",
            position=2,
        ),
    )

    create_category_for_board(
        board_id=board_id,
        user_id=lucas_id,
        data=CreateCategoryRequest(
            name="Treino",
            kind="individual",
            position=1,
        ),
    )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO categories (
                board_id,
                name,
                kind,
                position,
                active
            )
            VALUES (%s, %s, %s, %s, FALSE);
            """,
            (
                board_id,
                "Categoria antiga",
                "shared",
                0,
            ),
        )

    categories = get_categories_for_board(
        board_id=board_id,
        user_id=lais_id,
    )

    assert [
        category.name
        for category in categories
    ] == [
        "Treino",
        "Amor",
    ]


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_non_member_cannot_list_categories(
    monkeypatch,
) -> None:
    _, _, patrick_id, board_id = (
        prepare_category_context(
            monkeypatch
        )
    )

    with pytest.raises(
        CategoryVisibilityError
    ):
        get_categories_for_board(
            board_id=board_id,
            user_id=patrick_id,
        )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_owner_can_create_category_through_api(
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
            "name": "Lucas",
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

    board_response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    assert board_response.status_code == 201

    board_id = board_response.json()["id"]

    category_response = client.post(
        f"/api/boards/{board_id}/categories",
        json={
            "name": "Treino",
            "kind": "individual",
            "position": 1,
        },
    )

    assert category_response.status_code == 201

    assert category_response.json() == {
        "id": 1,
        "board_id": board_id,
        "name": "Treino",
        "kind": "individual",
        "position": 1,
    }


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_create_category_rejects_invalid_kind(
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

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas",
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

    board_response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    board_id = board_response.json()["id"]

    response = client.post(
        f"/api/boards/{board_id}/categories",
        json={
            "name": "Privado",
            "kind": "private",
            "position": 1,
        },
    )

    assert response.status_code == 422


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_owner_can_list_categories_through_api(
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

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas",
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

    board_response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    board_id = board_response.json()["id"]

    client.post(
        f"/api/boards/{board_id}/categories",
        json={
            "name": "Amor",
            "kind": "shared",
            "position": 2,
        },
    )

    client.post(
        f"/api/boards/{board_id}/categories",
        json={
            "name": "Treino",
            "kind": "individual",
            "position": 1,
        },
    )

    response = client.get(
        f"/api/boards/{board_id}/categories"
    )

    assert response.status_code == 200

    categories = response.json()

    assert [
        category["name"]
        for category in categories
    ] == [
        "Treino",
        "Amor",
    ]
