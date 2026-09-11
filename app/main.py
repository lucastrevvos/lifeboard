from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth.routes import router as auth_router
from app.boards.routes import router as boards_router
from app.config import get_session_secret_key, is_production


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="LifeBoard")

app.add_middleware(
    SessionMiddleware,
    secret_key=get_session_secret_key(),
    session_cookie="lifeboard_session",
    same_site="lax",
    https_only=is_production()
)

app.include_router(auth_router)

app.include_router(boards_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "name": "LifeBoard",
        "status": "ok",
    }


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
