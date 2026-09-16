from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.invitations.schemas import (
    CreateInvitationRequest,
    InvitationResponse,
)
from app.invitations.service import (
    AlreadyBoardMemberError,
    InvitationAlreadyProcessedError,
    InvitationNotForUserError,
    InvitationNotFoundError,
    InvitedUserNotFoundError,
    NotBoardOwnerError,
    PendingInvitationAlreadyExistsError,
    accept_invitation_for_user,
    decline_invitation_for_user,
    invite_user_to_board,
)


router = APIRouter(
    prefix="/api/boards",
    tags=["invitations"],
)


@router.post(
    "/{board_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    board_id: int,
    data: CreateInvitationRequest,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> InvitationResponse:
    try:
        return invite_user_to_board(
            board_id=board_id,
            invited_by_user_id=current_user.id,
            data=data,
        )

    except NotBoardOwnerError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the board owner can invite users",
        ) from exc

    except InvitedUserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invited user not found",
        ) from exc

    except AlreadyBoardMemberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a board member",
        ) from exc

    except PendingInvitationAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pending invitation already exists",
        ) from exc


@router.post(
    "/invitations/{invitation_id}/accept",
    response_model=InvitationResponse,
)
def accept_invitation_route(
    invitation_id: int,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> InvitationResponse:
    try:
        return accept_invitation_for_user(
            invitation_id=invitation_id,
            user_id=current_user.id,
        )

    except InvitationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        ) from exc

    except InvitationNotForUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitation does not belong to this user",
        ) from exc

    except InvitationAlreadyProcessedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invitation has already been processed",
        ) from exc


@router.post(
    "/invitations/{invitation_id}/decline",
    response_model=InvitationResponse,
)
def decline_invitation_route(
    invitation_id: int,
    current_user: UserResponse = Depends(
        get_current_user
    ),
) -> InvitationResponse:
    try:
        return decline_invitation_for_user(
            invitation_id=invitation_id,
            user_id=current_user.id,
        )

    except InvitationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        ) from exc

    except InvitationNotForUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitation does not belong to this user",
        ) from exc

    except InvitationAlreadyProcessedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invitation has already been processed",
        ) from exc
