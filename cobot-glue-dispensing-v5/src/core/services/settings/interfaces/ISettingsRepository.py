"""
Interface for settings repository pattern.

This module provides a standardized interface for settings repositories,
allowing different settings types to implement their own storage and
retrieval logic while maintaining a consistent API.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Generic, TypeVar

# Generic type for settings objects
T = TypeVar('T')


class ISettingsRepository(ABC, Generic[T]):
    """
    Abstract base class for settings repositories.
    
    This interface defines the standard operations that all settings
    repositories must implement, providing a consistent API for
    settings management regardless of the underlying storage mechanism.
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize the repository.
        
        Args:
            file_path: Optional path to the settings file
        """
        self.file_path = file_path
    
    @abstractmethod
    def load(self) -> T:
        """
        Load settings from storage.
        
        Returns:
            The settings object with loaded data
        
        Raises:
            SettingsLoadError: If loading fails
        """
        pass
    
    @abstractmethod
    def save(self, settings: T) -> None:
        """
        Save settings to storage.
        
        Args:
            settings: The settings object to save
        
        Raises:
            SettingsSaveError: If saving fails
        """
        pass
    
    @abstractmethod
    def get_default(self) -> T:
        """
        Get default settings for this type.
        
        Returns:
            A settings object with default values
        """
        pass
    
    @abstractmethod
    def to_dict(self, settings: T) -> Dict[str, Any]:
        """
        Convert settings object to dictionary.
        
        Args:
            settings: The settings object to convert
        
        Returns:
            Dictionary representation of the settings
        """
        pass
    
    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> T:
        """
        Create settings object from dictionary.
        
        Args:
            data: Dictionary data to convert
        
        Returns:
            Settings object created from the data
        """
        pass
    
    @abstractmethod
    def get_settings_type(self) -> str:
        """
        Get the settings type identifier.
        
        Returns:
            String identifier for this settings type
        """
        pass


class SettingsRepositoryError(Exception):
    """Base exception for settings repository errors."""
    pass


class SettingsLoadError(SettingsRepositoryError):
    """Raised when settings loading fails."""
    pass


class SettingsSaveError(SettingsRepositoryError):
    """Raised when settings saving fails."""
    pass