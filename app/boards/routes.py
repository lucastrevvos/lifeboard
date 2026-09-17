from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.boards.schemas import BoardResponse, CreateBoardRequest, WeeklyBoardResponse
from app.boards.service import (
    WeeklyBoardPermissionError,
    create_board_for_user,
    get_boards_for_user,
    get_weekly_board_for_user,
)


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


@router.get(
    "/{board_id}/week",
    response_model=WeeklyBoardResponse,
)
def get_weekly_board_route(
    board_id: int,
    date: date,
    current_user: UserResponse = Depends(get_current_user),
) -> WeeklyBoardResponse:
    try:
        return get_weekly_board_for_user(
            board_id=board_id,
            user_id=current_user.id,
            reference_date=date,
        )
    except WeeklyBoardPermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this board",
        ) from exc
