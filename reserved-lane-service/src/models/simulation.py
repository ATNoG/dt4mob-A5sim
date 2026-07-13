from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    paying_percentage: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of eligible vehicles allowed to pay to enter the reserved lane.",
    )
    price: float = Field(ge=0.0, description="Price in euros for using the reserved lane.")
    traffic_scale: float = Field(gt=0.0, description="Traffic volume scale factor applied to the closed-lane scenarios.")


class ScenarioResult(BaseModel):
    total_vehicles: int
    lane2_vehicles: int
    lane2_usage_perc: str
    revenue: float
    avg_speeds: dict[str, float]


class SimulationResponse(BaseModel):
    real: ScenarioResult
    allOpen: ScenarioResult
    closedLane: ScenarioResult
    closedLaneFast: ScenarioResult


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class JobSubmitted(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[SimulationResponse] = None
    error: Optional[str] = None


class JobListItem(BaseModel):
    job_id: str
    status: JobStatus
    request: SimulationRequest
    created_at: float
    error: Optional[str] = None
