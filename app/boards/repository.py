from app.database.connection import get_connection

from datetime import date


def create_board(
    name: str,
    user_id: int,
) -> dict[str, int | str]:
    with get_connection() as connection:
        with connection.transaction():
            board = connection.execute(
                """
                INSERT INTO boards (
                    name,
                    created_by_user_id
                )
                VALUES (%s, %s)
                RETURNING id, name;
                """,
                (name, user_id),
            ).fetchone()

            if board is None:
                raise RuntimeError("Board was not created")

            board_id = board[0]

            connection.execute(
                """
                INSERT INTO board_members (
                    board_id,
                    user_id,
                    role
                )
                VALUES (%s, %s, 'owner');
                """,
                (board_id, user_id),
            )

    return {
        "id": board_id,
        "name": board[1],
        "role": "owner",
    }

def list_boards_for_user(
    user_id: int,
) -> list[dict[str, int | str]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                b.id,
                b.name,
                bm.role
            FROM boards AS b
            INNER JOIN board_members AS bm
                ON bm.board_id = b.id
            WHERE bm.user_id = %s
            ORDER BY b.created_at, b.id;
            """,
            (user_id,),
        ).fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "role": row[2],
        }
        for row in rows
    ]


def is_board_member(
    board_id: int,
    user_id: int,
) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM board_members
                WHERE board_id = %s
                  AND user_id = %s
            );
            """,
            (
                board_id,
                user_id,
            ),
        ).fetchone()

    return bool(row[0]) if row is not None else False


def list_weekly_board_rows(
    board_id: int,
    user_id: int,
    week_start: date,
    week_end: date,
) -> list[dict[str, object]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                c.id,
                c.name,
                c.kind,
                c.position,
                r.response_date,
                r.value
            FROM categories AS c
            LEFT JOIN responses AS r
                ON r.category_id = c.id
               AND r.response_date BETWEEN %s AND %s
               AND (
                    (
                        c.kind = 'shared'
                        AND r.subject_user_id IS NULL
                    )
                    OR
                    (
                        c.kind = 'individual'
                        AND r.subject_user_id = %s
                    )
               )
            WHERE c.board_id = %s
              AND c.active = TRUE
            ORDER BY
                c.position,
                c.id,
                r.response_date;
            """,
            (
                week_start,
                week_end,
                user_id,
                board_id,
            ),
        ).fetchall()

    return [
        {
            "category_id": row[0],
            "category_name": row[1],
            "category_kind": row[2],
            "category_position": row[3],
            "response_date": row[4],
            "response_value": row[5],
        }
        for row in rows
    ]
