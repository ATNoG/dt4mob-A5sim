import multiprocessing
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.api.routes import router
from src.settings import settings

app = FastAPI(
    title="Reserved Lane Simulation Service",
    description="On-demand SUMO simulation for evaluating the A5 paid reserved lane.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(TEMPLATES_DIR / "index.html")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/auth/config")
async def auth_config() -> dict[str, str]:
    return {
        "server_url": settings.auth.server_uri,
        "realm": settings.auth.realm,
        "client_id": settings.auth.client_id,
    }


if __name__ == "__main__":
    import uvicorn

    multiprocessing.set_start_method("spawn", force=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
