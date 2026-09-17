# LifeBoard

LifeBoard is a shared weekly life board for tracking individual and shared activities.

This project is being developed as the CS50x 2026 Final Project.

## Stack

- Python + FastAPI
- PostgreSQL (Neon)
- Next.js + TypeScript (frontend, developed separately)
- GitHub Actions
- Azure Container Apps

## Core idea

Users create boards, invite other registered users, define individual or shared categories, and explicitly record each day as yes or no. Missing responses remain pending.

## Browser security

The API accepts credentialed browser requests only from origins configured in
`FRONTEND_ORIGINS` (comma-separated). Development defaults to
`http://localhost:3000`; production has no implicit allowed origin.

The signed session cookie uses `SameSite=Lax` and HTTPS-only cookies in
production. Together with the explicit CORS allowlist and JSON request bodies,
this provides pragmatic CSRF protection for the MVP without adding a separate
token flow. The frontend must use `credentials: "include"` in API requests.

## Acknowledgements

OpenAI Codex was used as an AI coding assistant for implementation review,
tests, and documentation. All generated changes were reviewed and validated
against the project's requirements.
