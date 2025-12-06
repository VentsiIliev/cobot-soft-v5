"""
Camera settings update strategy.

This module provides the update strategy for camera settings.
"""

from typing import Dict, Any, Optional
from .base_strategy import SettingsUpdateStrategy


class CameraSettingsUpdateStrategy(SettingsUpdateStrategy):
    """
    Update strategy for camera settings.

    Camera settings use the built-in updateSettings method on the settings
    object itself, so this strategy delegates to that method.
    """

    def update(self, current_settings: Optional[Any], updates: Dict[str, Any], repository: Any) -> Any:
        """
        Apply updates to camera settings.

        Args:
            current_settings: Current camera settings object (or None)
            updates: Dictionary of camera setting updates
            repository: Camera settings repository

        Returns:
            Updated camera settings object

        Raises:
            ValueError: If the update fails
        """
        if current_settings is None:
            # No existing settings, create new from provided data
            return repository.from_dict(updates)

        # Use the built-in updateSettings method to handle flat keys properly
        success, message = current_settings.updateSettings(updates)
        if not success:
            raise ValueError(f"Failed to update camera settings: {message}")

        # Debug: Verify in-memory settings were updated
        print(f"🔍 Debug: Camera settings in memory after update:")
        print(f"  - Enable auto adjust: {current_settings.get_brightness_auto()}")
        print(f"  - Kp: {current_settings.get_brightness_kp()}")
        print(f"  - Target brightness: {current_settings.get_target_brightness()}")

        return current_settings

    def notify(self, updates: Dict[str, Any]) -> None:
        """
        Notify VisionSystem of camera settings changes.

        Args:
            updates: The camera settings that were updated
        """
        try:
            from core.services.vision.VisionService import VisionServiceSingleton
            vision_service = VisionServiceSingleton.get_instance()
            if vision_service:
                print(f"🔄 Notifying VisionSystem of camera settings update...")
                vision_service.updateSettings(updates)
                print(f"✅ VisionSystem updated with new camera settings")
            else:
                print(f"⚠️ Warning: VisionService not available for settings update")
        except Exception as e:
            print(f"⚠️ Warning: Failed to notify VisionSystem of camera settings update: {e}")