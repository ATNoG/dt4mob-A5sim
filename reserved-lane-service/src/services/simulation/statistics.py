from src.models.simulation import ScenarioResult


class StatisticsCollector:
    """Accumulates per-vehicle observations during a single TraCI run.
    """

    def __init__(self, target_lanes: list[str]):
        self._all_vehicles: set[str] = set()
        self._lane2_vehicles: set[str] = set()
        self._detected_ids: set[str] = set()
        # lane_id -> [sum_of_speeds_m_s, sample_count]
        self._lane_speed_data: dict[str, list[float]] = {
            lane: [0.0, 0] for lane in target_lanes
        }

    def record_vehicle(self, vehicle_id: str, lane_id: str, speed_m_s: float) -> None:
        self._all_vehicles.add(vehicle_id)

        if lane_id in self._lane_speed_data:
            bucket = self._lane_speed_data[lane_id]
            bucket[0] += speed_m_s
            bucket[1] += 1

        if lane_id.endswith("_2"):
            self._lane2_vehicles.add(vehicle_id)

    def record_detection(self, vehicle_id: str) -> None:
        self._detected_ids.add(vehicle_id)

    def result(self, price: float, revenue_applicable: bool) -> ScenarioResult:
        total = len(self._all_vehicles)
        lane2 = len(self._lane2_vehicles)
        # detected = len(self._detected_ids)

        avg_speeds_kmh: dict[str, float] = {}
        for lane_id, (total_speed, samples) in self._lane_speed_data.items():
            avg_ms = (total_speed / samples) if samples > 0 else 0.0
            avg_speeds_kmh[lane_id] = round(avg_ms * 3.6, 2)

        usage_perc = f"{(lane2 / total) * 100:.2f}%" if total > 0 else "0%"
        revenue = round(price * lane2, 2) if revenue_applicable else 0.0

        return ScenarioResult(
            total_vehicles=total,
            lane2_vehicles=lane2,
            lane2_usage_perc=usage_perc,
            revenue=revenue,
            avg_speeds=avg_speeds_kmh,
        )
