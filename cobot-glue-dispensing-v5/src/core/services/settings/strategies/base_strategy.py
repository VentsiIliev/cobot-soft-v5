"""
Base strategy interface for settings updates.

This module provides the abstract interface that all settings update
strategies must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SettingsUpdateStrategy(ABC):
    """
    Abstract base class for settings update strategies.

    Each settings type can have its own update strategy that encapsulates
    the specific logic needed to update that type of settings.
    """

    @abstractmethod
    def update(self, current_settings: Optional[Any], updates: Dict[str, Any], repository: Any) -> Any:
        """
        Apply updates to settings.

        Args:
            current_settings: Current settings object (or None if creating new)
            updates: Dictionary of updates to apply
            repository: The repository for this settings type

        Returns:
            Updated settings object

        Raises:
            ValueError: If updates are invalid or cannot be applied
        """
        pass

    def notify(self, updates: Dict[str, Any]) -> None:
        """
        Perform any post-update notifications.

        This method is called after settings are successfully updated and saved.
        Override this method if your settings type needs to notify other
        components about changes.

        Args:
            updates: The updates that were applied
        """
        pass