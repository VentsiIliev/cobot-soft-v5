from frontend.core.shared.base_widgets.AppWidget import AppWidget
from plugins.core.settings.ui.SettingsContent import SettingsContent
from communication_layer.api.v1.endpoints import camera_endpoints


class SettingsAppWidget(AppWidget):
    """Settings application widget using clean service pattern"""

    def __init__(self, parent=None, controller=None, controller_service=None):
        self.controller = controller  # Keep for backward compatibility
        self.controller_service = controller_service
        super().__init__("Settings", parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button
        self.setStyleSheet("""
                   QWidget {
                       background-color: #f8f9fa;
                       font-family: 'Segoe UI', Arial, sans-serif;
                       color: #000000;  /* Force black text */
                   }
                   
               """)
        # Replace the content with actual SettingsContent if available
        try:

            # Remove the placeholder content - no more callback needed!
            # Settings will be handled via signals using the clean service pattern

            def updateCameraFeedCallback():

                frame = self.controller.handle(camera_endpoints.UPDATE_CAMERA_FEED)
                self.content_widget.updateCameraFeed(frame)

            def onRawModeRequested(state):
                if state:
                    print("Raw mode requested SettingsAppWidget")
                    self.controller.handle(camera_endpoints.CAMERA_ACTION_RAW_MODE_ON)
                else:
                    print("Raw mode off requested SettingsAppWidget")
                    self.controller.handle(camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF)

            try:
                # Create SettingsContent with controller_service - it will emit signals instead
                self.content_widget = SettingsContent(
                    controller=self.controller,
                    controller_service=self.controller_service
                )

                # Connect to the new unified signal for settings changes
                self.content_widget.setting_changed.connect(self._handle_setting_change)
                
                # Connect action signals
                self.content_widget.update_camera_feed_requested.connect(lambda: updateCameraFeedCallback())
                self.content_widget.raw_mode_requested.connect(lambda state: onRawModeRequested(state))

                # Connect glue types management signals if glue settings tab exists
                self._setup_glue_types_signals()

            except Exception as e:
                import traceback
                traceback.print_exc()
                raise e

            if self.controller is None:
                raise ValueError("Controller is not set for SettingsAppWidget")

            # Settings will be loaded lazily when each tab is selected
            # This prevents blocking the UI on startup
            print("Settings plugin loaded - settings will be fetched when tabs are selected")

            # content_widget.show()
            print("SettingsContent loaded successfully")
            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:

            # Keep the placeholder if the UserManagementWidget is not available
            print("SettingsContent not available, using placeholder")

    def _handle_setting_change(self, key: str, value, component_type: str):
        """
        Handle setting changes using the clean service pattern.
        This replaces the old callback approach with signal-based handling.
        
        Args:
            key: The setting key
            value: The new value
            component_type: The component class name
        """
        print(f"🔧 Setting change signal received: {component_type}.{key} = {value}")
        
        # Use the clean service pattern
        result = self.controller_service.settings.update_setting(key, value, component_type)
        
        if result:
            print(f"✅ Settings update successful: {result.message}")
            # Could show success toast here
        else:
            print(f"❌ Settings update failed: {result.message}")
            # Could show error dialog here
    
    def _setup_glue_types_signals(self):
        """Setup signal connections for glue types management."""
        if not hasattr(self.content_widget, 'glueSettingsTabLayout'):
            return

        glue_layout = self.content_widget.glueSettingsTabLayout
        if not hasattr(glue_layout, 'glue_type_tab'):
            return

        tab = glue_layout.glue_type_tab

        # Connect request signals to controller
        tab.glue_types_load_requested.connect(self._handle_load_glue_types)
        tab.glue_type_add_requested.connect(self._handle_add_glue_type)
        tab.glue_type_update_requested.connect(self._handle_update_glue_type)
        tab.glue_type_remove_requested.connect(self._handle_remove_glue_type)

        # Initial load
        self._handle_load_glue_types()

    def _handle_load_glue_types(self):
        """Load glue types via controller."""
        from communication_layer.api.v1.endpoints import glue_endpoints
        from communication_layer.api.v1.Response import Response

        response_dict = self.controller.handle(glue_endpoints.GLUE_TYPES_GET)

        # Update UI with response
        if hasattr(self.content_widget, 'glueSettingsTabLayout'):
            glue_layout = self.content_widget.glueSettingsTabLayout
            if hasattr(glue_layout, 'glue_type_tab'):
                glue_layout.glue_type_tab.update_glue_types_from_response(response_dict)

    def _handle_add_glue_type(self, name: str, description: str):
        """Add glue type via controller."""
        from communication_layer.api.v1.Response import Response
        from PyQt6.QtWidgets import QMessageBox

        response_dict = self.controller.handleAddGlueType(name, description)
        response = Response.from_dict(response_dict)

        if response.status == "success":
            # Reload all glue types
            self._handle_load_glue_types()
            QMessageBox.information(self, "Success", response.message or "Glue type added successfully")
        else:
            QMessageBox.warning(self, "Error", response.message or "Failed to add glue type")

    def _handle_update_glue_type(self, glue_id: str, name: str, description: str):
        """Update glue type via controller."""
        from communication_layer.api.v1.Response import Response
        from PyQt6.QtWidgets import QMessageBox

        response_dict = self.controller.handleUpdateGlueType(glue_id, name, description)
        response = Response.from_dict(response_dict)

        if response.status == "success":
            self._handle_load_glue_types()
            QMessageBox.information(self, "Success", response.message or "Glue type updated successfully")
        else:
            QMessageBox.warning(self, "Error", response.message or "Failed to update glue type")

    def _handle_remove_glue_type(self, glue_id: str):
        """Remove glue type via controller."""
        from communication_layer.api.v1.Response import Response
        from PyQt6.QtWidgets import QMessageBox

        response_dict = self.controller.handleRemoveGlueType(glue_id)
        response = Response.from_dict(response_dict)

        if response.status == "success":
            self._handle_load_glue_types()
            QMessageBox.information(self, "Success", response.message or "Glue type deleted successfully")
        else:
            QMessageBox.warning(self, "Error", response.message or "Failed to delete glue type")

    def clean_up(self):
        """Clean up resources when widget is destroyed"""
        if hasattr(self, 'content_widget') and self.content_widget:
            self.content_widget.clean_up()