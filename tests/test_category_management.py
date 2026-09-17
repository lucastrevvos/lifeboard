import os
from contextlib import contextmanager
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.database.connection import get_connection
from app.main import app
from scripts.migrate import run_migrations


client = TestClient(app)
pytestmark = pytest.mark.integration


def prepare_management_context(
    monkeypatch,
) -> dict[str, int]:
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
        users = {}
        for name in ("Lucas", "Lais", "Patrick"):
            row = connection.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (
                    name,
                    f"{name.lower()}@example.com",
                    "not-used",
                ),
            ).fetchone()
            assert row is not None
            users[name.lower()] = row[0]

        board = connection.execute(
            """
            INSERT INTO boards (name, created_by_user_id)
            VALUES ('Casa', %s)
            RETURNING id;
            """,
            (users["lucas"],),
        ).fetchone()
        other_board = connection.execute(
            """
            INSERT INTO boards (name, created_by_user_id)
            VALUES ('Projeto', %s)
            RETURNING id;
            """,
            (users["patrick"],),
        ).fetchone()
        assert board is not None
        assert other_board is not None

        connection.execute(
            """
            INSERT INTO board_members (board_id, user_id, role)
            VALUES
                (%s, %s, 'owner'),
                (%s, %s, 'member'),
                (%s, %s, 'owner');
            """,
            (
                board[0],
                users["lucas"],
                board[0],
                users["lais"],
                other_board[0],
                users["patrick"],
            ),
        )

        category_ids = {}
        for name, position in (("A", 10), ("B", 20), ("C", 30)):
            row = connection.execute(
                """
                INSERT INTO categories (board_id, name, kind, position)
                VALUES (%s, %s, 'individual', %s)
                RETURNING id;
                """,
                (board[0], name, position),
            ).fetchone()
            assert row is not None
            category_ids[name.lower()] = row[0]

        foreign = connection.execute(
            """
            INSERT INTO categories (board_id, name, kind, position)
            VALUES (%s, 'X', 'shared', 0)
            RETURNING id;
            """,
            (other_board[0],),
        ).fetchone()
        assert foreign is not None

    return {
        **users,
        "board": board[0],
        "other_board": other_board[0],
        **category_ids,
        "foreign": foreign[0],
    }


@contextmanager
def authenticated_as(user_id: int) -> Iterator[None]:
    app.dependency_overrides[get_current_user] = lambda: UserResponse(
        id=user_id,
        name="Test user",
        email="test@example.com",
    )
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def category_positions(board_id: int) -> list[tuple[int, int]]:
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT id, position
            FROM categories
            WHERE board_id = %s
              AND active = TRUE
            ORDER BY id;
            """,
            (board_id,),
        ).fetchall()


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_owner_reorders_all_active_categories(
    monkeypatch,
) -> None:
    context = prepare_management_context(monkeypatch)

    with authenticated_as(context["lucas"]):
        response = client.put(
            f"/api/boards/{context['board']}/categories/reorder",
            json={
                "category_ids": [
                    context["c"],
                    context["a"],
                    context["b"],
                ],
            },
        )
        listed = client.get(
            f"/api/boards/{context['board']}/categories"
        )

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["C", "A", "B"]
    assert [item["position"] for item in response.json()] == [0, 1, 2]
    assert [item["name"] for item in listed.json()] == ["C", "A", "B"]


@pytest.mark.parametrize(
    "invalid_order",
    ["duplicate", "missing", "foreign", "inactive"],
)
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_invalid_reorder_is_atomic(
    monkeypatch,
    invalid_order: str,
) -> None:
    context = prepare_management_context(monkeypatch)

    if invalid_order == "inactive":
        with get_connection() as connection:
            connection.execute(
                "UPDATE categories SET active = FALSE WHERE id = %s;",
                (context["c"],),
            )

    orders = {
        "duplicate": [context["a"], context["a"], context["c"]],
        "missing": [context["a"], context["b"]],
        "foreign": [context["a"], context["b"], context["foreign"]],
        "inactive": [context["a"], context["b"], context["c"]],
    }
    before = category_positions(context["board"])

    with authenticated_as(context["lucas"]):
        response = client.put(
            f"/api/boards/{context['board']}/categories/reorder",
            json={"category_ids": orders[invalid_order]},
        )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "category_ids must contain all active board "
            "categories exactly once"
        )
    }
    assert category_positions(context["board"]) == before


@pytest.mark.parametrize("user", ["lais", "patrick"])
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_only_owner_can_reorder_categories(
    monkeypatch,
    user: str,
) -> None:
    context = prepare_management_context(monkeypatch)

    with authenticated_as(context[user]):
        response = client.put(
            f"/api/boards/{context['board']}/categories/reorder",
            json={
                "category_ids": [
                    context["a"],
                    context["b"],
                    context["c"],
                ],
            },
        )

    assert response.status_code == 403


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_owner_soft_deactivates_category(
    monkeypatch,
) -> None:
    context = prepare_management_context(monkeypatch)
    url = (
        f"/api/boards/{context['board']}"
        f"/categories/{context['b']}"
    )

    with authenticated_as(context["lucas"]):
        first = client.delete(url)
        listed = client.get(
            f"/api/boards/{context['board']}/categories"
        )
        second = client.delete(url)

    assert first.status_code == 204
    assert first.content == b""
    assert [item["name"] for item in listed.json()] == ["A", "C"]
    assert second.status_code == 404

    with get_connection() as connection:
        row = connection.execute(
            "SELECT active FROM categories WHERE id = %s;",
            (context["b"],),
        ).fetchone()
    assert row == (False,)


@pytest.mark.parametrize("user", ["lais", "patrick"])
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_only_owner_can_deactivate_category(
    monkeypatch,
    user: str,
) -> None:
    context = prepare_management_context(monkeypatch)

    with authenticated_as(context[user]):
        response = client.delete(
            f"/api/boards/{context['board']}/categories/{context['a']}"
        )

    assert response.status_code == 403


@pytest.mark.parametrize("category", ["foreign", "nonexistent"])
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_deactivate_nonexistent_category_returns_not_found(
    monkeypatch,
    category: str,
) -> None:
    context = prepare_management_context(monkeypatch)
    category_id = (
        context["foreign"]
        if category == "foreign"
        else 999999
    )

    with authenticated_as(context["lucas"]):
        response = client.delete(
            f"/api/boards/{context['board']}/categories/{category_id}"
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_deactivation_preserves_responses_and_blocks_new_writes(
    monkeypatch,
) -> None:
    context = prepare_management_context(monkeypatch)
    response_url = (
        f"/api/boards/{context['board']}"
        f"/categories/{context['a']}"
        "/responses/2026-09-16"
    )

    with authenticated_as(context["lucas"]):
        saved = client.put(response_url, json={"value": True})
        deactivated = client.delete(
            f"/api/boards/{context['board']}/categories/{context['a']}"
        )
        rejected = client.put(response_url, json={"value": False})

    assert saved.status_code == 200
    assert deactivated.status_code == 204
    assert rejected.status_code == 404
    assert rejected.json() == {"detail": "Active category not found"}

    with get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM responses WHERE category_id = %s;",
            (context["a"],),
        ).fetchone()
    assert count == (1,)


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_reorder_normalizes_positions_after_deactivation(
    monkeypatch,
) -> None:
    context = prepare_management_context(monkeypatch)

    with authenticated_as(context["lucas"]):
        client.delete(
            f"/api/boards/{context['board']}/categories/{context['b']}"
        )
        reordered = client.put(
            f"/api/boards/{context['board']}/categories/reorder",
            json={"category_ids": [context["c"], context["a"]]},
        )

    assert reordered.status_code == 200
    assert [item["name"] for item in reordered.json()] == ["C", "A"]
    assert [item["position"] for item in reordered.json()] == [0, 1]
