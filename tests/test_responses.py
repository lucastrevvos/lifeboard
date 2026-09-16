import os
from datetime import date

import pytest

from app.database.connection import get_connection
from app.responses.schemas import UpsertResponseRequest
from app.responses.service import (
    get_response_for_user,
    save_response_for_user,
    ResponseCategoryNotFoundError,
    ResponsePermissionError,
)


from scripts.migrate import run_migrations


pytestmark = pytest.mark.integration

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def prepare_response_context(
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

        assert lucas is not None
        assert lais is not None

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

        category = connection.execute(
            """
            INSERT INTO categories (
                board_id,
                name,
                kind,
                position
            )
            VALUES (%s, %s, 'individual', 1)
            RETURNING id;
            """,
            (
                board[0],
                "Treino",
            ),
        ).fetchone()

        assert category is not None

    return (
        lucas[0],
        lais[0],
        board[0],
        category[0],
    )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_individual_responses_are_independent_per_user(
    monkeypatch,
) -> None:
    (
        lucas_id,
        lais_id,
        board_id,
        category_id,
    ) = prepare_response_context(monkeypatch)

    response_date = date(
        2026,
        9,
        16,
    )

    lucas_before = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lucas_id,
    )

    lais_before = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lais_id,
    )

    assert lucas_before.state == "pending"
    assert lais_before.state == "pending"

    lucas_yes = save_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lucas_id,
        data=UpsertResponseRequest(
            value=True
        ),
    )

    assert lucas_yes.state == "yes"
    assert lucas_yes.subject_user_id == lucas_id

    lais_still_pending = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lais_id,
    )

    assert lais_still_pending.state == "pending"

    lucas_no = save_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lucas_id,
        data=UpsertResponseRequest(
            value=False
        ),
    )

    assert lucas_no.state == "no"

    lais_after = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lais_id,
    )

    assert lais_after.state == "pending"

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                subject_user_id,
                value
            FROM responses
            WHERE category_id = %s
              AND response_date = %s
            ORDER BY id;
            """,
            (
                category_id,
                response_date,
            ),
        ).fetchall()

    assert rows == [
        (
            lucas_id,
            False,
        )
    ]


def prepare_shared_response_context(
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

        assert lucas is not None
        assert lais is not None

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

        category = connection.execute(
            """
            INSERT INTO categories (
                board_id,
                name,
                kind,
                position
            )
            VALUES (%s, %s, 'shared', 1)
            RETURNING id;
            """,
            (
                board[0],
                "Amor",
            ),
        ).fetchone()

        assert category is not None

    return (
        lucas[0],
        lais[0],
        board[0],
        category[0],
    )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_shared_response_is_shared_between_members(
    monkeypatch,
) -> None:
    (
        lucas_id,
        lais_id,
        board_id,
        category_id,
    ) = prepare_shared_response_context(
        monkeypatch
    )

    response_date = date(
        2026,
        9,
        16,
    )

    lucas_before = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lucas_id,
    )

    lais_before = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lais_id,
    )

    assert lucas_before.state == "pending"
    assert lais_before.state == "pending"

    lucas_yes = save_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lucas_id,
        data=UpsertResponseRequest(
            value=True
        ),
    )

    assert lucas_yes.state == "yes"
    assert lucas_yes.subject_user_id is None

    lais_sees_yes = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lais_id,
    )

    assert lais_sees_yes.state == "yes"
    assert lais_sees_yes.subject_user_id is None

    lais_no = save_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lais_id,
        data=UpsertResponseRequest(
            value=False
        ),
    )

    assert lais_no.state == "no"
    assert lais_no.subject_user_id is None

    lucas_sees_no = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lucas_id,
    )

    assert lucas_sees_no.state == "no"

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                subject_user_id,
                value,
                updated_by_user_id
            FROM responses
            WHERE category_id = %s
              AND response_date = %s;
            """,
            (
                category_id,
                response_date,
            ),
        ).fetchall()

    assert rows == [
        (
            None,
            False,
            lais_id,
        )
    ]


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_non_member_cannot_read_or_write_response(
    monkeypatch,
) -> None:
    (
        lucas_id,
        _,
        board_id,
        category_id,
    ) = prepare_response_context(monkeypatch)

    response_date = date(
        2026,
        9,
        16,
    )

    with get_connection() as connection:
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

    assert patrick is not None

    patrick_id = patrick[0]

    with pytest.raises(
        ResponsePermissionError
    ):
        get_response_for_user(
            board_id=board_id,
            category_id=category_id,
            response_date=response_date,
            user_id=patrick_id,
        )

    with pytest.raises(
        ResponsePermissionError
    ):
        save_response_for_user(
            board_id=board_id,
            category_id=category_id,
            response_date=response_date,
            user_id=patrick_id,
            data=UpsertResponseRequest(
                value=True
            ),
        )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_inactive_category_cannot_receive_response(
    monkeypatch,
) -> None:
    (
        lucas_id,
        _,
        board_id,
        category_id,
    ) = prepare_response_context(monkeypatch)

    response_date = date(
        2026,
        9,
        16,
    )

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE categories
            SET active = FALSE
            WHERE id = %s;
            """,
            (category_id,),
        )

    with pytest.raises(
        ResponseCategoryNotFoundError
    ):
        save_response_for_user(
            board_id=board_id,
            category_id=category_id,
            response_date=response_date,
            user_id=lucas_id,
            data=UpsertResponseRequest(
                value=True
            ),
        )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_inactive_category_keeps_response_history_readable(
    monkeypatch,
) -> None:
    (
        lucas_id,
        _,
        board_id,
        category_id,
    ) = prepare_response_context(monkeypatch)

    response_date = date(
        2026,
        9,
        16,
    )

    saved = save_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lucas_id,
        data=UpsertResponseRequest(
            value=True
        ),
    )

    assert saved.state == "yes"

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE categories
            SET active = FALSE
            WHERE id = %s;
            """,
            (category_id,),
        )

    historical = get_response_for_user(
        board_id=board_id,
        category_id=category_id,
        response_date=response_date,
        user_id=lucas_id,
    )

    assert historical.state == "yes"


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_individual_response_flow_through_api(
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

    register = client.post(
        "/api/auth/register",
        json={
            "name": "Lucas",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert register.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert login.status_code == 200

    board = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    assert board.status_code == 201

    board_id = board.json()["id"]

    category = client.post(
        f"/api/boards/{board_id}/categories",
        json={
            "name": "Treino",
            "kind": "individual",
            "position": 1,
        },
    )

    assert category.status_code == 201

    category_id = category.json()["id"]

    response_url = (
        f"/api/boards/{board_id}"
        f"/categories/{category_id}"
        f"/responses/2026-09-16"
    )

    pending = client.get(response_url)

    assert pending.status_code == 200
    assert pending.json()["state"] == "pending"

    yes = client.put(
        response_url,
        json={
            "value": True,
        },
    )

    assert yes.status_code == 200
    assert yes.json()["state"] == "yes"

    yes_again = client.get(response_url)

    assert yes_again.status_code == 200
    assert yes_again.json()["state"] == "yes"

    no = client.put(
        response_url,
        json={
            "value": False,
        },
    )

    assert no.status_code == 200
    assert no.json()["state"] == "no"

    no_again = client.get(response_url)

    assert no_again.status_code == 200
    assert no_again.json()["state"] == "no"


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_shared_response_is_visible_to_other_member_through_api(
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
        "/api/auth/register",
        json={
            "name": "Laís",
            "email": "lais@example.com",
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

    board = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    board_id = board.json()["id"]

    invitation = client.post(
        f"/api/boards/{board_id}/invitations",
        json={
            "email": "lais@example.com",
        },
    )

    assert invitation.status_code == 201

    invitation_id = invitation.json()["id"]

    category = client.post(
        f"/api/boards/{board_id}/categories",
        json={
            "name": "Amor",
            "kind": "shared",
            "position": 1,
        },
    )

    assert category.status_code == 201

    category_id = category.json()["id"]

    response_url = (
        f"/api/boards/{board_id}"
        f"/categories/{category_id}"
        f"/responses/2026-09-16"
    )

    lucas_yes = client.put(
        response_url,
        json={
            "value": True,
        },
    )

    assert lucas_yes.status_code == 200
    assert lucas_yes.json()["state"] == "yes"
    assert lucas_yes.json()["subject_user_id"] is None

    client.cookies.clear()

    client.post(
        "/api/auth/login",
        json={
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    accept = client.post(
        f"/api/boards/invitations/{invitation_id}/accept"
    )

    assert accept.status_code == 200

    lais_reads = client.get(response_url)

    assert lais_reads.status_code == 200
    assert lais_reads.json()["state"] == "yes"
    assert lais_reads.json()["subject_user_id"] is None


def test_response_route_rejects_invalid_date() -> None:
    client.cookies.clear()

    response = client.get(
        "/api/boards/1/categories/1/responses/banana"
    )

    assert response.status_code in {
        401,
        422,
    }
