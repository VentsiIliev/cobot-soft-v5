import os
import sys
from typing import Optional
from PyQt6.QtWidgets import QWidget

# Import plugin base classes
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from plugins.base.plugin_interface import IPlugin, PluginMetadata, PluginCategory, PluginPermission

# Import the widget
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))
from plugins.core.modbus_settings_plugin.ui.ModbusSettingsAppWidget import ModbusSettingsAppWidget


class ModbusSettingsPlugin(IPlugin):
    def __init__(self):
        super().__init__()
        self._metadata = PluginMetadata(
            name="Modbus Settings",
            version="1.0.0",
            author="PL Team",
            description="Configure Modbus RTU communication settings",
            category=PluginCategory.CORE,
            permissions=[PluginPermission.FILE_SYSTEM]
        )
        self._widget = None

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return self._metadata

    @property
    def icon_path(self) -> str:
        """Return path to plugin icon"""
        return os.path.join(os.path.dirname(__file__), "icons", "modbus.png")

    def initialize(self, controller_service) -> bool:
        """
        Initialize the Modbus Settings plugin.

        Args:
            controller_service: Main controller service for backend operations

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Store controller service for later widget creation
            self.controller_service = controller_service
            self._mark_initialized(True)
            print(f"[{self.metadata.name}] Plugin initialized")
            return True
        except Exception as e:
            print(f"Modbus Settings plugin initialization failed: {e}")
            self._mark_initialized(False)
            return False

    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create the Modbus Settings widget.

        Args:
            parent: Parent widget for the settings interface

        Returns:
            QWidget representing the Modbus Settings interface
        """
        if not self._is_initialized:
            raise RuntimeError("Plugin not initialized")

        # Create widget instance if it doesn't exist
        if not self._widget:
            self._widget = ModbusSettingsAppWidget(
                parent=parent,
                controller=self.controller_service.controller if hasattr(self, 'controller_service') else None,
                controller_service=self.controller_service if hasattr(self, 'controller_service') else None
            )
            print(f"Created plugin widget for: {self.metadata.name}")

        return self._widget

    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        try:
            if self._widget:
                # Clean up widget if it has a cleanup method
                if hasattr(self._widget, 'clean_up'):
                    self._widget.clean_up()
                self._widget = None

            self.controller_service = None
            self._mark_initialized(False)
            print(f"[{self.metadata.name}] Plugin cleanup")

        except Exception as e:
            print(f"Error during Modbus Settings plugin cleanup: {e}")

    def can_load(self) -> bool:
        """Check if plugin can be loaded"""
        return True

    def get_status(self) -> dict:
        """Get plugin status"""
        status = super().get_status()
        status.update({
            "widget_created": self._widget is not None,
            "controller_service_available": self.controller_service is not None if hasattr(self, 'controller_service') else False
        })
        return status
