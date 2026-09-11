import pytest
from pydantic import ValidationError

from app.auth.schemas import LoginRequest, RegisterRequest, UserResponse
from app.auth.service import normalize_email

def test_normalize_email() -> None:
    assert normalize_email("   Lucas@Example.COM  ") == "lucas@example.com"

def test_register_request_normalizes_name() -> None:
    request = RegisterRequest(
        name="   Lucas Amaral   ",
        email="lucas@example.com",
        password="secret123"
    )

    assert request.name == "Lucas Amaral"

def test_register_request_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="Lucas",
            email="lucas@example.com",
            password="123"
        )

def test_user_response_uses_integer_id() -> None:
    user = UserResponse(
        id=1,
        name="Lucas Amaral",
        email="lucas@example.com",
    )

    assert user.id == 1
    assert isinstance(user.id, int)
