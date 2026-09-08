from hashlib import sha256
from pathlib import Path

from app.database.connection import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = BASE_DIR / "database" / "migrations"

def calculate_checksum(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()

def ensure_migrations_table(connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            checksum TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

def get_applied_migrations(connection) -> dict[str, str]:
    rows = connection.execute(
        """
        SELECT version, checksum
        FROM schema_migrations;
        """
    ).fetchall()

    return {
        version: checksum
        for version, checksum in rows
    }

def run_migrations() -> None:
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    with get_connection() as connection:
        connection.autocommit = True

        ensure_migrations_table(connection)

        applied_migrations = get_applied_migrations(connection)

        for migration_file in migration_files:
            version = migration_file.name
            migration_sql = migration_file.read_text(encoding="utf-8")
            checksum = calculate_checksum(migration_sql)

            if version in applied_migrations:
                if applied_migrations[version] != checksum:
                    raise RuntimeError(
                        f"Applied migration was modified: {version}"
                    )

                print(f"Already applied: {version}")
                continue

            print(f"Applying: {version}")

            with connection.transaction():
                connection.execute(migration_sql)

                connection.execute(
                    """
                    INSERT INTO schema_migrations (version, checksum)
                    VALUES (%s, %s)
                    """,
                    (version, checksum)
                )

            print(f"Applied: {version}")

if __name__ == "__main__":
    run_migrations()

