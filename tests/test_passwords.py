from app.security.passwords import hash_password, verify_password

def test_hash_password_does_not_store_plaintext() -> None:
    password = "life-board-secret"

    hashed = hash_password(password)

    assert hashed != password

def test_verify_password_accepts_correct_password() -> None:
    password = "life-board-secret"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True

def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("correct-password")

    assert verify_password("wrong-password", hashed) is False
