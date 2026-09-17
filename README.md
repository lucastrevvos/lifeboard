# LifeBoard

#### Video Demo: <VIDEO_URL>

#### Description:

LifeBoard is a shared weekly life board built as my CS50x 2026 Final Project. The idea came from a physical Monday-to-Sunday board used to track recurring areas of everyday life such as training, diet, work, and shared activities. The goal of the project is to preserve that simple weekly-board mental model while adding authentication, persistence, collaboration, historical navigation, and clear ownership rules.

A user can register, sign in, create one or more boards, invite another already-registered user, and organize each board with categories. Categories can be **individual** or **shared**. An individual category belongs conceptually to each member separately: if two people are members of the same board, one person can mark training as yes while the other marks it as no on the same date. A shared category instead has one board-level answer for the date, so every member sees the same state.

Each day has three possible states: **yes**, **no**, or **pending**. A deliberate database design choice is that `pending` is represented by the absence of a response row. A stored boolean `true` means yes and `false` means no. This prevents “not answered yet” from being confused with an explicit negative answer.

The main interface is a weekly grid with categories as rows and Monday through Sunday as columns. Members can record yes/no responses directly in the cells, move between previous and future weeks, and return to the current week. Owners can also create categories, reorder them, soft-deactivate them, and invite members. Category changes are reflected in the weekly board without a full-page reload.

## Main features

- Account registration, login, logout, and session restoration.
- Signed HttpOnly cookie-based authentication.
- Multiple boards per user.
- Owner/member roles for board access.
- Invitations to already-registered users with accept/decline flow.
- Individual and shared categories.
- Yes/no/pending daily response model.
- Monday-to-Sunday weekly board.
- Historical week navigation.
- Persistent PostgreSQL storage.
- Owner-only category reorder and soft deactivation.
- Responsive Next.js interface.
- Backend integration tests with PostgreSQL in CI.
- Frontend lint and production build checks in CI.

## Technology stack

The backend is written in **Python** with **FastAPI**, **Pydantic**, and **psycopg**. PostgreSQL is used for persistence; during development I use a PostgreSQL-compatible connection string such as a Neon database. Passwords are hashed with Argon2 through `pwdlib`.

The frontend is a separate **Next.js 16** application using **TypeScript**, **React 19**, and the App Router. Browser requests use `fetch` with `credentials: "include"` so the FastAPI session cookie remains the source of authentication state. No JWT or token is stored in local storage.

The repository uses **GitHub Actions** for continuous integration. The backend CI job runs against PostgreSQL 17 and Python 3.13. The frontend job uses Node.js 20 and runs ESLint plus a production Next.js build.

## Architecture

The backend intentionally uses explicit SQL instead of an ORM. The main flow is:

```text
HTTP request
    ↓
FastAPI route
    ↓
service / application rules
    ↓
repository
    ↓
explicit psycopg SQL
    ↓
PostgreSQL
```

This structure keeps HTTP concerns, business rules, and persistence separate without introducing a large framework or a rich domain model that the project does not yet need.

For example, category reordering is implemented as a database transaction. The backend locks the active category rows with `SELECT ... FOR UPDATE`, verifies that the client supplied exactly the complete active category set, updates normalized positions, and commits the transaction. If validation fails, no positions are changed.

Authentication uses FastAPI/Starlette sessions. The cookie stores only the user identifier and is signed with the configured session secret. In production it is marked HTTPS-only. The API also uses an explicit CORS allowlist and credentialed requests.

## Database model

The core tables are:

- `users`: registered accounts and password hashes.
- `boards`: shared weekly boards and their creator.
- `board_members`: users belonging to a board with owner/member roles.
- `invitations`: board invitations and their pending/accepted/declined state.
- `categories`: board categories, type, order, and active state.
- `responses`: daily yes/no answers plus the user who last updated them.
- `schema_migrations`: migration versions and checksums.

Response uniqueness differs by category type. Shared responses use one row per category/date with `subject_user_id IS NULL`. Individual responses include the member as the subject. PostgreSQL partial unique indexes enforce those invariants at the database level.

## Important design decisions

### Explicit SQL instead of an ORM

I chose `psycopg` and handwritten SQL because one goal of the project was to make database behavior visible. Queries, transactions, constraints, and locking are therefore easy to inspect rather than being hidden behind an ORM abstraction.

### Pending means no row

A pending response is not stored as a third database value. If no response row exists for that category/date/subject, the application presents `pending`. This keeps explicit “no” answers distinct from unanswered days.

### Individual versus shared categories

The backend owns this rule instead of trusting the browser. For an individual category the authenticated user becomes the response subject. For a shared category the subject is `NULL`, producing one shared answer visible to all board members.

### Cookie sessions instead of JWT

LifeBoard is a browser application, so a signed HttpOnly session cookie keeps authentication simple and avoids storing bearer tokens in JavaScript-accessible browser storage. The frontend restores the logged-in user through `/api/auth/me`.

### Soft category deactivation

Categories are deactivated with `active = FALSE` rather than being deleted. Existing response rows are preserved. This avoids destructive cascading behavior and keeps historical data in the database even though inactive categories are no longer shown in the active weekly grid.

### Complete-list category reorder

The frontend sends the complete desired active-category order instead of commands such as “move category 4 to position 2.” The backend validates the whole set and normalizes positions to `0..n-1` atomically. This makes the final state unambiguous.

## Repository structure

### Backend

- `app/main.py` creates the FastAPI application, configures CORS and session middleware, registers routers, and exposes the health endpoint.
- `app/config.py` reads database, session, environment, and frontend-origin configuration.
- `app/database/connection.py` creates PostgreSQL connections.
- `app/security/passwords.py` contains password hashing and verification helpers.
- `app/auth/` implements registration, login, logout, current-user lookup, schemas, service rules, and SQL persistence.
- `app/boards/` implements board creation, board visibility, membership checks, and the aggregated weekly read model.
- `app/invitations/` implements invitation creation, listing, acceptance, decline, and membership creation.
- `app/categories/` implements category creation/listing, owner authorization, atomic reordering, and soft deactivation.
- `app/responses/` implements daily response reads/writes and individual/shared response semantics.

Each feature package follows the same small pattern: `routes.py` for HTTP mapping, `service.py` for application rules, `repository.py` for SQL, and `schemas.py` for Pydantic request/response models.

### Database and scripts

- `database/migrations/001_initial_schema.sql` creates the initial relational model and constraints.
- `database/migrations/002_fix_shared_response_index.sql` corrects the shared-response partial unique index without rewriting an already-applied migration.
- `database/migrations/003_add_pending_invitation_unique_index.sql` prevents duplicate pending invitations for the same board/user pair.
- `scripts/migrate.py` applies migrations in filename order, records SHA-256 checksums, and refuses to silently accept changes to migrations that were already applied.
- `scripts/check_database.py` and `scripts/inspect_database.py` are small database inspection utilities used during development.

### Frontend

- `frontend/src/app/page.tsx` is the public landing page.
- `frontend/src/app/login/page.tsx` and `frontend/src/app/register/page.tsx` expose authentication screens.
- `frontend/src/app/boards/page.tsx` lists boards, creates boards, and displays pending invitations.
- `frontend/src/app/boards/[boardId]/page.tsx` composes the weekly board and management views and coordinates category refreshes.
- `frontend/src/components/AuthForm.tsx` implements reusable login/register behavior.
- `frontend/src/components/ProtectedPage.tsx` restores the current session before rendering authenticated pages.
- `frontend/src/components/PendingInvitations.tsx` renders invitation accept/decline controls.
- `frontend/src/components/WeeklyBoard.tsx` renders week navigation, the Monday-Sunday grid, and response mutations.
- `frontend/src/components/BoardManagement.tsx` implements category creation/reorder/deactivation and member invitations.
- `frontend/src/lib/api.ts` centralizes HTTP calls and always includes browser credentials.
- `frontend/src/lib/types.ts` defines frontend TypeScript contracts.
- `frontend/src/app/globals.css` contains the responsive application styling.

### Tests and CI

The `tests/` directory covers authentication, registration, boards, invitations, categories, category management, responses, weekly aggregation, migrations, configuration, CORS, passwords, schema rules, and health checks. PostgreSQL-backed tests are skipped locally when `TEST_DATABASE_URL` is not configured; the GitHub Actions backend job provides a disposable PostgreSQL database and runs the full suite.

`.github/workflows/ci.yml` contains two independent jobs: backend tests and frontend lint/build.

## Running LifeBoard locally

### Prerequisites

- Python 3.13 is the version used by CI.
- Node.js 20 is the version used by CI.
- A PostgreSQL database. A local PostgreSQL instance or a hosted PostgreSQL-compatible service can be used.

### 1. Backend configuration

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` and provide real values:

```env
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
SESSION_SECRET_KEY=replace-with-a-long-random-secret
APP_ENV=development
FRONTEND_ORIGINS=http://localhost:3000
```

If Next.js starts on another local port, add that exact origin to `FRONTEND_ORIGINS` as a comma-separated value.

### 2. Install backend dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

On Windows I run the Python environment through WSL.

### 3. Apply database migrations

```bash
python -m scripts.migrate
```

### 4. Start FastAPI

```bash
python -m uvicorn app.main:app --reload --port 8000
```

The health endpoint is available at:

```text
http://localhost:8000/api/health
```

### 5. Configure and start the frontend

In another terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The default frontend API setting is:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Open the local URL printed by Next.js, normally `http://localhost:3000`.

## Running checks

Backend:

```bash
source .venv/bin/activate
python -m pytest
```

For the complete PostgreSQL-backed integration suite, set `TEST_DATABASE_URL` to a disposable test database. Do not point destructive integration tests at a normal development or production database.

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Security notes

Passwords are stored as Argon2 hashes rather than plaintext. Authenticated browser state is stored in a signed HttpOnly session cookie. The production cookie is HTTPS-only. CORS uses an explicit list of allowed frontend origins and credentialed requests. Board access and owner-only mutations are rechecked on the backend; hiding owner controls in the frontend is only a UX decision and is not used as the security boundary.

## Current limitations

LifeBoard is intentionally a focused MVP. It does not currently include category restore, renaming, changing category type after creation, resetting an explicit response back to pending, real-time updates, notifications, analytics, streaks, or an AI feature. Deactivated categories are removed from the active weekly read model even when viewing older weeks; the response data itself is preserved. These limitations were kept outside the CS50 final-project scope to avoid turning the project into an open-ended product build.

The repository is designed to run locally for evaluation. A production deployment can be added separately; the authentication cookie/domain strategy should be reviewed if frontend and backend are hosted on unrelated sites.

## AI assistance disclosure

For this final project, OpenAI ChatGPT and OpenAI Codex were used as development assistants for architecture discussion, implementation suggestions, debugging, test-case generation, code review, and documentation. Their output was not treated as automatically correct: changes were reviewed, executed, tested, revised, and validated against the intended behavior before being accepted. Project-wide AI-assistance citations are also present as comments in the backend and frontend entry modules in accordance with the CS50x final-project instructions.

## CS50x submission

Before submission, replace `<VIDEO_URL>` near the top of this README with the public or unlisted video URL.

From the directory containing this README and the project source code, submit with:

```bash
submit50 cs50/problems/2026/x/project
```

After submitting, visit the CS50x gradebook and confirm that the final project has been processed and that the course completion banner appears.
