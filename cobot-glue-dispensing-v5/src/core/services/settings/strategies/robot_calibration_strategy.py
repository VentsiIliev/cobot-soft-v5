"""
Robot calibration settings update strategy.

This module provides the update strategy for robot calibration settings.
"""

from typing import Dict, Any, Optional, Set
from .base_strategy import SettingsUpdateStrategy


class RobotCalibrationSettingsUpdateStrategy(SettingsUpdateStrategy):
    """
    Update strategy for robot calibration settings.

    This strategy handles:
    - Adaptive movement configuration keys (nested under adaptive_movement_config)
    - Key mappings (e.g., "required_marker_ids" -> "required_ids")
    - Direct updates for other calibration settings
    """

    # Keys that belong to adaptive_movement_config
    ADAPTIVE_MOVEMENT_KEYS: Set[str] = {
        "min_step_mm",
        "max_step_mm",
        "target_error_mm",
        "max_error_ref",
        "k",
        "derivative_scaling"
    }

    # Key mappings for compatibility
    KEY_MAPPINGS: Dict[str, str] = {
        "required_marker_ids": "required_ids"
    }

    def update(self, current_settings: Optional[Any], updates: Dict[str, Any], repository: Any) -> Any:
        """
        Apply updates to robot calibration settings.

        Args:
            current_settings: Current robot calibration settings object (or None)
            updates: Dictionary of robot calibration setting updates
            repository: Robot calibration settings repository

        Returns:
            Updated robot calibration settings object
        """
        if current_settings is None:
            # No existing settings, create new from provided data
            return repository.from_dict(updates)

        # Convert current settings to dict for manipulation
        current_dict = repository.to_dict(current_settings)

        # Apply each update
        for key, value in updates.items():
            if key in self.ADAPTIVE_MOVEMENT_KEYS:
                # Nested update for adaptive movement config
                if "adaptive_movement_config" not in current_dict:
                    current_dict["adaptive_movement_config"] = {}
                current_dict["adaptive_movement_config"][key] = value
            else:
                # Apply key mapping if needed, then update
                actual_key = self.KEY_MAPPINGS.get(key, key)
                current_dict[actual_key] = value

        # Create settings object from updated dict
        return repository.from_dict(current_dict)

    def notify(self, updates: Dict[str, Any]) -> None:
        """
        No notification needed for robot calibration settings updates.

        Args:
            updates: The robot calibration settings that were updated
        """
        pass
