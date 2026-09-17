from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CreateCategoryRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=120,
    )

    kind: Literal[
        "individual",
        "shared",
    ]

    position: int = Field(
        default=0,
        ge=0,
    )

    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "name cannot be empty"
            )

        return value


class CategoryResponse(BaseModel):
    id: int
    board_id: int
    name: str
    kind: str
    position: int


class ReorderCategoriesRequest(BaseModel):
    category_ids: list[int]
