CREATE UNIQUE INDEX uq_pending_invitation
ON invitations (
    board_id,
    invited_user_id
)
WHERE status = 'pending';
