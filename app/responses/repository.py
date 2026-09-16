from datetime import date

from app.database.connection import get_connection

def is_board_member(
    board_id: int,
    user_id: int,
) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM board_members
            WHERE board_id = %s
              AND user_id = %s;
            """,
            (
                board_id,
                user_id,
            ),
        ).fetchone()

    return row is not None


def find_category(
    board_id: int,
    category_id: int,
) -> dict[str, int | str | bool] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                board_id,
                kind,
                active
            FROM categories
            WHERE id = %s
              AND board_id = %s;
            """,
            (
                category_id,
                board_id,
            ),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "board_id": row[1],
        "kind": row[2],
        "active": row[3],
    }


def upsert_individual_response(
    category_id: int,
    response_date: date,
    user_id: int,
    value: bool,
) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO responses (
                category_id,
                subject_user_id,
                response_date,
                value,
                updated_by_user_id
            )
            VALUES (%s, %s, %s, %s, %s)

            ON CONFLICT (
                category_id,
                response_date,
                subject_user_id
            )
            WHERE subject_user_id IS NOT NULL

            DO UPDATE SET
                value = EXCLUDED.value,
                updated_by_user_id = EXCLUDED.updated_by_user_id,
                updated_at = NOW()

            RETURNING value;
            """,
            (
                category_id,
                user_id,
                response_date,
                value,
                user_id,
            ),
        ).fetchone()

    if row is None:
        raise RuntimeError(
            "Response was not saved"
        )

    return row[0]


def upsert_shared_response(
    category_id: int,
    response_date: date,
    user_id: int,
    value: bool,
) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO responses (
                category_id,
                subject_user_id,
                response_date,
                value,
                updated_by_user_id
            )
            VALUES (%s, NULL, %s, %s, %s)

            ON CONFLICT (
                category_id,
                response_date
            )
            WHERE subject_user_id IS NULL

            DO UPDATE SET
                value = EXCLUDED.value,
                updated_by_user_id = EXCLUDED.updated_by_user_id,
                updated_at = NOW()

            RETURNING value;
            """,
            (
                category_id,
                response_date,
                value,
                user_id,
            ),
        ).fetchone()

    if row is None:
        raise RuntimeError(
            "Response was not saved"
        )

    return row[0]


def find_individual_response(
    category_id: int,
    response_date: date,
    user_id: int,
) -> bool | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT value
            FROM responses
            WHERE category_id = %s
              AND response_date = %s
              AND subject_user_id = %s;
            """,
            (
                category_id,
                response_date,
                user_id,
            ),
        ).fetchone()

    if row is None:
        return None

    return row[0]


def find_shared_response(
    category_id: int,
    response_date: date,
) -> bool | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT value
            FROM responses
            WHERE category_id = %s
              AND response_date = %s
              AND subject_user_id IS NULL;
            """,
            (
                category_id,
                response_date,
            ),
        ).fetchone()

    if row is None:
        return None

    return row[0]
