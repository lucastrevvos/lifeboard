from app.database.connection import get_connection


def is_board_owner(
    board_id: int,
    user_id: int,
) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM board_members
            WHERE board_id = %s
              AND user_id = %s
              AND role = 'owner';
            """,
            (
                board_id,
                user_id,
            ),
        ).fetchone()

    return row is not None


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

def create_category(
    board_id: int,
    name: str,
    kind: str,
    position: int,
) -> dict[str, int | str]:
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO categories (
                board_id,
                name,
                kind,
                position
            )
            VALUES (%s, %s, %s, %s)
            RETURNING
                id,
                board_id,
                name,
                kind,
                position;
            """,
            (
                board_id,
                name,
                kind,
                position,
            ),
        ).fetchone()

    if row is None:
        raise RuntimeError(
            "Category was not created"
        )

    return {
        "id": row[0],
        "board_id": row[1],
        "name": row[2],
        "kind": row[3],
        "position": row[4],
    }

def list_active_categories(
    board_id: int,
) -> list[dict[str, int | str]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                board_id,
                name,
                kind,
                position
            FROM categories
            WHERE board_id = %s
              AND active = TRUE
            ORDER BY
                position,
                id;
            """,
            (board_id,),
        ).fetchall()

    return [
        {
            "id": row[0],
            "board_id": row[1],
            "name": row[2],
            "kind": row[3],
            "position": row[4],
        }
        for row in rows
    ]


def reorder_active_categories(
    board_id: int,
    category_ids: list[int],
) -> list[dict[str, int | str]] | None:
    with get_connection() as connection:
        with connection.transaction():
            locked_rows = connection.execute(
                """
                SELECT id
                FROM categories
                WHERE board_id = %s
                  AND active = TRUE
                ORDER BY id
                FOR UPDATE;
                """,
                (board_id,),
            ).fetchall()

            active_ids = [row[0] for row in locked_rows]

            if (
                len(category_ids) != len(active_ids)
                or set(category_ids) != set(active_ids)
            ):
                return None

            for position, category_id in enumerate(category_ids):
                connection.execute(
                    """
                    UPDATE categories
                    SET position = %s
                    WHERE id = %s
                      AND board_id = %s
                      AND active = TRUE;
                    """,
                    (
                        position,
                        category_id,
                        board_id,
                    ),
                )

            rows = connection.execute(
                """
                SELECT
                    id,
                    board_id,
                    name,
                    kind,
                    position
                FROM categories
                WHERE board_id = %s
                  AND active = TRUE
                ORDER BY position, id;
                """,
                (board_id,),
            ).fetchall()

    return [
        {
            "id": row[0],
            "board_id": row[1],
            "name": row[2],
            "kind": row[3],
            "position": row[4],
        }
        for row in rows
    ]


def deactivate_category(
    board_id: int,
    category_id: int,
) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE categories
            SET active = FALSE
            WHERE id = %s
              AND board_id = %s
              AND active = TRUE
            RETURNING id;
            """,
            (
                category_id,
                board_id,
            ),
        ).fetchone()

    return row is not None
