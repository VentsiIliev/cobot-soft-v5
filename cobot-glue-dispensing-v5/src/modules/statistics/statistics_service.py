from datetime import datetime
from typing import Dict, Any


class StatisticsService:
    """Service to handle business logic for glue spray statistics."""

    def update_component_state(self, statistics: Dict[str, Any], component: str, new_state: str, count_type: str):
        ts = datetime.now()

        # Handle nested paths like "motors.1"
        if "." in component:
            parts = component.split(".")
            target = statistics
            for part in parts[:-1]:
                target = target[part]
            component_data = target[parts[-1]]
            component_key = parts[-1]
        else:
            component_data = statistics[component]
            component_key = component

        component_data[count_type] += 1

        if new_state == "on":
            component_data["last_on_timestamp"] = ts.isoformat()
            component_data["current_state"] = "on"
            component_data["session_start"] = ts.isoformat()
        else:  # new_state == "off"
            component_data["last_off_timestamp"] = ts.isoformat()
            component_data["current_state"] = "off"
            if component_data["session_start"]:
                start = datetime.fromisoformat(component_data["session_start"])
                runtime = (ts - start).total_seconds()
                component_data["total_runtime_seconds"] += runtime
                component_data["session_start"] = None

            # Increment total_cycles if both generator and all motors are off
            all_motors_off = True
            if "motors" in statistics:
                for motor_addr, motor_data in statistics["motors"].items():
                    if motor_data.get("current_state") == "on":
                        all_motors_off = False
                        break

            if (statistics["generator"]["current_state"] == "off" and all_motors_off):
                statistics["system"]["total_cycles"] += 1

        return statistics

    def reset_statistics(self, statistics: Dict[str, Any], default_statistics: Dict[str, Any]):
        statistics.clear()
        statistics.update(default_statistics)
        statistics["system"]["session_start"] = datetime.now().isoformat()
        return statistics

    def reset_component(self, statistics: Dict[str, Any], default_statistics: Dict[str, Any], component: str):
        if component == "motors":
            # Reset all motors
            statistics["motors"] = {}
            return statistics
        elif component.startswith("motor_"):
            # Reset specific motor
            motor_address = component.replace("motor_", "")
            if "motors" in statistics and motor_address in statistics["motors"]:
                del statistics["motors"][motor_address]
            return statistics
        elif component not in ["generator", "system"]:
            raise ValueError(f"Unknown component: {component}")

        if component in default_statistics:
            statistics[component] = default_statistics[component].copy()
        return statistics
