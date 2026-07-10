import os
import random
import sys

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import traci  # noqa: E402

from src.models.simulation import ScenarioResult  # noqa: E402
from src.settings import settings  # noqa: E402
from src.services.simulation.statistics import StatisticsCollector  # noqa: E402

_NO_REVENUE_SCENARIOS = {"real", "allOpen"}
_CLOSED_LANE_SCENARIOS = {"closedLane", "closedLaneFast"}


class ScenarioExecutor:
    """Runs a single one of the four SUMO scenarios (real / allOpen /
    closedLane / closedLaneFast) to completion via TraCI and returns its
    aggregated KPIs. One instance = one SUMO process on one TraCI port, so
    multiple executors can run concurrently as long as their ports differ.
    """

    def __init__(
        self,
        name: str,
        scale_traffic: float,
        paying_percentage: float,
        price: float,
        port: int,
    ):
        self.name = name
        self.scale_traffic = scale_traffic
        self.paying_percentage = paying_percentage
        self.price = price
        self.port = port

    def _sumo_cmd(self) -> list[str]:
        cfg = settings.sumo
        cmd = [
            cfg.binary,
            "-n", cfg.network_file,
            "--additional-files", cfg.additional_files,
            "--begin", str(cfg.begin),
            "--end", str(cfg.end),
            "--time-to-teleport", "-1",
            # "--statistics-output",
            # f"stats.xml",
            "--step-length", str(cfg.step_length),
            "--output-prefix", f"{cfg.output_dir}/{self.name}_{self.scale_traffic}_{self.paying_percentage:.2f}_",
            "--quit-on-end",
        ]

        if self.name == "real":
            # real scenario replays recorded traffic: no scaling.
            cmd += ["-r", cfg.route_file_real]
        else:
            cmd += ["-r", cfg.route_file_closed, "--scale", str(self.scale_traffic)]

        return cmd

    def run(self) -> ScenarioResult:
        cfg = settings.sumo
        traci.start(self._sumo_cmd(), port=self.port)

        if self.name in _CLOSED_LANE_SCENARIOS:
            for lane in cfg.closed_lanes:
                traci.lane.setDisallowed(lane, ["custom1", "custom2"])

        collector = StatisticsCollector(cfg.target_lanes)
        # Vehicles change lane at a probability derived from the requested
        # paying percentage, normalized against the 0.8 baseline used when
        # the routes were generated (kept identical to the original PoC).
        change_probability = (
            self.paying_percentage / 0.8 if self.paying_percentage > 0 else 0.0
        )
        processed_vehicle_ids: set[str] = set()

        try:
            while traci.simulation.getMinExpectedNumber() > 0:
                traci.simulationStep()

                if traci.simulation.getTime() >= cfg.end:
                    break

                for vehicle_id in traci.vehicle.getIDList():
                    lane_id = traci.vehicle.getLaneID(vehicle_id)
                    speed = traci.vehicle.getSpeed(vehicle_id)
                    collector.record_vehicle(vehicle_id, lane_id, speed)

                    if self.name == "closedLaneFast":
                        self._maybe_move_to_paid_lane(
                            vehicle_id, processed_vehicle_ids, change_probability
                        )

                for vehicle_id in traci.inductionloop.getLastStepVehicleIDs(
                    cfg.toll_detector_id
                ):
                    collector.record_detection(vehicle_id)
        finally:
            traci.close()

        return collector.result(
            price=self.price,
            revenue_applicable=self.name not in _NO_REVENUE_SCENARIOS,
        )

    def _maybe_move_to_paid_lane(
        self,
        vehicle_id: str,
        processed_vehicle_ids: set[str],
        change_probability: float,
    ) -> None:
        cfg = settings.sumo

        if vehicle_id in processed_vehicle_ids:
            return
        if traci.vehicle.getTypeID(vehicle_id) != "custom2":
            return

        x_pos, _ = traci.vehicle.getPosition(vehicle_id)
        if not (cfg.lane_change_x_min < x_pos < cfg.lane_change_x_max):
            return

        processed_vehicle_ids.add(vehicle_id)
        if random.random() < min(change_probability, 1.0):
            traci.vehicle.setType(vehicle_id, "passenger")
            traci.vehicle.changeLane(vehicle_id, 2, 1000.0)
