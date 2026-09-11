from app.auth.repository import DuplicateEmailError, create_user
from app.auth.schemas import RegisterRequest, UserResponse
from app.security.passwords import hash_password

class EmailAlreadyRegisteredError(Exception):
    pass

def normalize_email(email: str) -> str:
    return email.strip().lower()

def register_user(data: RegisterRequest) -> UserResponse:
    email = normalize_email(str(data.email))

    hashed_password = hash_password(data.password)

    try:
        user = create_user(
            name=data.name,
            email=email,
            password_hash=hashed_password
        )
    except DuplicateEmailError as exc:
        raise EmailAlreadyRegisteredError from exc

    return UserResponse(**user)
