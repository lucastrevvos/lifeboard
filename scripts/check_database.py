from app.database.connection import get_connection

def main() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

    print(f"Database connection OK: {result}")

if __name__ == "__main__":
    main()
