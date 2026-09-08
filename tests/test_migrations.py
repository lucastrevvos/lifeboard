from scripts.migrate import calculate_checksum

def test_checksum_is_deterministic() -> None:
    sql = "CREATE TABLE example (id INTEGER);"

    first = calculate_checksum(sql)
    second = calculate_checksum(sql)

    assert first == second

def test_checksum_changes_when_migration_changes() -> None:
    original = "CREATE TABLE example (id INTEGER);"
    modified = "CREATE TABLE example (id BIGINT);"

    assert calculate_checksum(original) != calculate_checksum(modified)
