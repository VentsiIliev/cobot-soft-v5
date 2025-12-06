"""
Default settings update strategy.

This module provides the default update strategy for settings types
that don't require special handling.
"""

from typing import Dict, Any, Optional
from .base_strategy import SettingsUpdateStrategy


class DefaultSettingsUpdateStrategy(SettingsUpdateStrategy):
    """
    Default update strategy for settings without special requirements.

    This strategy simply:
    1. Converts current settings to dict
    2. Updates the dict with new values
    3. Converts back to settings object
    """

    def update(self, current_settings: Optional[Any], updates: Dict[str, Any], repository: Any) -> Any:
        """
        Apply updates to settings using simple dict merge.

        Args:
            current_settings: Current settings object (or None)
            updates: Dictionary of setting updates
            repository: Settings repository

        Returns:
            Updated settings object
        """
        if current_settings is None:
            # No existing settings, create new from provided data
            return repository.from_dict(updates)

        # Simple merge: convert to dict, update, convert back
        current_dict = repository.to_dict(current_settings)
        current_dict.update(updates)
        return repository.from_dict(current_dict)

    def notify(self, updates: Dict[str, Any]) -> None:
        """
        No notification needed for default settings updates.

        Args:
            updates: The settings that were updated
        """
        pass
