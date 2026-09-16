import psycopg

from app.invitations.repository import (
    create_invitation,
    find_user_id_by_email,
    is_board_member,
    is_board_owner,
    accept_invitation,
    find_invitation_by_id,
    decline_invitation,
    list_pending_invitations_for_user,
)
from app.invitations.schemas import (
    CreateInvitationRequest,
    InvitationResponse,
)

from app.invitations.schemas import PendingInvitationResponse


class NotBoardOwnerError(Exception):
    pass


class InvitedUserNotFoundError(Exception):
    pass


class AlreadyBoardMemberError(Exception):
    pass


class PendingInvitationAlreadyExistsError(Exception):
    pass

class InvitationNotFoundError(Exception):
    pass

class InvitationNotForUserError(Exception):
    pass

class InvitationAlreadyProcessedError(Exception):
    pass

def accept_invitation_for_user(
    invitation_id: int,
    user_id: int,
) -> InvitationResponse:
    invitation = find_invitation_by_id(
        invitation_id
    )

    if invitation is None:
        raise InvitationNotFoundError

    if invitation["invited_user_id"] != user_id:
        raise InvitationNotForUserError

    if invitation["status"] != "pending":
        raise InvitationAlreadyProcessedError

    accepted_invitation = accept_invitation(
        invitation_id=invitation_id,
        user_id=user_id,
    )

    if accepted_invitation is None:
        raise InvitationAlreadyProcessedError

    return InvitationResponse(
        **accepted_invitation
    )

def invite_user_to_board(
    board_id: int,
    invited_by_user_id: int,
    data: CreateInvitationRequest,
) -> InvitationResponse:
    if not is_board_owner(
        board_id=board_id,
        user_id=invited_by_user_id,
    ):
        raise NotBoardOwnerError

    invited_email = str(data.email).strip().lower()

    invited_user_id = find_user_id_by_email(
        invited_email
    )

    if invited_user_id is None:
        raise InvitedUserNotFoundError

    if is_board_member(
        board_id=board_id,
        user_id=invited_user_id,
    ):
        raise AlreadyBoardMemberError

    try:
        invitation = create_invitation(
            board_id=board_id,
            invited_user_id=invited_user_id,
            invited_by_user_id=invited_by_user_id,
        )

    except psycopg.errors.UniqueViolation as exc:
        raise PendingInvitationAlreadyExistsError from exc

    return InvitationResponse(**invitation)


def decline_invitation_for_user(
    invitation_id: int,
    user_id: int,
) -> InvitationResponse:
    invitation = find_invitation_by_id(
        invitation_id
    )

    if invitation is None:
        raise InvitationNotFoundError

    if invitation["invited_user_id"] != user_id:
        raise InvitationNotForUserError

    if invitation["status"] != "pending":
        raise InvitationAlreadyProcessedError

    declined_invitation = decline_invitation(
        invitation_id=invitation_id,
        user_id=user_id,
    )

    if declined_invitation is None:
        raise InvitationAlreadyProcessedError

    return InvitationResponse(
        **declined_invitation
    )


def get_pending_invitations_for_user(
    user_id: int,
) -> list[PendingInvitationResponse]:
    invitations = list_pending_invitations_for_user(
        user_id=user_id,
    )

    return [
        PendingInvitationResponse(
            **invitation
        )
        for invitation in invitations
    ]
