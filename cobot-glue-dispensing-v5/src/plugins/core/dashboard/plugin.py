import os
from typing import Optional
from PyQt6.QtWidgets import QWidget

# Import plugin base classes
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from plugins.base.plugin_interface import IPlugin, PluginMetadata, PluginCategory

# Import the existing settings widget
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))
from plugins.core.dashboard.ui.DashboardAppWidget import DashboardAppWidget

class DashboardPlugin(IPlugin):
    """
    Dashboard plugin for main application dashboard.

    Provides access to the main dashboard interface through a
    unified plugin architecture.
    """

    def __init__(self):
        super().__init__()
        self._widget_instance = None

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata and information"""
        return PluginMetadata(
            name="Dashboard",
            version="1.0.0",
            author="PL Team",
            description="Main application dashboard interface",
            category=PluginCategory.CORE,
            dependencies=[],
            permissions=[],
            auto_load=True,
            min_app_version="1.0.0"
        )

    @property
    def icon_path(self) -> str:
        """Path to plugin icon"""
        return os.path.join(os.path.dirname(__file__), "icons", "dashboard.png")

    def initialize(self, controller_service) -> bool:
        """
        Initialize the dashboard plugin.

        Args:
            controller_service: The controller service instance.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            self.controller_service = controller_service
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error initializing Dashboard plugin: {e}")
            return False

    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create and return the dashboard widget.

        Args:
            parent: Optional parent widget.

        Returns:
            QWidget: The dashboard widget instance.
        """
        try:
            controller = self.controller_service.get_controller()
            widget = DashboardAppWidget(controller=controller)
            return widget
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Return a fallback widget with the required signal
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))
            from frontend.core.shared.base_widgets.AppWidget import AppWidget
            return AppWidget(app_name=f"Dashboard Error: {e}")

    def cleanup(self) -> None:
        """Cleanup resources used by the dashboard plugin"""
        if self._widget_instance:
            self._widget_instance.deleteLater()
            self._widget_instance = None

    def can_load(self) -> bool:
        """
        Determine if the plugin can be loaded.

        Returns:
            bool: True if the plugin can be loaded, False otherwise.
        """
        return True

    def get_status(self) -> str:
        """
        Get the current status of the plugin.

        Returns:
            str: Status message.
        """
        return "Dashboard plugin is ready."