"""
Camera settings repository implementation.

This module provides a repository for managing camera settings
using the standardized repository interface.
"""

from typing import Dict, Any

from .BaseJsonSettingsRepository import BaseJsonSettingsRepository
from core.model.settings.CameraSettings import CameraSettings


class CameraSettingsRepository(BaseJsonSettingsRepository[CameraSettings]):
    """
    Repository for camera settings using JSON storage.
    
    Handles loading, saving, and conversion of camera settings
    to/from JSON format.
    """
    
    def get_default(self) -> CameraSettings:
        """
        Get default camera settings.
        
        Returns:
            CameraSettings object with default values
        """
        return CameraSettings()
    
    def to_dict(self, settings: CameraSettings) -> Dict[str, Any]:
        """
        Convert camera settings to dictionary.
        
        Args:
            settings: CameraSettings object to convert
        
        Returns:
            Dictionary representation of camera settings
        """
        return settings.to_dict()
    
    def from_dict(self, data: Dict[str, Any]) -> CameraSettings:
        """
        Create camera settings from dictionary.
        
        Args:
            data: Dictionary data to convert
        
        Returns:
            CameraSettings object created from the data
        """
        return CameraSettings(data=data)
    
    def get_settings_type(self) -> str:
        """
        Get the settings type identifier.
        
        Returns:
            String identifier for camera settings
        """
        return "camera"