from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CreateBoardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("name cannot be empty")

        return value


class BoardResponse(BaseModel):
    id: int
    name: str
    role: str


class WeeklyDayState(BaseModel):
    date: date
    state: Literal["yes", "no", "pending"]


class WeeklyCategoryResponse(BaseModel):
    id: int
    name: str
    kind: Literal["individual", "shared"]
    position: int
    days: list[WeeklyDayState]


class WeeklyBoardResponse(BaseModel):
    board_id: int
    week_start: date
    week_end: date
    categories: list[WeeklyCategoryResponse]
