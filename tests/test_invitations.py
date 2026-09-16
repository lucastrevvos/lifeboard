import os

import psycopg
import pytest

from app.database.connection import get_connection
from scripts.migrate import run_migrations

from app.invitations.schemas import CreateInvitationRequest
from app.invitations.service import (
    AlreadyBoardMemberError,
    InvitationAlreadyProcessedError,
    InvitationNotForUserError,
    NotBoardOwnerError,
    PendingInvitationAlreadyExistsError,
    accept_invitation_for_user,
    invite_user_to_board,
    decline_invitation_for_user,
    get_pending_invitations_for_user
)

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_accepted_invitation_cannot_be_processed_again(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    invitation = invite_user_to_board(
        board_id=board_id,
        invited_by_user_id=lucas_id,
        data=CreateInvitationRequest(
            email="lais@example.com",
        ),
    )

    accept_invitation_for_user(
        invitation_id=invitation.id,
        user_id=lais_id,
    )

    with pytest.raises(InvitationAlreadyProcessedError):
        accept_invitation_for_user(
            invitation_id=invitation.id,
            user_id=lais_id,
        )

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_invited_user_can_accept_invitation(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    invitation = invite_user_to_board(
        board_id=board_id,
        invited_by_user_id=lucas_id,
        data=CreateInvitationRequest(
            email="lais@example.com",
        ),
    )

    accepted = accept_invitation_for_user(
        invitation_id=invitation.id,
        user_id=lais_id,
    )

    assert accepted.status == "accepted"

    with get_connection() as connection:
        invitation_row = connection.execute(
            """
            SELECT
                status,
                responded_at
            FROM invitations
            WHERE id = %s;
            """,
            (invitation.id,),
        ).fetchone()

        membership_row = connection.execute(
            """
            SELECT role
            FROM board_members
            WHERE board_id = %s
              AND user_id = %s;
            """,
            (
                board_id,
                lais_id,
            ),
        ).fetchone()

    assert invitation_row is not None
    assert invitation_row[0] == "accepted"
    assert invitation_row[1] is not None

    assert membership_row == ("member",)


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_other_user_cannot_accept_invitation(
    monkeypatch,
) -> None:
    lucas_id, _, board_id = prepare_invitation_context(
        monkeypatch
    )

    invitation = invite_user_to_board(
        board_id=board_id,
        invited_by_user_id=lucas_id,
        data=CreateInvitationRequest(
            email="lais@example.com",
        ),
    )

    with pytest.raises(InvitationNotForUserError):
        accept_invitation_for_user(
            invitation_id=invitation.id,
            user_id=lucas_id,
        )

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_member_cannot_invite_through_api(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE users
            RESTART IDENTITY CASCADE;
            """
        )

    client.cookies.clear()

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    client.post(
        "/api/auth/register",
        json={
            "name": "Laís",
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    client.post(
        "/api/auth/register",
        json={
            "name": "Patrick",
            "email": "patrick@example.com",
            "password": "secret123",
        },
    )

    client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    board_response = client.post(
        "/api/boards",
        json={"name": "Casa"},
    )

    assert board_response.status_code == 201

    board_id = board_response.json()["id"]

    with get_connection() as connection:
        lais = connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s;
            """,
            ("lais@example.com",),
        ).fetchone()

        assert lais is not None

        connection.execute(
            """
            INSERT INTO board_members (
                board_id,
                user_id,
                role
            )
            VALUES (%s, %s, 'member');
            """,
            (
                board_id,
                lais[0],
            ),
        )

    client.cookies.clear()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200

    response = client.post(
        f"/api/boards/{board_id}/invitations",
        json={
            "email": "patrick@example.com",
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Only the board owner can invite users",
    }

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)

def test_owner_can_invite_user_through_api(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE users
            RESTART IDENTITY CASCADE;
            """
        )

    client.cookies.clear()

    lucas_response = client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert lucas_response.status_code == 201

    lais_response = client.post(
        "/api/auth/register",
        json={
            "name": "Laís",
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    assert lais_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200

    board_response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    assert board_response.status_code == 201

    board_id = board_response.json()["id"]

    invitation_response = client.post(
        f"/api/boards/{board_id}/invitations",
        json={
            "email": "lais@example.com",
        },
    )

    assert invitation_response.status_code == 201

    body = invitation_response.json()

    assert body["board_id"] == board_id
    assert body["status"] == "pending"




pytestmark = pytest.mark.integration

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_owner_cannot_create_duplicate_pending_invitation(
    monkeypatch,
) -> None:
    lucas_id, _, board_id = prepare_invitation_context(
        monkeypatch
    )

    data = CreateInvitationRequest(
        email="lais@example.com",
    )

    first_invitation = invite_user_to_board(
        board_id=board_id,
        invited_by_user_id=lucas_id,
        data=data,
    )

    assert first_invitation.status == "pending"

    with pytest.raises(
        PendingInvitationAlreadyExistsError
    ):
        invite_user_to_board(
            board_id=board_id,
            invited_by_user_id=lucas_id,
            data=data,
        )

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_owner_can_invite_registered_user(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    invitation = invite_user_to_board(
        board_id=board_id,
        invited_by_user_id=lucas_id,
        data=CreateInvitationRequest(
            email="lais@example.com",
        ),
    )

    assert invitation.board_id == board_id
    assert invitation.invited_user_id == lais_id
    assert invitation.status == "pending"

def prepare_invitation_context(monkeypatch) -> tuple[int, int, int]:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE users
            RESTART IDENTITY CASCADE;
            """
        )

        lucas = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash
            )
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                "Lucas Amaral",
                "lucas@example.com",
                "not-used",
            ),
        ).fetchone()

        lais = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash
            )
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                "Laís",
                "lais@example.com",
                "not-used",
            ),
        ).fetchone()

        assert lucas is not None
        assert lais is not None

        board = connection.execute(
            """
            INSERT INTO boards (
                name,
                created_by_user_id
            )
            VALUES (%s, %s)
            RETURNING id;
            """,
            (
                "Casa",
                lucas[0],
            ),
        ).fetchone()

        assert board is not None

        connection.execute(
            """
            INSERT INTO board_members (
                board_id,
                user_id,
                role
            )
            VALUES (%s, %s, 'owner');
            """,
            (
                board[0],
                lucas[0],
            ),
        )

    return lucas[0], lais[0], board[0]

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_only_one_pending_invitation_per_board_user(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO invitations (
                board_id,
                invited_user_id,
                invited_by_user_id
            )
            VALUES (%s, %s, %s);
            """,
            (
                board_id,
                lais_id,
                lucas_id,
            ),
        )

    with pytest.raises(psycopg.errors.UniqueViolation):
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO invitations (
                    board_id,
                    invited_user_id,
                    invited_by_user_id
                )
                VALUES (%s, %s, %s);
                """,
                (
                    board_id,
                    lais_id,
                    lucas_id,
                ),
            )

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM invitations
            WHERE board_id = %s
              AND invited_user_id = %s
              AND status = 'pending';
            """,
            (
                board_id,
                lais_id,
            ),
        ).fetchone()

    assert row is not None
    assert row[0] == 1

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_new_invitation_allowed_after_decline(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    with get_connection() as connection:
        invitation = connection.execute(
            """
            INSERT INTO invitations (
                board_id,
                invited_user_id,
                invited_by_user_id
            )
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                board_id,
                lais_id,
                lucas_id,
            ),
        ).fetchone()

        assert invitation is not None

        connection.execute(
            """
            UPDATE invitations
            SET status = 'declined'
            WHERE id = %s;
            """,
            (invitation[0],),
        )

    with get_connection() as connection:
        second_invitation = connection.execute(
            """
            INSERT INTO invitations (
                board_id,
                invited_user_id,
                invited_by_user_id
            )
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                board_id,
                lais_id,
                lucas_id,
            ),
        ).fetchone()

    assert second_invitation is not None


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_member_cannot_invite_user(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    with get_connection() as connection:
        patrick = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash
            )
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                "Patrick",
                "patrick@example.com",
                "not-used",
            ),
        ).fetchone()

        assert patrick is not None

        connection.execute(
            """
            INSERT INTO board_members (
                board_id,
                user_id,
                role
            )
            VALUES (%s, %s, 'member');
            """,
            (
                board_id,
                lais_id,
            ),
        )

    with pytest.raises(NotBoardOwnerError):
        invite_user_to_board(
            board_id=board_id,
            invited_by_user_id=lais_id,
            data=CreateInvitationRequest(
                email="patrick@example.com",
            ),
        )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_owner_cannot_invite_existing_member(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO board_members (
                board_id,
                user_id,
                role
            )
            VALUES (%s, %s, 'member');
            """,
            (
                board_id,
                lais_id,
            ),
        )

    with pytest.raises(AlreadyBoardMemberError):
        invite_user_to_board(
            board_id=board_id,
            invited_by_user_id=lucas_id,
            data=CreateInvitationRequest(
                email="lais@example.com",
            ),
        )

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_invited_user_can_decline_invitation(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    invitation = invite_user_to_board(
        board_id=board_id,
        invited_by_user_id=lucas_id,
        data=CreateInvitationRequest(
            email="lais@example.com",
        ),
    )

    declined = decline_invitation_for_user(
        invitation_id=invitation.id,
        user_id=lais_id,
    )

    assert declined.status == "declined"

    with get_connection() as connection:
        invitation_row = connection.execute(
            """
            SELECT
                status,
                responded_at
            FROM invitations
            WHERE id = %s;
            """,
            (invitation.id,),
        ).fetchone()

        membership_row = connection.execute(
            """
            SELECT role
            FROM board_members
            WHERE board_id = %s
              AND user_id = %s;
            """,
            (
                board_id,
                lais_id,
            ),
        ).fetchone()

    assert invitation_row is not None
    assert invitation_row[0] == "declined"
    assert invitation_row[1] is not None

    assert membership_row is None

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_declined_invitation_cannot_be_processed_again(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    invitation = invite_user_to_board(
        board_id=board_id,
        invited_by_user_id=lucas_id,
        data=CreateInvitationRequest(
            email="lais@example.com",
        ),
    )

    decline_invitation_for_user(
        invitation_id=invitation.id,
        user_id=lais_id,
    )

    with pytest.raises(
        InvitationAlreadyProcessedError
    ):
        decline_invitation_for_user(
            invitation_id=invitation.id,
            user_id=lais_id,
        )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_accepted_invitation_cannot_be_declined(
    monkeypatch,
) -> None:
    lucas_id, lais_id, board_id = prepare_invitation_context(
        monkeypatch
    )

    invitation = invite_user_to_board(
        board_id=board_id,
        invited_by_user_id=lucas_id,
        data=CreateInvitationRequest(
            email="lais@example.com",
        ),
    )

    accept_invitation_for_user(
        invitation_id=invitation.id,
        user_id=lais_id,
    )

    with pytest.raises(
        InvitationAlreadyProcessedError
    ):
        decline_invitation_for_user(
            invitation_id=invitation.id,
            user_id=lais_id,
        )


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_invited_user_can_accept_invitation_through_api(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE users
            RESTART IDENTITY CASCADE;
            """
        )

    client.cookies.clear()

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    client.post(
        "/api/auth/register",
        json={
            "name": "Laís",
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    board_response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    assert board_response.status_code == 201

    board_id = board_response.json()["id"]

    invitation_response = client.post(
        f"/api/boards/{board_id}/invitations",
        json={
            "email": "lais@example.com",
        },
    )

    assert invitation_response.status_code == 201

    invitation_id = invitation_response.json()["id"]

    client.cookies.clear()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    assert login_response.status_code == 200

    accept_response = client.post(
        f"/api/boards/invitations/{invitation_id}/accept"
    )

    assert accept_response.status_code == 200

    body = accept_response.json()

    assert body["id"] == invitation_id
    assert body["status"] == "accepted"

    with get_connection() as connection:
        membership = connection.execute(
            """
            SELECT role
            FROM board_members
            WHERE board_id = %s
              AND user_id = (
                  SELECT id
                  FROM users
                  WHERE email = %s
              );
            """,
            (
                board_id,
                "lais@example.com",
            ),
        ).fetchone()

    assert membership == ("member",)


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_invited_user_can_decline_invitation_through_api(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE users
            RESTART IDENTITY CASCADE;
            """
        )

    client.cookies.clear()

    client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    client.post(
        "/api/auth/register",
        json={
            "name": "Laís",
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    board_response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    board_id = board_response.json()["id"]

    invitation_response = client.post(
        f"/api/boards/{board_id}/invitations",
        json={
            "email": "lais@example.com",
        },
    )

    invitation_id = invitation_response.json()["id"]

    client.cookies.clear()

    client.post(
        "/api/auth/login",
        json={
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    decline_response = client.post(
        f"/api/boards/invitations/{invitation_id}/decline"
    )

    assert decline_response.status_code == 200

    body = decline_response.json()

    assert body["id"] == invitation_id
    assert body["status"] == "declined"

    with get_connection() as connection:
        membership = connection.execute(
            """
            SELECT role
            FROM board_members
            WHERE board_id = %s
              AND user_id = (
                  SELECT id
                  FROM users
                  WHERE email = %s
              );
            """,
            (
                board_id,
                "lais@example.com",
            ),
        ).fetchone()

    assert membership is None


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_user_only_sees_their_pending_invitations(
    monkeypatch,
) -> None:
    (
        lucas_id,
        lais_id,
        board_id,
    ) = prepare_invitation_context(monkeypatch)

    with get_connection() as connection:
        patrick = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash
            )
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (
                "Patrick",
                "patrick@example.com",
                "not-used",
            ),
        ).fetchone()

        assert patrick is not None
        patrick_id = patrick[0]

        pending = connection.execute(
            """
            INSERT INTO invitations (
                board_id,
                invited_user_id,
                invited_by_user_id,
                status
            )
            VALUES (%s, %s, %s, 'pending')
            RETURNING id;
            """,
            (
                board_id,
                lais_id,
                lucas_id,
            ),
        ).fetchone()

        accepted = connection.execute(
            """
            INSERT INTO invitations (
                board_id,
                invited_user_id,
                invited_by_user_id,
                status
            )
            VALUES (%s, %s, %s, 'accepted')
            RETURNING id;
            """,
            (
                board_id,
                lais_id,
                lucas_id,
            ),
        ).fetchone()

        declined = connection.execute(
            """
            INSERT INTO invitations (
                board_id,
                invited_user_id,
                invited_by_user_id,
                status
            )
            VALUES (%s, %s, %s, 'declined')
            RETURNING id;
            """,
            (
                board_id,
                lais_id,
                lucas_id,
            ),
        ).fetchone()

        patrick_pending = connection.execute(
            """
            INSERT INTO invitations (
                board_id,
                invited_user_id,
                invited_by_user_id,
                status
            )
            VALUES (%s, %s, %s, 'pending')
            RETURNING id;
            """,
            (
                board_id,
                patrick_id,
                lucas_id,
            ),
        ).fetchone()

    assert pending is not None
    assert accepted is not None
    assert declined is not None
    assert patrick_pending is not None

    invitations = get_pending_invitations_for_user(
        user_id=lais_id,
    )

    assert len(invitations) == 1

    invitation = invitations[0]

    assert invitation.id == pending[0]
    assert invitation.board_id == board_id
    assert invitation.board_name == "Casa"
    assert invitation.invited_by_user_id == lucas_id
    assert invitation.invited_by_name == "Lucas Amaral"
    assert invitation.status == "pending"
    assert invitation.created_at is not None


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL is not configured",
)
def test_user_can_list_pending_invitations_through_api(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ["TEST_DATABASE_URL"],
    )

    run_migrations()

    with get_connection() as connection:
        connection.execute(
            """
            TRUNCATE users
            RESTART IDENTITY CASCADE;
            """
        )

    client.cookies.clear()

    lucas_response = client.post(
        "/api/auth/register",
        json={
            "name": "Lucas Amaral",
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert lucas_response.status_code == 201

    lais_response = client.post(
        "/api/auth/register",
        json={
            "name": "Laís",
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    assert lais_response.status_code == 201

    login_lucas = client.post(
        "/api/auth/login",
        json={
            "email": "lucas@example.com",
            "password": "secret123",
        },
    )

    assert login_lucas.status_code == 200

    board_response = client.post(
        "/api/boards",
        json={
            "name": "Casa",
        },
    )

    assert board_response.status_code == 201

    board_id = board_response.json()["id"]

    invitation_response = client.post(
        f"/api/boards/{board_id}/invitations",
        json={
            "email": "lais@example.com",
        },
    )

    assert invitation_response.status_code == 201

    invitation_id = invitation_response.json()["id"]

    client.cookies.clear()

    login_lais = client.post(
        "/api/auth/login",
        json={
            "email": "lais@example.com",
            "password": "secret123",
        },
    )

    assert login_lais.status_code == 200

    response = client.get(
        "/api/boards/invitations"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1

    invitation = body[0]

    assert invitation["id"] == invitation_id
    assert invitation["board_id"] == board_id
    assert invitation["board_name"] == "Casa"
    assert invitation["invited_by_name"] == "Lucas Amaral"
    assert invitation["status"] == "pending"


def test_pending_invitations_requires_authentication() -> None:
    client.cookies.clear()

    response = client.get(
        "/api/boards/invitations"
    )

    assert response.status_code == 401
