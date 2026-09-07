from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="LifeBoard")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "name": "LifeBoard",
        "status": "ok",
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")
