from datetime import datetime
from typing import Dict, Any


class StatisticsService:
    """Service to handle business logic for glue spray statistics."""

    def update_component_state(self, statistics: Dict[str, Any], component: str, new_state: str, count_type: str):
        ts = datetime.now()
        statistics[component][count_type] += 1

        if new_state == "on":
            statistics[component]["last_on_timestamp"] = ts.isoformat()
            statistics[component]["current_state"] = "on"
            statistics[component]["session_start"] = ts.isoformat()
        else:  # new_state == "off"
            statistics[component]["last_off_timestamp"] = ts.isoformat()
            statistics[component]["current_state"] = "off"
            if statistics[component]["session_start"]:
                start = datetime.fromisoformat(statistics[component]["session_start"])
                runtime = (ts - start).total_seconds()
                statistics[component]["total_runtime_seconds"] += runtime
                statistics[component]["session_start"] = None

            # Increment total_cycles if both generator and motor are off
            if (statistics["generator"]["current_state"] == "off" and
                    statistics["motor"]["current_state"] == "off"):
                statistics["system"]["total_cycles"] += 1

        return statistics

    def reset_statistics(self, statistics: Dict[str, Any], default_statistics: Dict[str, Any]):
        statistics.clear()
        statistics.update(default_statistics)
        statistics["system"]["session_start"] = datetime.now().isoformat()
        return statistics

    def reset_component(self, statistics: Dict[str, Any], default_statistics: Dict[str, Any], component: str):
        if component not in ["generator", "motor"]:
            raise ValueError(f"Unknown component: {component}")
        statistics[component] = default_statistics[component]
        return statistics
