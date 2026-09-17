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
    ReorderCategoriesRequest,
)
from app.categories.service import (
    CategoryNotFoundError,
    CategoryPermissionError,
    CategoryReorderError,
    CategoryVisibilityError,
    create_category_for_board,
    deactivate_category_for_board,
    get_categories_for_board,
    reorder_categories_for_board,
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


@router.put(
    "/{board_id}/categories/reorder",
    response_model=list[CategoryResponse],
)
def reorder_categories_route(
    board_id: int,
    data: ReorderCategoriesRequest,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> list[CategoryResponse]:
    try:
        return reorder_categories_for_board(
            board_id=board_id,
            user_id=current_user.id,
            data=data,
        )

    except CategoryPermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the board owner can reorder categories",
        ) from exc

    except CategoryReorderError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "category_ids must contain all active board "
                "categories exactly once"
            ),
        ) from exc


@router.delete(
    "/{board_id}/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_category_route(
    board_id: int,
    category_id: int,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> None:
    try:
        deactivate_category_for_board(
            board_id=board_id,
            category_id=category_id,
            user_id=current_user.id,
        )

    except CategoryPermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the board owner can deactivate categories",
        ) from exc

    except CategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
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
