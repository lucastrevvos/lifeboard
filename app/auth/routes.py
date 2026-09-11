from fastapi import APIRouter, HTTPException, status

from app.auth.schemas import RegisterRequest, UserResponse
from app.auth.service import (
    EmailAlreadyRegisteredError,
    register_user
)

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

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

