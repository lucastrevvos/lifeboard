import os

import psycopg
import pytest

from app.database.connection import get_connection
from scripts.migrate import run_migrations


pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_shared_and_individual_response_uniqueness(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.autocommit = True

        connection.execute(
            """
            TRUNCATE
                responses,
                categories,
                invitations,
                board_members,
                boards,
                users
            RESTART IDENTITY CASCADE;
            """
        )

        lucas_id = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            ("Lucas", "lucas@example.test", "hash"),
        ).fetchone()[0]

        lais_id = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            ("Laís", "lais@example.test", "hash"),
        ).fetchone()[0]

        board_id = connection.execute(
            """
            INSERT INTO boards (name, created_by_user_id)
            VALUES (%s, %s)
            RETURNING id;
            """,
            ("Lucas & Laís", lucas_id),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO board_members (board_id, user_id, role)
            VALUES
                (%s, %s, 'owner'),
                (%s, %s, 'member');
            """,
            (board_id, lucas_id, board_id, lais_id),
        )

        shared_category_id = connection.execute(
            """
            INSERT INTO categories (board_id, name, kind)
            VALUES (%s, 'Amor', 'shared')
            RETURNING id;
            """,
            (board_id,),
        ).fetchone()[0]

        individual_category_id = connection.execute(
            """
            INSERT INTO categories (board_id, name, kind)
            VALUES (%s, 'Treino', 'individual')
            RETURNING id;
            """,
            (board_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO responses (
                category_id,
                subject_user_id,
                response_date,
                value,
                updated_by_user_id
            )
            VALUES (%s, NULL, DATE '2026-09-08', TRUE, %s);
            """,
            (shared_category_id, lucas_id),
        )

        with pytest.raises(psycopg.errors.UniqueViolation):
            connection.execute(
                """
                INSERT INTO responses (
                    category_id,
                    subject_user_id,
                    response_date,
                    value,
                    updated_by_user_id
                )
                VALUES (%s, NULL, DATE '2026-09-08', FALSE, %s);
                """,
                (shared_category_id, lais_id),
            )

        connection.execute(
            """
            INSERT INTO responses (
                category_id,
                subject_user_id,
                response_date,
                value,
                updated_by_user_id
            )
            VALUES
                (%s, %s, DATE '2026-09-08', TRUE, %s),
                (%s, %s, DATE '2026-09-08', FALSE, %s);
            """,
            (
                individual_category_id,
                lucas_id,
                lucas_id,
                individual_category_id,
                lais_id,
                lais_id,
            ),
        )

        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM responses
            WHERE category_id = %s;
            """,
            (individual_category_id,),
        ).fetchone()[0]

        assert count == 2
