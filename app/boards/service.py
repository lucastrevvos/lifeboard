from datetime import date, timedelta

from app.boards.repository import (
    create_board,
    is_board_member,
    list_boards_for_user,
    list_weekly_board_rows,
)
from app.boards.schemas import (
    BoardResponse,
    CreateBoardRequest,
    WeeklyBoardResponse,
    WeeklyCategoryResponse,
    WeeklyDayState,
)


class WeeklyBoardPermissionError(Exception):
    pass


def get_week_range(reference_date: date) -> tuple[date, date]:
    week_start = reference_date - timedelta(days=reference_date.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


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


def get_weekly_board_for_user(
    board_id: int,
    user_id: int,
    reference_date: date,
) -> WeeklyBoardResponse:
    if not is_board_member(board_id=board_id, user_id=user_id):
        raise WeeklyBoardPermissionError

    week_start, week_end = get_week_range(reference_date)
    rows = list_weekly_board_rows(
        board_id=board_id,
        user_id=user_id,
        week_start=week_start,
        week_end=week_end,
    )

    categories: list[WeeklyCategoryResponse] = []
    category_days: dict[int, dict[date, bool]] = {}

    for row in rows:
        category_id = int(row["category_id"])

        if category_id not in category_days:
            category_days[category_id] = {}
            categories.append(
                WeeklyCategoryResponse(
                    id=category_id,
                    name=str(row["category_name"]),
                    kind=row["category_kind"],
                    position=int(row["category_position"]),
                    days=[],
                )
            )

        response_date = row["response_date"]
        response_value = row["response_value"]
        if isinstance(response_date, date) and isinstance(response_value, bool):
            category_days[category_id][response_date] = response_value

    for category in categories:
        values = category_days[category.id]
        category.days = [
            WeeklyDayState(
                date=week_start + timedelta(days=offset),
                state=(
                    "pending"
                    if week_start + timedelta(days=offset) not in values
                    else "yes"
                    if values[week_start + timedelta(days=offset)] is True
                    else "no"
                ),
            )
            for offset in range(7)
        ]

    return WeeklyBoardResponse(
        board_id=board_id,
        week_start=week_start,
        week_end=week_end,
        categories=categories,
    )
