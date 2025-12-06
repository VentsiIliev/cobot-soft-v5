"""
Settings repository registry.

This module provides a registry for managing different types of
settings repositories, allowing dynamic registration and discovery
of settings types.
"""

from typing import Dict, Type, Optional
import logging

from core.database.settings.RobotCalibrationRepository import RobotCalibrationSettingsRepository
from core.services.settings.interfaces.ISettingsRepository import ISettingsRepository
from core.database.settings.CameraSettingsRepository import CameraSettingsRepository
from core.database.settings.RobotSettingsRepository import RobotSettingsRepository

class SettingsRepositoryRegistry:
    """
    Registry for managing settings repositories.
    
    This class allows dynamic registration and discovery of settings
    repository implementations, making it easy to add new settings types.
    """
    
    def __init__(self):
        """Initialize the repository registry."""
        self._repository_classes: Dict[str, Type[ISettingsRepository]] = {}
        self._repositories: Dict[str, ISettingsRepository] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Auto-register core repositories
        self._register_core_repositories()
    
    def register_repository_class(self, settings_type: str, repository_class: Type[ISettingsRepository]) -> None:
        """
        Register a repository class for a settings type.
        
        Args:
            settings_type: Identifier for the settings type
            repository_class: Repository class to register
        """
        self._repository_classes[settings_type] = repository_class
        self.logger.debug(f"Registered repository class for {settings_type}: {repository_class.__name__}")
    
    def create_repository(self, settings_type: str, file_path: Optional[str] = None) -> ISettingsRepository:
        """
        Create a repository instance for the given settings type.
        
        Args:
            settings_type: Identifier for the settings type
            file_path: Optional path to the settings file
        
        Returns:
            Repository instance for the settings type
        
        Raises:
            ValueError: If the settings type is not registered
        """
        if settings_type not in self._repository_classes:
            raise ValueError(f"No repository class registered for settings type: {settings_type}")
        
        repository_class = self._repository_classes[settings_type]
        repository = repository_class(file_path)
        
        # Cache the repository instance
        self._repositories[settings_type] = repository
        
        self.logger.debug(f"Created repository instance for {settings_type}")
        return repository
    
    def get_repository(self, settings_type: str) -> Optional[ISettingsRepository]:
        """
        Get an existing repository instance.
        
        Args:
            settings_type: Identifier for the settings type
        
        Returns:
            Repository instance if it exists, None otherwise
        """
        return self._repositories.get(settings_type)
    
    def get_registered_types(self) -> list[str]:
        """
        Get list of all registered settings types.
        
        Returns:
            List of registered settings type identifiers
        """
        return list(self._repository_classes.keys())
    
    def is_type_registered(self, settings_type: str) -> bool:
        """
        Check if a settings type is registered.
        
        Args:
            settings_type: Identifier for the settings type
        
        Returns:
            True if the type is registered, False otherwise
        """
        return settings_type in self._repository_classes
    
    def _register_core_repositories(self) -> None:
        """Register core repository types."""
        try:

            self.register_repository_class("camera", CameraSettingsRepository)
            self.register_repository_class("robot_config", RobotSettingsRepository)
            self.register_repository_class("robot_calibration_settings", RobotCalibrationSettingsRepository)
            
            self.logger.info("Core repositories registered successfully")
        except ImportError as e:
            self.logger.error(f"Failed to register core repositories: {e}")


# Global registry instance
_repository_registry = SettingsRepositoryRegistry()


def get_settings_repository_registry() -> SettingsRepositoryRegistry:
    """
    Get the global settings repository registry.
    
    Returns:
        The global SettingsRepositoryRegistry instance
    """
    return _repository_registry