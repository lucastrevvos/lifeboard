from datetime import date

from app.responses.repository import (
    find_category,
    find_individual_response,
    find_shared_response,
    is_board_member,
    upsert_individual_response,
    upsert_shared_response,
)
from app.responses.schemas import (
    ResponseState,
    UpsertResponseRequest,
)


class ResponsePermissionError(Exception):
    pass


class ResponseCategoryNotFoundError(Exception):
    pass


def response_value_to_state(
    value: bool | None,
) -> str:
    if value is None:
        return "pending"

    if value is True:
        return "yes"

    return "no"


def save_response_for_user(
    board_id: int,
    category_id: int,
    response_date: date,
    user_id: int,
    data: UpsertResponseRequest,
) -> ResponseState:
    if not is_board_member(
        board_id=board_id,
        user_id=user_id,
    ):
        raise ResponsePermissionError

    category = find_category(
    board_id=board_id,
    category_id=category_id,
    )

    if category is None:
        raise ResponseCategoryNotFoundError

    if category["active"] is not True:
        raise ResponseCategoryNotFoundError

    if category["kind"] == "individual":
        value = upsert_individual_response(
            category_id=category_id,
            response_date=response_date,
            user_id=user_id,
            value=data.value,
        )

        return ResponseState(
            category_id=category_id,
            response_date=response_date,
            subject_user_id=user_id,
            state=response_value_to_state(value),
        )

    value = upsert_shared_response(
        category_id=category_id,
        response_date=response_date,
        user_id=user_id,
        value=data.value,
    )

    return ResponseState(
        category_id=category_id,
        response_date=response_date,
        subject_user_id=None,
        state=response_value_to_state(value),
    )


def get_response_for_user(
    board_id: int,
    category_id: int,
    response_date: date,
    user_id: int,
) -> ResponseState:
    if not is_board_member(
        board_id=board_id,
        user_id=user_id,
    ):
        raise ResponsePermissionError

    category = find_category(
        board_id=board_id,
        category_id=category_id,
    )

    if category is None:
        raise ResponseCategoryNotFoundError

    if category["kind"] == "individual":
        value = find_individual_response(
            category_id=category_id,
            response_date=response_date,
            user_id=user_id,
        )

        return ResponseState(
            category_id=category_id,
            response_date=response_date,
            subject_user_id=user_id,
            state=response_value_to_state(value),
        )

    value = find_shared_response(
        category_id=category_id,
        response_date=response_date,
    )

    return ResponseState(
        category_id=category_id,
        response_date=response_date,
        subject_user_id=None,
        state=response_value_to_state(value),
    )
