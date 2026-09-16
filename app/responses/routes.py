from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.responses.schemas import (
    ResponseState,
    UpsertResponseRequest,
)
from app.responses.service import (
    ResponseCategoryNotFoundError,
    ResponsePermissionError,
    get_response_for_user,
    save_response_for_user,
)


router = APIRouter(
    prefix="/api/boards",
    tags=["responses"],
)


@router.put(
    "/{board_id}/categories/{category_id}/responses/{response_date}",
    response_model=ResponseState,
)
def save_response_route(
    board_id: int,
    category_id: int,
    response_date: date,
    data: UpsertResponseRequest,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> ResponseState:
    try:
        return save_response_for_user(
            board_id=board_id,
            category_id=category_id,
            response_date=response_date,
            user_id=current_user.id,
            data=data,
        )

    except ResponsePermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this board",
        ) from exc

    except ResponseCategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active category not found",
        ) from exc


@router.get(
    "/{board_id}/categories/{category_id}/responses/{response_date}",
    response_model=ResponseState,
)
def get_response_route(
    board_id: int,
    category_id: int,
    response_date: date,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> ResponseState:
    try:
        return get_response_for_user(
            board_id=board_id,
            category_id=category_id,
            response_date=response_date,
            user_id=current_user.id,
        )

    except ResponsePermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this board",
        ) from exc

    except ResponseCategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active category not found",
        ) from exc
