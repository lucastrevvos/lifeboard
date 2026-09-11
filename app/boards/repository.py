from app.database.connection import get_connection


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
