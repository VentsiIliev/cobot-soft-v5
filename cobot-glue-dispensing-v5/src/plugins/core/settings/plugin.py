"""
Settings Plugin Implementation

Main plugin class for the settings management system.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import QWidget

# Import plugin base classes
import sys

from frontend.core.shared.base_widgets.AppWidget import AppWidget

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from plugins.base.plugin_interface import IPlugin, PluginMetadata, PluginCategory, PluginPermission

# Import the existing settings widget
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))
from plugins.core.settings.ui.SettingsAppWidget import SettingsAppWidget


class SettingsPlugin(IPlugin):
    """
    Settings plugin for system configuration management.
    
    Provides access to camera, robot, and glue settings through a
    unified interface with the new service architecture.
    """
    
    def __init__(self):
        super().__init__()
        self._widget_instance = None
    
    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata and information"""
        return PluginMetadata(
            name="Settings",
            version="1.0.0",
            author="PL Team",
            description="System settings management for camera, robot, and glue configurations",
            category=PluginCategory.CORE,
            dependencies=[],
            permissions=[
                PluginPermission.SETTINGS_READ,
                PluginPermission.SETTINGS_WRITE
            ],
            auto_load=True,
            min_app_version="1.0.0"
        )
    
    @property
    def icon_path(self) -> str:
        """Path to plugin icon"""
        return os.path.join(os.path.dirname(__file__), "icons", "settings.png")
    
    def initialize(self, controller_service) -> bool:
        """
        Initialize the settings plugin.
        
        Args:
            controller_service: Main controller service for backend operations
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.controller_service = controller_service
            self._mark_initialized(True)
            return True
        except Exception as e:
            print(f"Settings plugin initialization failed: {e}")
            self._mark_initialized(False)
            return False
    
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create the settings widget.
        
        Args:
            parent: Parent widget for the settings interface
            
        Returns:
            QWidget representing the settings interface
        """
        if not self._is_initialized:
            raise RuntimeError("Plugin not initialized")
        

        print("[SettingsPlugin] Creating cached settings widget instance")
        self._widget_instance = SettingsAppWidget(
            controller=self.controller_service.controller,  # For backward compatibility
            controller_service=self.controller_service
        )
        # self._widget_instance = AppWidget(app_name="Settings",parent=None)

        return self._widget_instance
    
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        try:
            if self._widget_instance:
                self._widget_instance.clean_up()
                self._widget_instance = None
            
            self.controller_service = None
            self._mark_initialized(False)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error during settings plugin cleanup: {e}")
    
    def can_load(self) -> bool:
        """Check if plugin can be loaded"""
        # Settings plugin should always be available
        return True
    
    def get_status(self) -> dict:
        """Get plugin status"""
        status = super().get_status()
        status.update({
            "widget_created": self._widget_instance is not None,
            "controller_service_available": self.controller_service is not None
        })
        return status