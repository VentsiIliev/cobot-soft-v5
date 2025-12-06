import os
import sys
from typing import Optional
from PyQt6.QtWidgets import QWidget

# Import plugin base classes
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from plugins.base.plugin_interface import IPlugin, PluginMetadata, PluginCategory, PluginPermission

# Import the widget
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))
from plugins.core.weight_cells_settings_plugin.ui.GlueWeightCellSettingsAppWidget import GlueWeightCellSettingsAppWidget


class GlueWeightCellsSettingsPlugin(IPlugin):
    def __init__(self):
        super().__init__()
        self._widget_instance = None


    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata and information"""
        return PluginMetadata(
            name="Glue Weight Cell Settings",
            version="1.0.0",
            author="PL Team",
            description="Manage settings for glue weight cells cells within the application",
            category=PluginCategory.CORE,
            dependencies=[],
            permissions=[
                PluginPermission.FILE_SYSTEM,
            ],
            auto_load=True,
            min_app_version="1.0.0"
        )

    @property
    def icon_path(self) -> str:
        """Path to plugin icon"""
        return os.path.join(os.path.dirname(__file__), "icons", "weight_cell.png")

    def initialize(self, controller_service) -> bool:
        """
             Initialize the user management plugin.

             Args:
                 controller_service: Main controller service for backend operations

             Returns:
                 True if initialization successful, False otherwise
             """
        try:
            # store controller service for later widget creation
            self.controller_service = controller_service
            self._mark_initialized(True)
            return True
        except Exception as e:
            print(f"Glue wight cells settings plugin initialization failed: {e}")
            self._mark_initialized(False)
            return False

    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create the glue weight cell settings widget.
        
        Args:
            parent: Parent widget for the settings interface
            
        Returns:
            QWidget representing the weight cell settings interface
        """
        if not self._is_initialized:
            raise RuntimeError("Plugin not initialized")

        # Create widget instance if it doesn't exist
        if not self._widget_instance:
            self._widget_instance = GlueWeightCellSettingsAppWidget(
                parent=parent,
                controller=self.controller_service.controller if hasattr(self, 'controller_service') else None,
                controller_service=self.controller_service if hasattr(self, 'controller_service') else None
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
            print(f"Error during weight cells settings plugin cleanup: {e}")

    def can_load(self) -> bool:
        return  True

    def get_status(self) -> dict:
        """Get plugin status"""
        status = super().get_status()
        status.update({
            "widget_created": self._widget_instance is not None,
            "controller_service_available": self.controller_service is not None if hasattr(self, 'controller_service') else False
        })
        return status