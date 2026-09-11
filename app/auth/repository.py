import psycopg

from app.database.connection import get_connection

class DuplicateEmailError(Exception):
    pass

def create_user(
        name: str,
        email: str,
        password_hash: str
) -> dict[str, int | str]:
    try:
        with get_connection() as connection:
            row = connection.execute(
                """
                INSERT INTO users (
                    name,
                    email,
                    password_hash
                )
                VALUES (%s, %s, %s)
                RETURNING id, name, email;
                """,
                (name, email, password_hash)
            ).fetchone()

    except psycopg.errors.UniqueViolation as exc:
        raise DuplicateEmailError from exc

    if row is None:
        raise RuntimeError("User was not created")

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2]
    }

def find_user_by_email(
        email: str
) -> dict[str, int | str] | None:
    with get_connection() as connection:
        row = connection.execute(
             """
            SELECT
                id,
                name,
                email,
                password_hash
            FROM users
            WHERE email = %s;
            """,
            (email,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "password_hash": row[3]
    }

def find_user_by_id(
        user_id: str
) -> dict[str, int | str] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                name,
                email
            FROM users
            WHERE id = %s;
            """,
            (user_id,)
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2]
    }
