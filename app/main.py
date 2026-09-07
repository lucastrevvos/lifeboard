from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="LifeBoard")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "name": "LifeBoard",
        "status": "ok",
    }


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
