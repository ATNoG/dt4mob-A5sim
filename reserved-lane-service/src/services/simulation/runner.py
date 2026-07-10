import logging
import multiprocessing

from src.models.simulation import SimulationRequest, SimulationResponse
from src.settings import settings
from src.services.simulation.scenario import ScenarioExecutor

# (scenario_name, fixed_paying_percentage_or_None)
# "real" and "allOpen" never depend on the paying percentage; only
# closedLaneFast actually uses the value the user submitted.
_SCENARIOS: list[tuple[str, float | None]] = [
    ("real", 0.0),
    ("allOpen", 0.0),
    ("closedLane", 0.0),
    ("closedLaneFast", None),
]


def _run_scenario_in_process(
    name: str,
    scale_traffic: float,
    paying_percentage: float,
    price: float,
    port: int,
    return_dict: dict,
) -> None:
    logging.info(
        "Running scenario=%s scale=%s perc=%.2f price=%s port=%s",
        name, scale_traffic, paying_percentage, price, port,
    )
    executor = ScenarioExecutor(name, scale_traffic, paying_percentage, price, port)
    result = executor.run()
    return_dict[name] = result.model_dump()


class SimulationRunner:
    """Spawns one OS process per scenario (matching the original PoC), each
    talking to its own SUMO instance over a distinct TraCI port, and joins
    them into a single SimulationResponse. This is a blocking call - the
    caller (SimulationJobManager) is responsible for running it off the
    event loop and for bounding how many of these run at once.
    """

    def run(self, request: SimulationRequest) -> SimulationResponse:
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        processes: list[multiprocessing.Process] = []

        for i, (name, fixed_percentage) in enumerate(_SCENARIOS):
            paying_percentage = (
                fixed_percentage if fixed_percentage is not None else request.paying_percentage
            )
            process = multiprocessing.Process(
                target=_run_scenario_in_process,
                args=(
                    name,
                    request.traffic_scale,
                    paying_percentage,
                    request.price,
                    settings.sumo.base_port + i,
                    return_dict,
                ),
            )
            process.start()
            processes.append(process)

        for process in processes:
            process.join()

        for process in processes:
            if process.exitcode not in (0, None):
                raise RuntimeError(
                    f"A scenario process exited with code {process.exitcode}"
                )

        return SimulationResponse(**dict(return_dict))
