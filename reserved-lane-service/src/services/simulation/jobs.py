import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from src.models.simulation import JobStatus, SimulationRequest, SimulationResponse
from src.services.simulation.runner import SimulationRunner
from src.settings import settings


@dataclass
class Job:
    id: str
    request: SimulationRequest
    status: JobStatus = JobStatus.PENDING
    result: Optional[SimulationResponse] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.monotonic)


class SimulationJobManager:
    """Turns the blocking, process-spawning SimulationRunner into an async
    job you can submit and poll. A semaphore caps how many simulation
    requests run at once (each one spawns 4 SUMO processes), so the service
    stays responsive under Kubernetes-style concurrent load instead of
    spawning an unbounded number of SUMO processes per request.
    """

    def __init__(self, max_concurrent_jobs: Optional[int] = None):
        self._jobs: dict[str, Job] = {}
        self._semaphore = asyncio.Semaphore(
            max_concurrent_jobs or settings.sumo.max_concurrent_jobs
        )
        self._runner = SimulationRunner()

    def submit(self, request: SimulationRequest) -> Job:
        self._evict_expired()

        job = Job(id=str(uuid.uuid4()), request=request)
        self._jobs[job.id] = job
        asyncio.create_task(self._execute(job))
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    async def _execute(self, job: Job) -> None:
        async with self._semaphore:
            job.status = JobStatus.RUNNING
            loop = asyncio.get_running_loop()
            try:
                job.result = await loop.run_in_executor(None, self._runner.run, job.request)
                job.status = JobStatus.DONE
            except Exception as exc:  # noqa: BLE001 - surface any failure to the client
                job.status = JobStatus.FAILED
                job.error = str(exc)

    def _evict_expired(self) -> None:
        ttl = settings.sumo.job_ttl_seconds
        now = time.monotonic()
        expired = [
            job_id
            for job_id, job in self._jobs.items()
            if job.status in (JobStatus.DONE, JobStatus.FAILED)
            and now - job.created_at > ttl
        ]
        for job_id in expired:
            del self._jobs[job_id]


job_manager = SimulationJobManager()
