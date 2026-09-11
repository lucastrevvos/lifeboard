from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.boards.schemas import BoardResponse, CreateBoardRequest
from app.boards.service import create_board_for_user, get_boards_for_user




router = APIRouter(
    prefix="/api/boards",
    tags=["boards"],
)


@router.post(
    "",
    response_model=BoardResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_board(
    data: CreateBoardRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> BoardResponse:
    return create_board_for_user(
        data=data,
        user_id=current_user.id,
    )

@router.get(
    "",
    response_model=list[BoardResponse],
)
def list_boards(
    current_user: UserResponse = Depends(get_current_user),
) -> list[BoardResponse]:
    return get_boards_for_user(
        user_id=current_user.id,
    )
