from app.boards.repository import create_board, list_boards_for_user
from app.boards.schemas import BoardResponse, CreateBoardRequest


def create_board_for_user(
    data: CreateBoardRequest,
    user_id: int,
) -> BoardResponse:
    board = create_board(
        name=data.name,
        user_id=user_id,
    )

    return BoardResponse(**board)

def get_boards_for_user(
    user_id: int,
) -> list[BoardResponse]:
    boards = list_boards_for_user(user_id)

    return [
        BoardResponse(**board)
        for board in boards
    ]
