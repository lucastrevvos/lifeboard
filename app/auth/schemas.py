from pydantic import BaseModel, Field, EmailStr, field_validator

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("name cannot be empty")

        return value

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
