from fastapi import APIRouter, HTTPException

from src.models.simulation import JobStatusResponse, JobSubmitted, SimulationRequest
from src.services.simulation.jobs import job_manager

router = APIRouter(prefix="/api/v1")


@router.post("/simulation", response_model=JobSubmitted, status_code=202)
async def submit_simulation(request: SimulationRequest) -> JobSubmitted:
    """Kicks off the 4-scenario SUMO simulation in the background and
    immediately returns a job id. Poll GET /simulation/{job_id} for results.
    """
    job = job_manager.submit(request)
    return JobSubmitted(job_id=job.id, status=job.status)


@router.get("/simulation/{job_id}", response_model=JobStatusResponse)
async def get_simulation(job_id: str) -> JobStatusResponse:
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        result=job.result,
        error=job.error,
    )
