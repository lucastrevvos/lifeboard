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
