from datetime import date
from typing import Literal

from pydantic import BaseModel


class UpsertResponseRequest(BaseModel):
    value: bool


class ResponseState(BaseModel):
    category_id: int
    response_date: date
    subject_user_id: int | None
    state: Literal[
        "yes",
        "no",
        "pending",
    ]
