import os

from PyQt6.QtWidgets import QWidget

from plugins import PluginMetadata, IPlugin
from plugins.base import PluginCategory, PluginPermission
from plugins.core.user_management.ui.UserManagementAppWidget import UserManagementAppWidget


class UserManagementPlugin(IPlugin):
    def __init__(self):
        super().__init__()
        self._widget_instance = None

    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata and information"""
        return PluginMetadata(
            name="User Management",
            version="1.0.0",
            author="PL Team",
            description="Manage user accounts, roles, and permissions within the application",
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
        return os.path.join(os.path.dirname(__file__), "icons", "user_management.png")

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
            print(f"User Management plugin initialization failed: {e}")
            self._mark_initialized(False)
            return False

    def create_widget(self, parent=None, controller_service=None) -> QWidget:
        if not self._is_initialized:
            raise RuntimeError("Plugin not initialized")

        if not self._widget_instance:
            self._widget_instance = UserManagementAppWidget()

        print(f"Creating User Management widget: {self._widget_instance}")
        return self._widget_instance

    def cleanup(self) -> None:
        try:
            if self._widget_instance:
                if hasattr(self._widget_instance, 'cleanup'):
                    self._widget_instance.cleanup()
                self._widget_instance = None

            self._mark_initialized(False)
        except Exception as e:
            print(f"Error during User Management plugin cleanup: {e}")

    def can_load(self) -> bool:
        return  True

    def get_status(self):
        status = super().get_status()
        status.update({
            "widget_created": self._widget_instance is not None,
            "controller_service_set": hasattr(self, 'controller_service')
        })
        return status
