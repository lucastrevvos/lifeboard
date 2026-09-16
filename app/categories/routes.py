from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.categories.schemas import (
    CategoryResponse,
    CreateCategoryRequest,
)
from app.categories.service import (
    CategoryPermissionError,
    CategoryVisibilityError,
    create_category_for_board,
    get_categories_for_board,
)


router = APIRouter(
    prefix="/api/boards",
    tags=["categories"],
)


@router.post(
    "/{board_id}/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category_route(
    board_id: int,
    data: CreateCategoryRequest,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> CategoryResponse:
    try:
        return create_category_for_board(
            board_id=board_id,
            user_id=current_user.id,
            data=data,
        )

    except CategoryPermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the board owner can create categories",
        ) from exc


@router.get(
    "/{board_id}/categories",
    response_model=list[CategoryResponse],
)
def list_categories_route(
    board_id: int,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> list[CategoryResponse]:
    try:
        return get_categories_for_board(
            board_id=board_id,
            user_id=current_user.id,
        )

    except CategoryVisibilityError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this board",
        ) from exc
