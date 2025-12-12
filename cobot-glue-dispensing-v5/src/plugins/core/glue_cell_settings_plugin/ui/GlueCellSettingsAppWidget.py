from typing import Dict, Tuple

from frontend.core.shared.base_widgets.AppWidget import AppWidget
from plugins.core.settings.ui.glue_cell_settings_tab.GlueCellSettingsUI import GlueCellSettingsUI
from plugins.core.settings.ui.glue_cell_settings_tab.models.cell_config import (
    CellConfig, ConnectionSettings, CalibrationSettings, MeasurementSettings
)
from plugins.core.settings.ui.glue_cell_settings_tab.utils.validators import (
    parse_glue_cell_key, get_field_section_mapping
)
from PyQt6.QtWidgets import QWidget

# Using the new modular GlueCellSettingsUI (v2.0 refactored architecture)

class GlueCellSettingsAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None, controller=None, controller_service=None):
        self.controller = controller
        self.controller_service = controller_service
        self.parent = parent

        # Cache for glue cell configurations (centralized data access)
        self.glue_cell_configs: Dict[int, CellConfig] = {}

        super().__init__("Glue Cell Settings", parent)
        print("GlueCellSettingsAppWidget initialized with parent:", self.parent)

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
            # Load glue types
            glue_type_names = []
            try:
                result = self.controller_service.settings.get_glue_types()
                if result.success and result.data:
                    glue_type_names = [gt.get("name") for gt in result.data if gt.get("name")]
                    print(f"[GlueCellSettingsAppWidget] Loaded {len(glue_type_names)} glue types")
            except Exception as e:
                print(f"[GlueCellSettingsAppWidget] Error loading glue types: {e}")

            try:
                # Create NEW modular glue cell settings UI (v2.0 refactored architecture)
                # This is the DUMB UI component - all business logic is handled below
                self.content_widget = QWidget(self.parent)

                # Initialize the new GlueCellSettingsUI (DUMB component)
                self.content_layout = GlueCellSettingsUI(
                    parent_widget=self.content_widget,
                    available_glue_types=glue_type_names
                )

                # Connect signals to centralized business logic handlers
                self.content_layout.value_changed_signal.connect(self._handle_glue_cell_setting_change)
                self.content_layout.cell_changed_signal.connect(self._handle_cell_changed)
                self.content_layout.tare_requested_signal.connect(self._handle_tare_requested)
                self.content_layout.reset_requested_signal.connect(self._handle_reset_requested)

                self.content_widget.setLayout(self.content_layout)

                print("[GlueCellSettingsAppWidget] ✅ Connected glue cell signals to business logic handlers")

                # Load all cell configurations (centralized data access)
                self._load_glue_cell_configs()

                # Initialize UI with first cell's config
                if self.glue_cell_configs:
                    first_cell_id = min(self.glue_cell_configs.keys())
                    self.content_layout.set_cell_config(self.glue_cell_configs[first_cell_id])
                    print(f"[GlueCellSettingsAppWidget] ✅ Initialized UI with Cell {first_cell_id}")

            except Exception as e:
                import traceback
                traceback.print_exc()
                # If content widget creation fails, we cannot proceed
                raise e

            # content_widget.show()
            print("GlueCellSettingsUI loaded successfully")
            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            # Keep the placeholder if the UserManagementWidget is not available
            print("GlueCellSettingsUI not available, using placeholder")

    # ============================================================================
    # Glue Cell Settings Handlers (Centralized Business Logic)
    # ============================================================================

    def _load_glue_cell_configs(self):
        """Load all glue cell configurations via controller_service."""
        try:
            result = self.controller_service.settings.get_glue_cells_config()

            if result.success:
                cells_data = result.data.get('cells', [])

                for cell_dto in cells_data:
                    cell_id = cell_dto.get('id')
                    if cell_id:
                        self.glue_cell_configs[cell_id] = CellConfig.from_dto(cell_dto)

                print(f"✅ Loaded {len(self.glue_cell_configs)} glue cell configurations")
            else:
                print(f"❌ Failed to load glue cell configs: {result.message}")
        except Exception as e:
            print(f"❌ Error loading glue cell configs: {e}")
            import traceback
            traceback.print_exc()

    def _handle_glue_cell_setting_change(self, key: str, value, className: str):
        """Handle ALL glue cell setting changes (CENTRALIZED BUSINESS LOGIC)."""
        if not key.startswith("load_cell_"):
            return

        try:
            cell_id, field_name = parse_glue_cell_key(key)
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
        """Handle cell selection change."""
        print(f"🔄 Cell changed to: {cell_id}")

        config = self.glue_cell_configs.get(cell_id)

        if config:
            self.content_layout.set_cell_config(config)
        else:
            print(f"⚠️ Cell {cell_id} not in cache, reloading...")
            self._load_glue_cell_configs()

            config = self.glue_cell_configs.get(cell_id)
            if config:
                self.content_layout.set_cell_config(config)

    def _handle_tare_requested(self, cell_id: int):
        """Handle tare request."""
        print(f"🔄 Tare requested for Cell {cell_id}")

        try:
            result = self.controller_service.settings.tare_glue_cell(cell_id)

            if result.success:
                new_offset = result.data.get('new_offset', 0.0)

                if cell_id in self.glue_cell_configs:
                    self.glue_cell_configs[cell_id].calibration.zero_offset = new_offset

                    if self.content_layout.current_cell == cell_id:
                        self.content_layout.set_cell_config(self.glue_cell_configs[cell_id])

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
        """Handle reset request."""
        print(f"🔄 Reset requested for Cell {cell_id}")

        try:
            result = self.controller_service.settings.reset_glue_cell(cell_id)

            if result.success:
                default_calibration = result.data.get('calibration', {})

                if cell_id in self.glue_cell_configs:
                    self.glue_cell_configs[cell_id].calibration = CalibrationSettings.from_dict(
                        default_calibration
                    )

                    if self.content_layout.current_cell == cell_id:
                        self.content_layout.set_cell_config(self.glue_cell_configs[cell_id])

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

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _validate_motor_address(self, cell_id: int, new_address: int) -> Tuple[bool, str]:
        """Validate motor address for conflicts with other cells."""
        for cid, config in self.glue_cell_configs.items():
            if cid != cell_id and config.connection.motor_address == new_address:
                return False, f"⚠️ Motor address {new_address} already used by Cell {cid}"

        return True, ""

    def _update_cached_config(self, cell_id: int, section: str, field_name: str, value):
        """Update cached config after successful API call."""
        if cell_id not in self.glue_cell_configs:
            return

        config = self.glue_cell_configs[cell_id]

        if section == "connection":
            setattr(config.connection, field_name, value)
        elif section == "calibration":
            setattr(config.calibration, field_name, value)
        elif section == "measurement":
            setattr(config.measurement, field_name, value)

    def _reload_cell_ui(self, cell_id: int):
        """Reload UI for a specific cell (used after validation failure)."""
        if cell_id in self.glue_cell_configs:
            if self.content_layout.current_cell == cell_id:
                self.content_layout.set_cell_config(self.glue_cell_configs[cell_id])

    def _show_toast(self, message: str):
        """Show a toast notification to the user."""
        from PyQt6.QtWidgets import QMessageBox

        if message.startswith("✅"):
            QMessageBox.information(self, "Success", message)
        elif message.startswith("⚠️") or message.startswith("❌"):
            QMessageBox.warning(self, "Warning", message)
        else:
            QMessageBox.information(self, "Info", message)

    def clean_up(self):
        """Clean up resources when the widget is closed"""
        print("Cleaning up GlueCellSettingsAppWidget")
        try:
            if hasattr(self, 'content_layout') and self.content_layout:
                # CRITICAL: Call the cleanup method on the GlueCellSettingsUI
                # to unsubscribe from MessageBroker
                if hasattr(self.content_layout, 'cleanup'):
                    self.content_layout.cleanup()
                    print("[GlueCellSettingsAppWidget] ✅ Cleaned up MessageBroker subscriptions")
        except Exception as e:
            print(f"Error during GlueCellSettingsAppWidget cleanup: {e}")
        super().clean_up() if hasattr(super(), 'clean_up') else None
