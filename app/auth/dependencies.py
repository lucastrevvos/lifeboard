from fastapi import HTTPException, Request, status

from app.auth.schemas import UserResponse
from app.auth.service import get_user_by_id


def get_current_user(request: Request) -> UserResponse:
    user_id = request.session.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = get_user_by_id(int(user_id))

    if user is None:
        request.session.clear()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user
