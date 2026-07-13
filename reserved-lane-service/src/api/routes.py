from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import KeycloakToken, check_role
from src.models.simulation import (
    JobListItem,
    JobStatusResponse,
    JobSubmitted,
    SimulationRequest,
)
from src.services.simulation.jobs import job_manager
from src.settings import settings

router = APIRouter(prefix="/api/v1")

require_role = check_role([settings.auth.role] if isinstance(settings.auth.role, str) else settings.auth.role)


@router.get("/simulation", response_model=list[JobListItem])
async def list_simulations(
    token: Annotated[KeycloakToken, Depends(require_role)],
) -> list[JobListItem]:
    return [
        JobListItem(
            job_id=job.id,
            status=job.status,
            request=job.request,
            created_at=job.created_at,
            error=job.error,
        )
        for job in job_manager.list_all()
    ]


@router.post("/simulation", response_model=JobSubmitted, status_code=202)
async def submit_simulation(
    request: SimulationRequest,
    token: Annotated[KeycloakToken, Depends(require_role)],
) -> JobSubmitted:
    """Kicks off the 4-scenario SUMO simulation in the background and
    immediately returns a job id. Poll GET /simulation/{job_id} for results.
    """
    job = job_manager.submit(request)
    return JobSubmitted(job_id=job.id, status=job.status)


@router.get("/simulation/{job_id}", response_model=JobStatusResponse)
async def get_simulation(
    job_id: str,
    token: Annotated[KeycloakToken, Depends(require_role)],
) -> JobStatusResponse:
    job = job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        result=job.result,
        error=job.error,
    )
