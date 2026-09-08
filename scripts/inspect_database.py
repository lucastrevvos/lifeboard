from app.database.connection import get_connection

def main() -> None:
    with get_connection() as connection:
        tables = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
        ).fetchall()

    print("Tables:")

    for (table_name,) in tables:
        print(f"- {table_name}")

if __name__ == "__main__":
    main()
