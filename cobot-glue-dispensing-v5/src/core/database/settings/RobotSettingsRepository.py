"""
Robot settings repository implementation.

This module provides a repository for managing robot configuration
using the standardized repository interface.
"""

from typing import Dict, Any

from .BaseJsonSettingsRepository import BaseJsonSettingsRepository
from core.model.settings.robotConfig.robotConfigModel import RobotConfig, get_default_config


class RobotSettingsRepository(BaseJsonSettingsRepository[RobotConfig]):
    """
    Repository for robot configuration using JSON storage.
    
    Handles loading, saving, and conversion of robot configuration
    to/from JSON format.
    """
    
    def get_default(self) -> RobotConfig:
        """
        Get default robot configuration.
        
        Returns:
            RobotConfig object with default values
        """
        try:
            return get_default_config()
        except Exception:
            # Fallback to empty config if default config fails
            return RobotConfig.from_dict({})
    
    def to_dict(self, settings: RobotConfig) -> Dict[str, Any]:
        """
        Convert robot configuration to dictionary.
        
        Args:
            settings: RobotConfig object to convert
        
        Returns:
            Dictionary representation of robot configuration
        """
        return settings.to_dict()
    
    def from_dict(self, data: Dict[str, Any]) -> RobotConfig:
        """
        Create robot configuration from dictionary.
        
        Args:
            data: Dictionary data to convert
        
        Returns:
            RobotConfig object created from the data
        """
        return RobotConfig.from_dict(data)
    
    def get_settings_type(self) -> str:
        """
        Get the settings type identifier.
        
        Returns:
            String identifier for robot configuration
        """
        return "robot_config"