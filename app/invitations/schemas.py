from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class CreateInvitationRequest(BaseModel):
    email: EmailStr


class InvitationResponse(BaseModel):
    id: int
    board_id: int
    invited_user_id: int
    status: str


class PendingInvitationResponse(BaseModel):
    id: int
    board_id: int
    board_name: str
    invited_by_user_id: int
    invited_by_name: str
    status: Literal["pending"]
    created_at: datetime
