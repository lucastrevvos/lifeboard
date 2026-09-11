from pathlib import Path

from fastapi import FastAPI
from app.auth.routes import router as auth_router
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="LifeBoard")

app.include_router(auth_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "name": "LifeBoard",
        "status": "ok",
    }


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
