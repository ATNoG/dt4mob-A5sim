import multiprocessing
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.api.routes import router

app = FastAPI(
    title="Reserved Lane Simulation Service",
    description="On-demand SUMO simulation for evaluating the A5 paid reserved lane.",
    version="0.1.0",
)
app.include_router(router)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(TEMPLATES_DIR / "index.html")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    # multiprocessing.Process 
    multiprocessing.set_start_method("spawn", force=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
