"""
Plugin Interface Definitions

Base interfaces and metadata classes for the plugin system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

from PyQt6.QtWidgets import QWidget


class PluginCategory(Enum):
    """Plugin categories for organization and loading priority"""
    CORE = "core"           # Essential system plugins
    FEATURE = "feature"     # Application feature plugins  
    EXTENSION = "extension" # Optional/third-party plugins
    TOOL = "tool"          # Utility and tool plugins


class PluginPermission(Enum):
    """Plugin permission system"""
    SETTINGS_READ = "settings.read"
    SETTINGS_WRITE = "settings.write"
    CAMERA_ACCESS = "camera.access"
    ROBOT_CONTROL = "robot.control"
    FILE_SYSTEM = "file.system"
    NETWORK_ACCESS = "network.access"


@dataclass
class PluginMetadata:
    """Plugin metadata and configuration"""
    name: str
    version: str
    author: str
    description: str
    category: PluginCategory = PluginCategory.FEATURE
    dependencies: List[str] = None
    permissions: List[PluginPermission] = None
    auto_load: bool = True
    min_app_version: str = "1.0.0"
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.permissions is None:
            self.permissions = []


class IPlugin(ABC):
    """
    Base interface for all plugins.
    
    This interface defines the contract that all plugins must implement
    to participate in the plugin system.
    """
    
    def __init__(self):
        self.controller_service = None
        self._is_initialized = False
        self._widget_cache = None
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        Plugin metadata and information.
        
        Returns:
            PluginMetadata with plugin details
        """
        pass
    
    @property
    @abstractmethod 
    def icon_path(self) -> str:
        """
        Path to plugin icon (relative to plugin directory).
        
        Returns:
            String path to icon file
        """
        pass
    
    @abstractmethod
    def initialize(self, controller_service) -> bool:
        """
        Initialize plugin with required services.
        
        Args:
            controller_service: Main controller service for backend operations
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create the main plugin widget/UI.
        
        Args:
            parent: Parent widget for the plugin UI
            
        Returns:
            QWidget representing the plugin's main interface
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleanup resources when plugin is unloaded.
        
        This method should release any resources, close connections,
        and perform necessary cleanup operations.
        """
        pass
    
    # Optional methods with default implementations
    
    def can_load(self) -> bool:
        """
        Check if plugin can be loaded.
        
        Override this to add custom loading conditions like
        permissions, dependencies, feature flags, etc.
        
        Returns:
            True if plugin can be loaded, False otherwise
        """
        return True
    
    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get plugin configuration schema for UI generation.
        
        Returns:
            Dictionary defining configuration options, or None
        """
        return None
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure plugin with provided settings.
        
        Args:
            config: Plugin configuration dictionary
            
        Returns:
            True if configuration successful, False otherwise
        """
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current plugin status and health information.
        
        Returns:
            Dictionary with status information
        """
        return {
            "initialized": self._is_initialized,
            "name": self.metadata.name,
            "version": self.metadata.version,
            "category": self.metadata.category.value
        }
    
    # Internal helper methods
    
    def _mark_initialized(self, success: bool = True) -> None:
        """Mark plugin as initialized"""
        self._is_initialized = success
    
    def _clear_widget_cache(self) -> None:
        """Clear cached widget instance"""
        self._widget_cache = None