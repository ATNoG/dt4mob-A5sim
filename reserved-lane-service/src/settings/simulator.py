from pydantic import BaseModel


class SimulatorSettings(BaseModel):
    # SUMO binary
    binary: str = "sumo"

    network_file: str = "A5.net.xml"
    route_file_real: str = "routes/vehicleRoutes.rou.xml"
    route_file_closed: str = "routes/vehicleRoutes2.rou.xml"
    additional_files: str = "detectors.det.xml,polygons.poly.xml"

    output_dir: str = "output"

    begin: int = 39346
    end: int = 40000
    step_length: float = 0.1

    # Lanes that get closed to regular traffic in the closedLane* scenarios.
    closed_lanes: list[str] = ["320209307_2", "49166745_2"]
    target_lanes: list[str] = ["320209307_0", "320209307_1", "320209307_2"]
    toll_detector_id: str = "toll_2"

    # x-position window (in network coordinates) where "custom2" vehicles
    # are considered for a paid lane change in the closedLaneFast scenario.
    lane_change_x_min: float = 400.0
    lane_change_x_max: float = 700.0

    base_port: int = 8813

    # How many simulation requests (each spawning 4 SUMO processes) may
    # run at the same time
    max_concurrent_jobs: int = 2

    # finished/failed job result persistence in seconds
    job_ttl_seconds: int = 3600
