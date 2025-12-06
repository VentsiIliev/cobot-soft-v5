"""
Robot configuration update strategy.

This module provides the update strategy for robot configuration settings.
"""

from typing import Dict, Any, Optional
from .base_strategy import SettingsUpdateStrategy


class RobotConfigUpdateStrategy(SettingsUpdateStrategy):
    """
    Update strategy for robot configuration settings.

    This strategy handles:
    - Uppercase key conversion for compatibility
    - Nested key updates using dot notation (e.g., "safety_limits.x_min")
    - Three-level nesting for movement groups (e.g., "movement_groups.SLOT 0 PICKUP.points")
    """

    def update(self, current_settings: Optional[Any], updates: Dict[str, Any], repository: Any) -> Any:
        """
        Apply updates to robot configuration.

        Args:
            current_settings: Current robot config object (or None)
            updates: Dictionary of robot config updates
            repository: Robot config repository

        Returns:
            Updated robot config object
        """
        if current_settings is None:
            # No existing settings, create new from provided data
            return repository.from_dict(updates)

        # Convert current settings to dict for manipulation
        current_dict = repository.to_dict(current_settings)

        # Apply each update
        for key, value in updates.items():
            if '.' in key:
                # Handle nested keys using dot notation
                self._update_nested_key(current_dict, key, value)
            else:
                # Simple key - convert to uppercase for compatibility
                current_dict[key.upper()] = value

        # Create settings object from updated dict
        return repository.from_dict(current_dict)

    def _update_nested_key(self, current_dict: Dict, key: str, value: Any) -> None:
        """
        Handle nested key updates using dot notation.

        Args:
            current_dict: The current settings dictionary
            key: Dotted key path (e.g., "safety_limits.x_min")
            value: Value to set
        """
        parts = key.split('.')

        if len(parts) == 2:
            # Handle 2-level nesting: "safety_limits.x_min"
            parent_key = parts[0].upper()
            child_key = parts[1].lower()

            # Ensure parent dict exists
            if parent_key not in current_dict:
                current_dict[parent_key] = {}

            # Update nested value
            current_dict[parent_key][child_key] = value

        elif len(parts) == 3 and parts[0] == "movement_groups":
            # Handle 3-level nesting: "movement_groups.SLOT 0 PICKUP.points"
            parent_key = "MOVEMENT_GROUPS"  # Always uppercase
            group_name = parts[1]  # Keep original case (e.g., "SLOT 0 PICKUP")
            setting_key = parts[2]  # e.g., "points", "position", "velocity"

            # Ensure parent dict exists
            if parent_key not in current_dict:
                current_dict[parent_key] = {}

            # Ensure group dict exists
            if group_name not in current_dict[parent_key]:
                current_dict[parent_key][group_name] = {}

            # Update the specific setting for this group
            current_dict[parent_key][group_name][setting_key] = value
            print(f"📝 Updated {parent_key}.{group_name}.{setting_key} = {value}")

        else:
            # Fallback for other nested keys
            actual_key = key.upper()
            current_dict[actual_key] = value

    def notify(self, updates: Dict[str, Any]) -> None:
        """
        No notification needed for robot config updates.

        Args:
            updates: The robot config updates that were applied
        """
        pass
