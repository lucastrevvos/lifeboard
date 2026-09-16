from app.categories.repository import (
    create_category,
    is_board_member,
    is_board_owner,
    list_active_categories,
)
from app.categories.schemas import (
    CategoryResponse,
    CreateCategoryRequest,
)


class CategoryPermissionError(Exception):
    pass


class CategoryVisibilityError(Exception):
    pass

def create_category_for_board(
    board_id: int,
    user_id: int,
    data: CreateCategoryRequest,
) -> CategoryResponse:
    if not is_board_owner(
        board_id=board_id,
        user_id=user_id,
    ):
        raise CategoryPermissionError

    category = create_category(
        board_id=board_id,
        name=data.name,
        kind=data.kind,
        position=data.position,
    )

    return CategoryResponse(
        **category
    )


def get_categories_for_board(
    board_id: int,
    user_id: int,
) -> list[CategoryResponse]:
    if not is_board_member(
        board_id=board_id,
        user_id=user_id,
    ):
        raise CategoryVisibilityError

    categories = list_active_categories(
        board_id=board_id
    )

    return [
        CategoryResponse(**category)
        for category in categories
    ]
