from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest, RegisterRequest, UserResponse
from app.auth.service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
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
    response_model=UserResponse,
)
def me(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    return current_user

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
