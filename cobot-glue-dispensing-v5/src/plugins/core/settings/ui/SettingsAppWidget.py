from typing import Dict, Optional, Tuple

from frontend.core.shared.base_widgets.AppWidget import AppWidget
from plugins.core.settings.ui.SettingsContent import SettingsContent
from communication_layer.api.v1.endpoints import camera_endpoints
from plugins.core.settings.ui.glue_cell_settings_tab.models.cell_config import (
    CellConfig, ConnectionSettings, CalibrationSettings, MeasurementSettings
)
from plugins.core.settings.ui.glue_cell_settings_tab.utils.validators import (
    parse_glue_cell_key, get_field_section_mapping
)


class SettingsAppWidget(AppWidget):
    """Settings application widget using clean service pattern"""

    def __init__(self, parent=None, controller=None, controller_service=None):
        self.controller = controller  # Keep for backward compatibility
        self.controller_service = controller_service

        # Cache for glue cell configurations (centralized data access)
        self.glue_cell_configs: Dict[int, CellConfig] = {}

        super().__init__("Settings", parent)

    def setup_ui(self):
        """
        Set up the user management specific UI"""
        super().setup_ui()  # Get the basic layout with the back button
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

                # Connect glue cell settings signals (centralized business logic)
                self._setup_glue_cell_signals()

                # Connect camera settings signals (centralized business logic)
                self._setup_camera_signals()

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
            # Could show the error dialog here
    
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

    def _setup_glue_cell_signals(self):
        """
        Setup signal connections for glue cell settings (CENTRALIZED PATTERN).

        Connects all signals from GlueCellSettingsUI to centralized handlers
        in SettingsAppWidget. This implements the DUMB UI / SMART Controller pattern.
        """
        if not hasattr(self.content_widget, 'glue_cell_tab'):
            print("⚠️ glue_cell_tab not found, skipping glue cell signals setup")
            return

        glue_cell_tab = self.content_widget.glue_cell_tab

        # Connect value change signal (backward compatibility)
        # This signal carries legacy format: "load_cell_1_zero_offset"
        glue_cell_tab.value_changed_signal.connect(self._handle_glue_cell_setting_change)

        # Connect new action signals
        glue_cell_tab.cell_changed_signal.connect(self._handle_cell_changed)
        glue_cell_tab.tare_requested_signal.connect(self._handle_tare_requested)
        glue_cell_tab.reset_requested_signal.connect(self._handle_reset_requested)

        print("✅ Glue cell signals connected to SettingsAppWidget")

        # Load all cell configurations (centralized data access)
        self._load_glue_cell_configs()

        # Initialize UI with first cell's config
        if self.glue_cell_configs:
            first_cell_id = min(self.glue_cell_configs.keys())
            glue_cell_tab.set_cell_config(self.glue_cell_configs[first_cell_id])
            print(f"✅ Initialized glue cell UI with Cell {first_cell_id}")

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

    # ============================================================================
    # Glue Cell Settings Handlers (Centralized Business Logic)
    # ============================================================================

    def _load_glue_cell_configs(self):
        """
        Load all glue cell configurations via controller_service.

        This is the centralized data loading point - ALL cell configs are
        loaded here and cached. UI components receive data via set_cell_config().
        """
        try:
            result = self.controller_service.settings.get_glue_cells_config()

            if result.success:
                cells_data = result.data.get('cells', [])

                for cell_dto in cells_data:
                    cell_id = cell_dto.get('id')
                    if cell_id:
                        # Parse DTO into dataclass
                        self.glue_cell_configs[cell_id] = CellConfig.from_dto(cell_dto)

                print(f"✅ Loaded {len(self.glue_cell_configs)} glue cell configurations")
            else:
                print(f"❌ Failed to load glue cell configs: {result.message}")
        except Exception as e:
            print(f"❌ Error loading glue cell configs: {e}")
            import traceback
            traceback.print_exc()

    def _handle_glue_cell_setting_change(self, key: str, value, className: str):
        """
        Handle ALL glue cell setting changes (CENTRALIZED BUSINESS LOGIC).

        This method receives signals from GlueCellSettingsUI and:
        1. Parses the legacy key format ("load_cell_1_zero_offset")
        2. Maps field to section (calibration/connection/measurement)
        3. Validates the change (e.g., motor address conflicts)
        4. Makes API call via controller_service
        5. Updates cached config
        6. Reloads UI if validation fails

        Args:
            key: Legacy format key (e.g., "load_cell_1_zero_offset")
            value: New value
            className: Component class name (for backward compatibility)
        """
        # Only handle glue cell keys
        if not key.startswith("load_cell_"):
            return

        try:
            # Parse key: "load_cell_1_zero_offset" → cell_id=1, field="zero_offset"
            cell_id, field_name = parse_glue_cell_key(key)

            # Get section mapping
            section_map = get_field_section_mapping()
            section = section_map.get(field_name)

            if not section:
                print(f"⚠️ Unknown field: {field_name}")
                return

            print(f"🔧 Glue cell setting change: Cell {cell_id}, {section}.{field_name} = {value}")

            # Validate motor address conflicts
            if field_name == "motor_address":
                is_valid, error_msg = self._validate_motor_address(cell_id, value)
                if not is_valid:
                    self._show_toast(error_msg)
                    self._reload_cell_ui(cell_id)
                    return

            # Make API call via controller_service
            result = self.controller_service.settings.update_glue_cell(
                cell_id,
                {section: {field_name: value}}
            )

            if result.success:
                # Update cached config
                self._update_cached_config(cell_id, section, field_name, value)
                print(f"✅ Glue cell setting updated successfully")
            else:
                print(f"❌ Failed to update glue cell setting: {result.message}")
                self._show_toast(f"Error: {result.message}")
                self._reload_cell_ui(cell_id)

        except ValueError as e:
            print(f"❌ Invalid key format: {key} - {e}")
        except Exception as e:
            print(f"❌ Error handling glue cell setting change: {e}")
            import traceback
            traceback.print_exc()

    def _handle_cell_changed(self, cell_id: int):
        """
        Handle cell selection change (CENTRALIZED BUSINESS LOGIC).

        Loads the config from cache (or fetches if not cached) and updates UI.

        Args:
            cell_id: Selected cell ID (1, 2, or 3)
        """
        print(f"🔄 Cell changed to: {cell_id}")

        # Get config from cache
        config = self.glue_cell_configs.get(cell_id)

        if config:
            # Update UI with cached config
            if hasattr(self.content_widget, 'glue_cell_tab'):
                self.content_widget.glue_cell_tab.set_cell_config(config)
        else:
            # Config not in cache - reload all configs
            print(f"⚠️ Cell {cell_id} not in cache, reloading...")
            self._load_glue_cell_configs()

            # Try again
            config = self.glue_cell_configs.get(cell_id)
            if config and hasattr(self.content_widget, 'glue_cell_tab'):
                self.content_widget.glue_cell_tab.set_cell_config(config)

    def _handle_tare_requested(self, cell_id: int):
        """
        Handle tare request (CENTRALIZED BUSINESS LOGIC).

        Makes API call to tare the cell and updates UI with new calibration values.

        Args:
            cell_id: Cell ID to tare
        """
        print(f"🔄 Tare requested for Cell {cell_id}")

        try:
            result = self.controller_service.settings.tare_glue_cell(cell_id)

            if result.success:
                # Get new calibration values from response
                new_offset = result.data.get('new_offset', 0.0)

                # Update cached config
                if cell_id in self.glue_cell_configs:
                    self.glue_cell_configs[cell_id].calibration.zero_offset = new_offset

                    # Update UI if this cell is currently displayed
                    if hasattr(self.content_widget, 'glue_cell_tab'):
                        if self.content_widget.glue_cell_tab.current_cell == cell_id:
                            self.content_widget.glue_cell_tab.set_cell_config(
                                self.glue_cell_configs[cell_id]
                            )

                self._show_toast(f"✅ Cell {cell_id} tared successfully")
                print(f"✅ Cell {cell_id} tared: new offset = {new_offset}")
            else:
                self._show_toast(f"❌ Tare failed: {result.message}")
                print(f"❌ Tare failed: {result.message}")

        except Exception as e:
            print(f"❌ Error during tare operation: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast(f"❌ Error: {str(e)}")

    def _handle_reset_requested(self, cell_id: int):
        """
        Handle reset request (CENTRALIZED BUSINESS LOGIC).

        Resets calibration values to defaults and updates UI.

        Args:
            cell_id: Cell ID to reset
        """
        print(f"🔄 Reset requested for Cell {cell_id}")

        try:
            result = self.controller_service.settings.reset_glue_cell(cell_id)

            if result.success:
                # Get default calibration values from response
                default_calibration = result.data.get('calibration', {})

                # Update cached config
                if cell_id in self.glue_cell_configs:
                    self.glue_cell_configs[cell_id].calibration = CalibrationSettings.from_dict(
                        default_calibration
                    )

                    # Update UI if this cell is currently displayed
                    if hasattr(self.content_widget, 'glue_cell_tab'):
                        if self.content_widget.glue_cell_tab.current_cell == cell_id:
                            self.content_widget.glue_cell_tab.set_cell_config(
                                self.glue_cell_configs[cell_id]
                            )

                self._show_toast(f"✅ Cell {cell_id} reset to defaults")
                print(f"✅ Cell {cell_id} reset to defaults")
            else:
                self._show_toast(f"❌ Reset failed: {result.message}")
                print(f"❌ Reset failed: {result.message}")

        except Exception as e:
            print(f"❌ Error during reset operation: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast(f"❌ Error: {str(e)}")

    def _setup_camera_signals(self):
        """
        Setup signal connections for camera settings (CENTRALIZED PATTERN).

        Connects all signals from CameraSettingsUI to centralized handlers
        in SettingsAppWidget. This implements the DUMB UI / SMART Controller pattern.
        """
        if not hasattr(self.content_widget, 'cameraSettingsTabLayout'):
            print("⚠️ cameraSettingsTabLayout not found, skipping camera signals setup")
            return

        camera_tab = self.content_widget.cameraSettingsTabLayout

        # Connect value change signal (handled by base _handle_setting_change)
        # This is already connected via content_widget.setting_changed

        # Connect camera action signals
        camera_tab.capture_image_requested.connect(self._handle_capture_image)
        camera_tab.start_calibration_requested.connect(self._handle_start_calibration)
        camera_tab.save_calibration_requested.connect(self._handle_save_calibration)
        camera_tab.load_calibration_requested.connect(self._handle_load_calibration)
        camera_tab.test_contour_detection_requested.connect(self._handle_test_contour_detection)
        camera_tab.test_aruco_detection_requested.connect(self._handle_test_aruco_detection)

        # Note: save/load/reset settings are handled in SettingsContent for backward compatibility
        # raw_mode_requested is also handled in SettingsContent

        print("✅ Camera signals connected to SettingsAppWidget")

    # ============================================================================
    # Camera Settings Handlers (Centralized Business Logic)
    # ============================================================================

    def _handle_capture_image(self):
        """
        Handle capture image request (CENTRALIZED BUSINESS LOGIC).

        Captures a frame from the camera and saves it.
        """
        print("🔄 Capture image requested")
        try:
            result = self.controller.handle(camera_endpoints.CAMERA_ACTION_CAPTURE)
            if result.get('status') == 'success':
                self._show_toast(f"✅ Image captured successfully")
                print(f"✅ Image captured: {result.get('message', '')}")
            else:
                self._show_toast(f"❌ Capture failed: {result.get('message', 'Unknown error')}")
                print(f"❌ Capture failed: {result.get('message', '')}")
        except Exception as e:
            print(f"❌ Error during capture: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast(f"❌ Error: {str(e)}")

    def _handle_start_calibration(self):
        """
        Handle start calibration request (CENTRALIZED BUSINESS LOGIC).

        Starts camera calibration process.
        """
        print("🔄 Start calibration requested")
        try:
            result = self.controller.handle(camera_endpoints.CAMERA_ACTION_START_CALIBRATION)
            if result.get('status') == 'success':
                self._show_toast(f"✅ Calibration started")
                print(f"✅ Calibration started: {result.get('message', '')}")
            else:
                self._show_toast(f"❌ Failed to start calibration: {result.get('message', 'Unknown error')}")
                print(f"❌ Failed to start calibration: {result.get('message', '')}")
        except Exception as e:
            print(f"❌ Error starting calibration: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast(f"❌ Error: {str(e)}")

    def _handle_save_calibration(self):
        """
        Handle save calibration request (CENTRALIZED BUSINESS LOGIC).

        Saves current camera calibration data.
        """
        print("🔄 Save calibration requested")
        try:
            result = self.controller.handle(camera_endpoints.CAMERA_ACTION_SAVE_CALIBRATION)
            if result.get('status') == 'success':
                self._show_toast(f"✅ Calibration saved successfully")
                print(f"✅ Calibration saved: {result.get('message', '')}")
            else:
                self._show_toast(f"❌ Failed to save calibration: {result.get('message', 'Unknown error')}")
                print(f"❌ Failed to save calibration: {result.get('message', '')}")
        except Exception as e:
            print(f"❌ Error saving calibration: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast(f"❌ Error: {str(e)}")

    def _handle_load_calibration(self):
        """
        Handle load calibration request (CENTRALIZED BUSINESS LOGIC).

        Loads saved camera calibration data.
        """
        print("🔄 Load calibration requested")
        try:
            result = self.controller.handle(camera_endpoints.CAMERA_ACTION_LOAD_CALIBRATION)
            if result.get('status') == 'success':
                self._show_toast(f"✅ Calibration loaded successfully")
                print(f"✅ Calibration loaded: {result.get('message', '')}")
            else:
                self._show_toast(f"❌ Failed to load calibration: {result.get('message', 'Unknown error')}")
                print(f"❌ Failed to load calibration: {result.get('message', '')}")
        except Exception as e:
            print(f"❌ Error loading calibration: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast(f"❌ Error: {str(e)}")

    def _handle_test_contour_detection(self):
        """
        Handle test contour detection request (CENTRALIZED BUSINESS LOGIC).

        Tests contour detection with current settings.
        """
        print("🔄 Test contour detection requested")
        try:
            result = self.controller.handle(camera_endpoints.CAMERA_ACTION_TEST_CONTOUR)
            if result.get('status') == 'success':
                self._show_toast(f"✅ Contour detection test completed")
                print(f"✅ Contour test completed: {result.get('message', '')}")
            else:
                self._show_toast(f"❌ Contour test failed: {result.get('message', 'Unknown error')}")
                print(f"❌ Contour test failed: {result.get('message', '')}")
        except Exception as e:
            print(f"❌ Error testing contour detection: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast(f"❌ Error: {str(e)}")

    def _handle_test_aruco_detection(self):
        """
        Handle test ArUco detection request (CENTRALIZED BUSINESS LOGIC).

        Tests ArUco marker detection with current settings.
        """
        print("🔄 Test ArUco detection requested")
        try:
            result = self.controller.handle(camera_endpoints.CAMERA_ACTION_TEST_ARUCO)
            if result.get('status') == 'success':
                self._show_toast(f"✅ ArUco detection test completed")
                print(f"✅ ArUco test completed: {result.get('message', '')}")
            else:
                self._show_toast(f"❌ ArUco test failed: {result.get('message', 'Unknown error')}")
                print(f"❌ ArUco test failed: {result.get('message', '')}")
        except Exception as e:
            print(f"❌ Error testing ArUco detection: {e}")
            import traceback
            traceback.print_exc()
            self._show_toast(f"❌ Error: {str(e)}")

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _validate_motor_address(self, cell_id: int, new_address: int) -> Tuple[bool, str]:
        """
        Validate motor address for conflicts with other cells.

        Args:
            cell_id: Cell ID being updated
            new_address: New motor address

        Returns:
            Tuple of (is_valid, error_message)
        """
        for cid, config in self.glue_cell_configs.items():
            if cid != cell_id and config.connection.motor_address == new_address:
                return False, f"⚠️ Motor address {new_address} already used by Cell {cid}"

        return True, ""

    def _update_cached_config(self, cell_id: int, section: str, field_name: str, value):
        """
        Update cached config after successful API call.

        Args:
            cell_id: Cell ID
            section: Section name (connection/calibration/measurement)
            field_name: Field name
            value: New value
        """
        if cell_id not in self.glue_cell_configs:
            return

        config = self.glue_cell_configs[cell_id]

        # Update the appropriate section
        if section == "connection":
            setattr(config.connection, field_name, value)
        elif section == "calibration":
            setattr(config.calibration, field_name, value)
        elif section == "measurement":
            setattr(config.measurement, field_name, value)

    def _reload_cell_ui(self, cell_id: int):
        """
        Reload UI for a specific cell (used after validation failure).

        Args:
            cell_id: Cell ID to reload
        """
        if cell_id in self.glue_cell_configs:
            if hasattr(self.content_widget, 'glue_cell_tab'):
                if self.content_widget.glue_cell_tab.current_cell == cell_id:
                    self.content_widget.glue_cell_tab.set_cell_config(
                        self.glue_cell_configs[cell_id]
                    )

    def _show_toast(self, message: str):
        """
        Show a toast notification to the user.

        Args:
            message: Message to display
        """
        # TODO: Implement proper toast notification
        # For now, just use QMessageBox
        from PyQt6.QtWidgets import QMessageBox

        if message.startswith("✅"):
            QMessageBox.information(self, "Success", message)
        elif message.startswith("⚠️") or message.startswith("❌"):
            QMessageBox.warning(self, "Warning", message)
        else:
            QMessageBox.information(self, "Info", message)

    def clean_up(self):
        """Clean up resources when the widget is destroyed"""
        if hasattr(self, 'content_widget') and self.content_widget:
            self.content_widget.clean_up()