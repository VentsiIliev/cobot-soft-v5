"""
Base JSON settings repository implementation.

This module provides a common implementation for settings repositories
that store their data in JSON format.
"""

import json
import os
from typing import Optional, TypeVar
import logging

from core.services.settings.interfaces.ISettingsRepository import (
    ISettingsRepository, SettingsLoadError, SettingsSaveError
)

T = TypeVar('T')


class BaseJsonSettingsRepository(ISettingsRepository[T]):
    """
    Base implementation for JSON-based settings repositories.
    
    This class provides common functionality for loading and saving
    settings to/from JSON files, while leaving the specific settings
    object creation and conversion to subclasses.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the JSON repository.
        
        Args:
            file_path: Path to the JSON settings file
        """
        super().__init__(file_path)
        self.logger = logging.getLogger(self.__class__.__name__)

    def load(self) -> T:
        """
        Load settings from JSON file.

        Returns:
            The settings object with loaded data, or default settings if file doesn't exist

        Raises:
            SettingsLoadError: If loading fails
        """
        try:
            if not self.file_path:
                print(f"No file path specified for {self.get_settings_type()} settings. Using defaults.")
                return self.get_default()

            if not os.path.exists(self.file_path):
                # File missing: create it populated with defaults, then return defaults
                default_settings = self.get_default()
                try:
                    dir_path = os.path.dirname(self.file_path) or "."
                    os.makedirs(dir_path, exist_ok=True)
                    with open(self.file_path, "w") as file:
                        json.dump(self.to_dict(default_settings), file, indent=2)
                    print(f"Settings file not found: {self.file_path}. Created with defaults.")
                except Exception as e:
                    raise SettingsLoadError(f"Failed to create default settings file {self.file_path}: {e}")
                return default_settings

            with open(self.file_path, 'r') as file:
                data = json.load(file)
                settings = self.from_dict(data)
                print(f"Loaded {self.get_settings_type()} settings from {self.file_path}")
                return settings

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Failed to load {self.get_settings_type()} settings: {e}")
            return self.get_default()
        except Exception as e:
            raise SettingsLoadError(f"Failed to load {self.get_settings_type()} settings: {e}")
    
    def save(self, settings: T) -> None:
        """
        Save settings to JSON file.
        
        Args:
            settings: The settings object to save
        
        Raises:
            SettingsSaveError: If saving fails
        """
        try:
            if not self.file_path:
                raise SettingsSaveError(f"No file path specified for {self.get_settings_type()} settings")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            data = self.to_dict(settings)
            with open(self.file_path, 'w') as file:
                json.dump(data, file, indent=2)
                
            print(f"Saved {self.get_settings_type()} settings to {self.file_path}")
            
        except Exception as e:
            raise SettingsSaveError(f"Failed to save {self.get_settings_type()} settings: {e}")
    
    def exists(self) -> bool:
        """
        Check if the settings file exists.
        
        Returns:
            True if the settings file exists, False otherwise
        """
        return self.file_path is not None and os.path.exists(self.file_path)