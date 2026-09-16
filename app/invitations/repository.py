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

def find_user_id_by_email(
    email: str,
) -> int | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s;
            """,
            (email,),
        ).fetchone()

    if row is None:
        return None

    return row[0]


def create_invitation(
    board_id: int,
    invited_user_id: int,
    invited_by_user_id: int,
) -> dict[str, int | str]:
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO invitations (
                board_id,
                invited_user_id,
                invited_by_user_id
            )
            VALUES (%s, %s, %s)
            RETURNING
                id,
                board_id,
                invited_user_id,
                status;
            """,
            (
                board_id,
                invited_user_id,
                invited_by_user_id,
            ),
        ).fetchone()

    if row is None:
        raise RuntimeError("Invitation was not created")

    return {
        "id": row[0],
        "board_id": row[1],
        "invited_user_id": row[2],
        "status": row[3],
    }


def find_invitation_by_id(
    invitation_id: int,
) -> dict[str, int | str] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                board_id,
                invited_user_id,
                status
            FROM invitations
            WHERE id = %s;
            """,
            (invitation_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "board_id": row[1],
        "invited_user_id": row[2],
        "status": row[3],
    }

def accept_invitation(
    invitation_id: int,
    user_id: int,
) -> dict[str, int | str] | None:
    with get_connection() as connection:
        with connection.transaction():
            invitation = connection.execute(
                """
                UPDATE invitations
                SET
                    status = 'accepted',
                    responded_at = NOW()
                WHERE id = %s
                  AND invited_user_id = %s
                  AND status = 'pending'
                RETURNING
                    id,
                    board_id,
                    invited_user_id,
                    status;
                """,
                (
                    invitation_id,
                    user_id,
                ),
            ).fetchone()

            if invitation is None:
                return None

            connection.execute(
                """
                INSERT INTO board_members (
                    board_id,
                    user_id,
                    role
                )
                VALUES (%s, %s, 'member');
                """,
                (
                    invitation[1],
                    user_id,
                ),
            )

    return {
        "id": invitation[0],
        "board_id": invitation[1],
        "invited_user_id": invitation[2],
        "status": invitation[3],
    }


def decline_invitation(
    invitation_id: int,
    user_id: int,
) -> dict[str, int | str] | None:
    with get_connection() as connection:
        invitation = connection.execute(
            """
            UPDATE invitations
            SET
                status = 'declined',
                responded_at = NOW()
            WHERE id = %s
              AND invited_user_id = %s
              AND status = 'pending'
            RETURNING
                id,
                board_id,
                invited_user_id,
                status;
            """,
            (
                invitation_id,
                user_id,
            ),
        ).fetchone()

    if invitation is None:
        return None

    return {
        "id": invitation[0],
        "board_id": invitation[1],
        "invited_user_id": invitation[2],
        "status": invitation[3],
    }
