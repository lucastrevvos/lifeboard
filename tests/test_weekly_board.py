import os
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.boards.service import get_week_range
from app.database.connection import get_connection
from app.main import app
from scripts.migrate import run_migrations


client = TestClient(app)


def test_week_range_normalizes_every_day_to_monday_sunday() -> None:
    expected = (date(2026, 9, 14), date(2026, 9, 20))

    for day in range(14, 21):
        assert get_week_range(date(2026, 9, day)) == expected


def test_weekly_board_requires_authentication() -> None:
    client.cookies.clear()

    response = client.get("/api/boards/1/week?date=2026-09-16")

    assert response.status_code == 401


def test_weekly_board_rejects_invalid_date() -> None:
    app.dependency_overrides[get_current_user] = lambda: UserResponse(
        id=1,
        name="Lucas",
        email="lucas@example.com",
    )
    try:
        response = client.get("/api/boards/1/week?date=banana")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def prepare_weekly_board(monkeypatch) -> tuple[int, int, int]:
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    run_migrations()

    with get_connection() as connection:
        connection.execute("TRUNCATE users RESTART IDENTITY CASCADE;")
        lucas = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES ('Lucas', 'lucas@example.com', 'not-used')
            RETURNING id;
            """
        ).fetchone()
        lais = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES ('Lais', 'lais@example.com', 'not-used')
            RETURNING id;
            """
        ).fetchone()
        outsider = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES ('Patrick', 'patrick@example.com', 'not-used')
            RETURNING id;
            """
        ).fetchone()
        assert lucas is not None and lais is not None and outsider is not None

        board = connection.execute(
            """
            INSERT INTO boards (name, created_by_user_id)
            VALUES ('Casa', %s)
            RETURNING id;
            """,
            (lucas[0],),
        ).fetchone()
        assert board is not None

        connection.execute(
            """
            INSERT INTO board_members (board_id, user_id, role)
            VALUES (%s, %s, 'owner'), (%s, %s, 'member');
            """,
            (board[0], lucas[0], board[0], lais[0]),
        )

        categories = connection.execute(
            """
            INSERT INTO categories (board_id, name, kind, position, active)
            VALUES
                (%s, 'Sem respostas', 'individual', 1, TRUE),
                (%s, 'Treino B', 'individual', 2, TRUE),
                (%s, 'Treino A', 'individual', 2, TRUE),
                (%s, 'Amor', 'shared', 3, TRUE),
                (%s, 'Inativa', 'shared', 0, FALSE)
            RETURNING id, name;
            """,
            (board[0], board[0], board[0], board[0], board[0]),
        ).fetchall()
        category_ids = {row[1]: row[0] for row in categories}

        connection.execute(
            """
            INSERT INTO responses (
                category_id, subject_user_id, response_date, value,
                updated_by_user_id
            )
            VALUES
                (%s, %s, '2026-09-14', TRUE, %s),
                (%s, %s, '2026-09-14', FALSE, %s),
                (%s, %s, '2026-09-15', FALSE, %s),
                (%s, NULL, '2026-09-16', TRUE, %s),
                (%s, NULL, '2026-09-16', TRUE, %s);
            """,
            (
                category_ids["Treino B"], lucas[0], lucas[0],
                category_ids["Treino B"], lais[0], lais[0],
                category_ids["Treino A"], lucas[0], lucas[0],
                category_ids["Amor"], lucas[0],
                category_ids["Inativa"], lucas[0],
            ),
        )

    return lucas[0], lais[0], outsider[0]


def current_user(user_id: int) -> UserResponse:
    return UserResponse(
        id=user_id,
        name="Test user",
        email=f"user{user_id}@example.com",
    )


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_weekly_board_returns_ordered_seven_day_aggregate(monkeypatch) -> None:
    lucas_id, _, _ = prepare_weekly_board(monkeypatch)
    app.dependency_overrides[get_current_user] = lambda: current_user(lucas_id)
    try:
        response = client.get("/api/boards/1/week?date=2026-09-16")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == "2026-09-14"
    assert body["week_end"] == "2026-09-20"
    assert [category["name"] for category in body["categories"]] == [
        "Sem respostas", "Treino B", "Treino A", "Amor"
    ]
    for category in body["categories"]:
        assert len(category["days"]) == 7
        assert [day["date"] for day in category["days"]] == [
            f"2026-09-{day:02d}" for day in range(14, 21)
        ]

    categories = {category["name"]: category for category in body["categories"]}
    assert [day["state"] for day in categories["Sem respostas"]["days"]] == [
        "pending"
    ] * 7
    assert categories["Treino B"]["days"][0]["state"] == "yes"
    assert categories["Treino A"]["days"][1]["state"] == "no"
    assert categories["Amor"]["days"][2]["state"] == "yes"


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_weekly_board_isolates_individual_and_shares_shared(monkeypatch) -> None:
    lucas_id, lais_id, _ = prepare_weekly_board(monkeypatch)

    results = {}
    for label, user_id in (("lucas", lucas_id), ("lais", lais_id)):
        app.dependency_overrides[get_current_user] = lambda user_id=user_id: current_user(
            user_id
        )
        try:
            response = client.get("/api/boards/1/week?date=2026-09-20")
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == 200
        results[label] = {
            category["name"]: category for category in response.json()["categories"]
        }

    assert results["lucas"]["Treino B"]["days"][0]["state"] == "yes"
    assert results["lais"]["Treino B"]["days"][0]["state"] == "no"
    assert results["lucas"]["Amor"] == results["lais"]["Amor"]


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_weekly_board_forbids_non_member(monkeypatch) -> None:
    _, _, outsider_id = prepare_weekly_board(monkeypatch)
    app.dependency_overrides[get_current_user] = lambda: current_user(outsider_id)
    try:
        response = client.get("/api/boards/1/week?date=2026-09-16")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
