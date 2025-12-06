from typing import Optional, Dict, Any

from PyQt6.QtWidgets import QWidget

from plugins import IPlugin, PluginMetadata
from plugins.base import PluginCategory, PluginPermission


class DxfBrowserPlugin(IPlugin):
    """
    DXF Browser plugin for managing and viewing DXF files.

    Provides functionality to browse, preview, and manage DXF files within the application.
    """

    def __init__(self):
        super().__init__()
        self._widget_instance = None

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata and information"""
        return PluginMetadata(
            name="DXF Browser",
            version="1.0.0",
            author="PL Team",
            description="DXF file management and viewing",
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
        import os
        return os.path.join(os.path.dirname(__file__), "icons", "dxf_browser.png")

    def initialize(self, controller_service) -> bool:
        """
        Initialize the DXF Browser plugin.

        Args:
            controller_service: Main controller service for backend operations
        """
        try:
            self.controller_service = controller_service
            self._mark_initialized(True)
            return True
        except Exception as e:
            print(f"Error initializing DXF Browser plugin: {e}")
            return False

    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """Create and return the DXF Browser widget instance"""
        try:
            from .ui.DxfBrowserAppWidget import DxfBrowserAppWidget
            
            controller = None
            if self.controller_service:
                controller = self.controller_service.get_controller()
            
            widget = DxfBrowserAppWidget(
                parent=parent,
                controller=controller,
                controller_service=self.controller_service
            )
            return widget
        except Exception as e:
            print(f"Error creating DXF Browser widget: {e}")
            # Return a fallback widget
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))
            from frontend.core.shared.base_widgets.AppWidget import AppWidget
            return AppWidget(app_name=f"DXF Browser Error: {e}")

    def cleanup(self) -> None:
        """Cleanup resources when the plugin is unloaded"""
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

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the plugin"""
        status = super().get_status()
        status.update({
            "widget_created": self._widget_instance is not None,
            "controller_service_available": self.controller_service is not None
        })
        return status
