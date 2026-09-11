from app.auth.repository import DuplicateEmailError, create_user, find_user_by_email, find_user_by_id
from app.auth.schemas import RegisterRequest, UserResponse, LoginRequest
from app.security.passwords import hash_password, verify_password

class EmailAlreadyRegisteredError(Exception):
    pass

class InvalidCredentialsError(Exception):
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

def authenticate_user(data: LoginRequest) -> UserResponse:

    email = normalize_email(str(data.email))

    user = find_user_by_email(email)

    if user is None:
        raise InvalidCredentialsError

    if not verify_password(
        data.password,
        str(user["password_hash"]),
    ):
        raise InvalidCredentialsError

    return UserResponse(
        id=int(user["id"]),
        name=str(user["name"]),
        email=str(user["email"])
    )

def get_user_by_id(user_id: int) -> UserResponse | None:
    user = find_user_by_id(user_id)

    if user is None:
        return None

    return UserResponse(**user)
