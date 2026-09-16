from pydantic import BaseModel, EmailStr


class CreateInvitationRequest(BaseModel):
    email: EmailStr


class InvitationResponse(BaseModel):
    id: int
    board_id: int
    invited_user_id: int
    status: str
