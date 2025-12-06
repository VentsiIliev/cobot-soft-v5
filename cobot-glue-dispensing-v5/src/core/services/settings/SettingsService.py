"""
Refactored Settings Service using Repository Pattern.

This module provides a clean, extensible settings service that uses
the repository pattern to manage different types of settings.
"""

from typing import Dict, Any, Optional
import logging

from core.SettingsRepositoryRegistry import get_settings_repository_registry
from core.services.settings.interfaces.ISettingsRepository import ISettingsRepository, SettingsRepositoryError
from core.application.interfaces.application_settings_interface import ApplicationSettingsRegistry
from communication_layer.api.v1 import Constants

# Import update strategies
from core.services.settings.strategies import (
    SettingsUpdateStrategy,
    CameraSettingsUpdateStrategy,
    RobotConfigUpdateStrategy,
    RobotCalibrationSettingsUpdateStrategy,
    DefaultSettingsUpdateStrategy
)


class SettingsService:
    """
    Refactored settings service using repository pattern.
    
    This service provides a clean, extensible way to manage different
    types of settings by using repositories for each settings type.
    Adding new settings types is as simple as creating a new repository
    and registering it.
    """
    
    def __init__(self, settings_file_paths: Dict[str, str], 
                 settings_registry: ApplicationSettingsRegistry):
        """
        Initialize the settings service.
        
        Args:
            settings_file_paths: Dictionary mapping settings types to file paths
            settings_registry: Registry for application-specific settings
        """
        self.settings_file_paths = settings_file_paths or {}
        self.settings_registry = settings_registry
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Cache for loaded settings objects - initialize early
        self._settings_cache: Dict[str, Any] = {}
        
        # Get the repository registry
        self.repository_registry = get_settings_repository_registry()

        # Create repositories for each configured settings type
        self.repositories: Dict[str, ISettingsRepository] = {}
        self._initialize_repositories()

        # Initialize update strategies
        self._update_strategies: Dict[str, SettingsUpdateStrategy] = {
            "camera": CameraSettingsUpdateStrategy(),
            "robot_config": RobotConfigUpdateStrategy(),
            "robot_calibration_settings": RobotCalibrationSettingsUpdateStrategy(),
        }
        self._default_strategy = DefaultSettingsUpdateStrategy()

        # Load all settings
        self.load_all_settings()
    
    def _initialize_repositories(self) -> None:
        """Initialize repositories for all configured settings types."""
        for settings_type, file_path in self.settings_file_paths.items():
            try:
                if self.repository_registry.is_type_registered(settings_type):
                    repository = self.repository_registry.create_repository(settings_type, file_path)
                    self.repositories[settings_type] = repository
                    print(f"Initialized repository for {settings_type} at {file_path}")
                else:
                    print(f"No repository registered for settings type: {settings_type}")
            except Exception as e:
                print(f"Failed to initialize repository for {settings_type}: {e}")


    def load_all_settings(self) -> None:
        """Load all settings from their repositories."""
        for settings_type, repository in self.repositories.items():
            try:
                settings = repository.load()
                self._settings_cache[settings_type] = settings
                print(f"Loaded {settings_type} settings")
            except SettingsRepositoryError as e:
                print(f"Failed to load {settings_type} settings: {e}")
    
    def save_all_settings(self) -> None:
        """Save all settings to their repositories."""
        for settings_type, repository in self.repositories.items():
            try:
                settings = self._settings_cache.get(settings_type)
                if settings is not None:
                    repository.save(settings)
                    self.logger.debug(f"Saved {settings_type} settings")
            except SettingsRepositoryError as e:
                print(f"Failed to save {settings_type} settings: {e}")
    
    def get_settings(self, settings_type: str) -> Optional[Any]:
        """
        Get settings object for a specific type.
        
        Args:
            settings_type: The settings type identifier
        
        Returns:
            Settings object or None if not found
        """
        return self._settings_cache.get(settings_type)
    
    def update_settings(self, settings_type: str, settings_data: Dict[str, Any]) -> None:
        """
        Update settings for a specific type.

        This method uses the strategy pattern to delegate type-specific
        update logic to specialized strategy classes.

        Args:
            settings_type: The settings type identifier
            settings_data: Partial or complete settings data to update

        Raises:
            ValueError: If no repository found for the settings type
            SettingsRepositoryError: If there's an error saving settings
        """
        print(f"[SETTINGS SERVICE] HANDLING SETTINGS TYPE {settings_type} DATA {settings_data}")

        # Validate repository exists
        repository = self.repositories.get(settings_type)
        if repository is None:
            raise ValueError(f"No repository found for settings type: {settings_type}")

        try:
            # Get the appropriate update strategy (or default)
            strategy = self._update_strategies.get(settings_type, self._default_strategy)

            # Get current settings
            current_settings = self.get_settings(settings_type)


            # Apply updates using strategy
            updated_settings = strategy.update(current_settings, settings_data, repository)

            # Update cache
            self._settings_cache[settings_type] = updated_settings

            # Save to file
            repository.save(updated_settings)

            # Perform any post-update notifications
            strategy.notify(settings_data)

            print(f"✅ Updated and saved {settings_type} settings: {list(settings_data.keys())}")

        except SettingsRepositoryError as e:
            print(f"❌ Failed to update {settings_type} settings: {e}")
            raise
        except Exception as e:
            print(f"❌ Error updating {settings_type} settings: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_settings_by_resource(self, key: str) -> Dict[str, Any]:
        """
        Get settings data by resource key (for backward compatibility).
        
        Args:
            key: The resource key
        
        Returns:
            Settings data as dictionary
        """
        # Handle core settings
        print(f"SettingsService: Getting settings for key: {key}")
        if key == Constants.REQUEST_RESOURCE_CAMERA:
            settings = self.get_settings("camera")
            if settings is not None:
                repository = self.repositories.get("camera")
                return repository.to_dict(settings) if repository else {}
        
        # Handle robot calibration settings
        if key == "robot_calibration_settings":
            settings = self.get_settings("robot_calibration_settings")
            if settings is not None:
                repository = self.repositories.get("robot_calibration_settings")
                return repository.to_dict(settings) if repository else {}
            return {}

        if key == Constants.REQUEST_RESOURCE_ROBOT:
            settings = self.get_settings("robot_config")
            if settings is not None:
                repository = self.repositories.get("robot_config")
                return repository.to_dict(settings) if repository else {}

        # Handle application-specific settings through registry
        resource_map = {
            "Glue": "glue",
            "Paint": "paint",
        }
        
        settings_type = resource_map.get(key, key.lower())
        
        if self.settings_registry.is_type_registered(settings_type):
            try:
                handler = self.settings_registry.get_handler(settings_type)
                return handler.handle_get_settings()
            except KeyError:
                print(f"Settings handler not found for type: {settings_type}")
                return {}
        
        print(f"Unknown settings key: {key}")
        return {}
    
    def updateSettings(self, settings: Dict[str, Any]) -> None:
        """
        Update settings (for backward compatibility).
        
        Args:
            settings: Settings dictionary with 'header' key
        """
        if 'header' not in settings:
            raise ValueError("Settings dictionary must contain a 'header' key")
        
        header = settings['header']
        
        if header == Constants.REQUEST_RESOURCE_CAMERA:
            # Remove header and update camera settings
            camera_data = {k: v for k, v in settings.items() if k != 'header'}
            self.update_settings("camera", camera_data)
            return

        if header == Constants.REQUEST_RESOURCE_ROBOT:
            # Remove header and update robot settings
            robot_data = {k: v for k, v in settings.items() if k != 'header'}
            self.update_settings("robot_config", robot_data)
            return

        # Handle application-specific settings through registry
        resource_map = {"Glue": "glue"}
        settings_type = resource_map.get(header, header.lower())
        
        if self.settings_registry.is_type_registered(settings_type):
            try:
                handler = self.settings_registry.get_handler(settings_type)
                # Remove header for handler
                handler_data = {k: v for k, v in settings.items() if k != 'header'}
                handler.handle_set_settings(handler_data)
            except KeyError:
                print(f"Settings handler not found for type: {settings_type}")
        else:
            print(f"Unknown settings type: {settings_type}")
    
    # Convenience methods for specific settings types
    
    def get_camera_settings(self):
        """Get camera settings object."""
        return self.get_settings("camera")
    
    def get_robot_config(self):
        """Get robot configuration object."""
        return self.get_settings("robot_config")

    def get_robot_calibration_settings(self):
        return self.get_settings("robot_calibration_settings")

    def register_settings_type(self, settings_type: str, repository_class) -> None:
        """
        Register a new settings type with its repository.
        
        Args:
            settings_type: Identifier for the settings type
            repository_class: Repository class for this settings type
        """
        self.repository_registry.register_repository_class(settings_type, repository_class)
        
        # If we have a file path for this type, initialize the repository
        file_path = self.settings_file_paths.get(settings_type)
        if file_path:
            try:
                repository = self.repository_registry.create_repository(settings_type, file_path)
                self.repositories[settings_type] = repository
                
                # Load settings for this type
                settings = repository.load()
                self._settings_cache[settings_type] = settings
                
                print(f"Registered and initialized new settings type: {settings_type}")
            except Exception as e:
                print(f"Failed to initialize repository for new type {settings_type}: {e}")
    
    def get_available_settings_types(self) -> list[str]:
        """
        Get list of all available settings types.

        Returns:
            List of registered settings type identifiers
        """
        return self.repository_registry.get_registered_types()

    def register_update_strategy(self, settings_type: str, strategy: SettingsUpdateStrategy) -> None:
        """
        Register a custom update strategy for a settings type.

        This allows applications to provide custom update logic for their
        settings types without modifying the core SettingsService.

        Args:
            settings_type: Identifier for the settings type
            strategy: Update strategy instance for this settings type

        Example:
            >>> custom_strategy = MyCustomSettingsStrategy()
            >>> service.register_update_strategy("my_custom_type", custom_strategy)
        """
        self._update_strategies[settings_type] = strategy
        print(f"Registered custom update strategy for: {settings_type}")
    
    def reload_robot_config(self) -> None:
        """Reload the robot configuration from its repository."""
        try:
            robot_config = self.get_settings("robot_config")
            if robot_config:
                repository = self.repositories.get("robot_config")
                if repository:
                    reloaded_config = repository.load()
                    self._settings_cache["robot_config"] = reloaded_config
                    print("Robot configuration reloaded successfully.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Failed to reload robot configuration: {e}")
    
    def updateCameraSettings(self, settings: Dict[str, Any]) -> None:
        """
        Update camera-specific settings and persist them to file.
        
        Args:
            settings: Dictionary containing camera settings data
        """
        print(f"Updating Camera Settings: {settings}")
        
        try:
            # Get current camera settings
            camera_settings = self.get_settings("camera")
            if camera_settings is None:
                print("No camera settings found")
                return
            
            # Update camera settings using the existing updateSettings method
            # This will handle the flat and nested format conversion
            camera_settings.updateSettings(settings)
            
            # Save the updated settings
            repository = self.repositories.get("camera")
            if repository:
                repository.save(camera_settings)
                print("Camera settings saved successfully")
            else:
                print("No camera repository found")
                
        except Exception as e:
            print(f"Failed to update camera settings: {e}")
            raise