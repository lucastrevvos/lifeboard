from fastapi import APIRouter, HTTPException, Request, status, Response

from app.auth.schemas import RegisterRequest, UserResponse, LoginRequest
from app.auth.service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    register_user,
    authenticate_user,
    get_user_by_id
)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

@router.post(
        "/logout",
        status_code=status.HTTP_204_NO_CONTENT
)
def logout(request: Request) -> Response:
    request.session.clear()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )

@router.get(
    "/me",
    response_model=UserResponse
)
def me(request: Request) -> UserResponse:
    user_id = request.session.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user = get_user_by_id(int(user_id))

    if user is None:
        request.session.clear()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    return user

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(data: RegisterRequest) -> UserResponse:
    try:
        return register_user(data)

    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        ) from exc

@router.post(
    "/login",
    response_model=UserResponse
)
def login(data: LoginRequest) -> UserResponse:
    try:
        return authenticate_user(data)

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        ) from exc

@router.post(
    "/login",
    response_model=UserResponse
)
def login(
    data: LoginRequest,
    request: Request,
) -> UserResponse:
    try:
        user = authenticate_user(data)

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc

    request.session.clear()
    request.session["user_id"] = user.id

    return user
