# CS50 AI assistance citation: OpenAI ChatGPT and OpenAI Codex were used as
# development assistants across the LifeBoard backend for architecture discussion,
# implementation suggestions, debugging, tests, review, and documentation. All
# accepted changes were reviewed and validated by the project author.

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth.routes import router as auth_router
from app.boards.routes import router as boards_router
from app.config import get_frontend_origins, get_session_secret_key, is_production

from app.invitations.routes import router as invitations_router

from app.categories.routes import router as categories_router

from app.responses.routes import router as responses_router


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="LifeBoard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=get_session_secret_key(),
    session_cookie="lifeboard_session",
    same_site="lax",
    https_only=is_production()
)

app.include_router(auth_router)

app.include_router(boards_router)

app.include_router(invitations_router)

app.include_router(categories_router)

app.include_router(responses_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "name": "LifeBoard",
        "status": "ok",
    }


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
