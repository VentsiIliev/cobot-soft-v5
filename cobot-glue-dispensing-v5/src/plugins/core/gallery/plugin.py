"""
Gallery Plugin Implementation

Main plugin class for the workpiece gallery management system.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import QWidget

# Import plugin base classes
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from plugins.base.plugin_interface import IPlugin, PluginMetadata, PluginCategory, PluginPermission

# Import the gallery widget
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))
from plugins.core.gallery.ui.GalleryAppWidget import GalleryAppWidget


class GalleryPlugin(IPlugin):
    """
    Gallery plugin for workpiece gallery management.
    
    Provides access to saved workpieces with thumbnail view,
    editing capabilities, and workpiece selection functionality.
    """
    
    def __init__(self):
        super().__init__()
        self._widget_instance = None
    
    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata and information"""
        return PluginMetadata(
            name="Gallery",
            version="1.0.0",
            author="PL Team",
            description="Workpiece gallery management with thumbnail view and editing capabilities",
            category=PluginCategory.CORE,
            dependencies=[],
            permissions=[
                PluginPermission.FILE_SYSTEM
            ],
            auto_load=True,
            min_app_version="1.0.0"
        )
    
    @property
    def icon_path(self) -> str:
        """Path to plugin icon"""
        return os.path.join(os.path.dirname(__file__), "icons", "gallery.png")
    
    def initialize(self, controller_service) -> bool:
        """
        Initialize the gallery plugin.
        
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
            print(f"Gallery plugin initialization failed: {e}")
            self._mark_initialized(False)
            return False
    
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create the gallery widget.
        
        Args:
            parent: Parent widget for the gallery interface
            
        Returns:
            QWidget representing the gallery interface
        """
        if not self._is_initialized:
            raise RuntimeError("Plugin not initialized")
        
        # Create widget instance if it doesn't exist
        if not self._widget_instance:
            self._widget_instance = GalleryAppWidget(

                controller=self.controller_service.controller,  # For backward compatibility
                controller_service=self.controller_service
            )
        
        return self._widget_instance
    
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        try:
            if self._widget_instance:
                # Clean up widget if it has a cleanup method
                if hasattr(self._widget_instance, 'clean_up'):
                    self._widget_instance.clean_up()
                self._widget_instance = None
            
            self.controller_service = None
            self._mark_initialized(False)
            
        except Exception as e:
            print(f"Error during gallery plugin cleanup: {e}")
    
    def can_load(self) -> bool:
        """Check if plugin can be loaded"""
        # Gallery plugin should always be available
        return True
    
    def get_status(self) -> dict:
        """Get plugin status"""
        status = super().get_status()
        status.update({
            "widget_created": self._widget_instance is not None,
            "controller_service_available": self.controller_service is not None
        })
        return status