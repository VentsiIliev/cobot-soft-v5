"""
Configuration tab - composes connection, calibration, and measurement groups.

DUMB component - only forwards signals, no business logic.
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from plugins.core.settings.ui.glue_cell_settings_tab.groups.connection_settings import ConnectionSettingsGroup
from plugins.core.settings.ui.glue_cell_settings_tab.groups.calibration_settings import CalibrationSettingsGroup
from plugins.core.settings.ui.glue_cell_settings_tab.groups.measurement_settings import MeasurementSettingsGroup
from plugins.core.settings.ui.glue_cell_settings_tab.models.cell_config import CellConfig


class ConfigurationTab(QWidget):
    """
    Configuration tab - DUMB UI component.

    Composes connection, calibration, and measurement groups.
    Forwards all signals upward with proper namespacing (e.g., "calibration.zero_offset").
    """

    # Unified signal for any configuration change (namespaced)
    config_changed_signal = pyqtSignal(str, object)  # "section.field", value

    # Forward tare and reset requests
    tare_requested_signal = pyqtSignal()
    reset_requested_signal = pyqtSignal()

    def __init__(self, available_glue_types: list = None, parent=None):
        """
        Initialize configuration tab.

        Args:
            available_glue_types: List of glue type names (from parent/SettingsAppWidget)
            parent: Parent widget
        """
        super().__init__(parent)
        self.available_glue_types = available_glue_types or []
        self.build_ui()

    def build_ui(self):
        """Build the UI layout"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # Connection settings (full width at top)
        self.connection_group = ConnectionSettingsGroup(self.available_glue_types)
        self.connection_group.connection_changed_signal.connect(
            lambda field, val: self.config_changed_signal.emit(f"connection.{field}", val)
        )
        layout.addWidget(self.connection_group)

        # Calibration + Measurement (side-by-side)
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)

        self.calibration_group = CalibrationSettingsGroup()
        self.calibration_group.calibration_changed_signal.connect(
            lambda field, val: self.config_changed_signal.emit(f"calibration.{field}", val)
        )
        self.calibration_group.tare_requested_signal.connect(self.tare_requested_signal.emit)
        self.calibration_group.reset_requested_signal.connect(self.reset_requested_signal.emit)
        row_layout.addWidget(self.calibration_group)

        self.measurement_group = MeasurementSettingsGroup()
        self.measurement_group.measurement_changed_signal.connect(
            lambda field, val: self.config_changed_signal.emit(f"measurement.{field}", val)
        )
        row_layout.addWidget(self.measurement_group)

        layout.addLayout(row_layout)
        layout.addStretch()

        self.setLayout(layout)

    def get_settings(self, cell_id: int) -> CellConfig:
        """
        Get complete cell configuration from all groups.

        Args:
            cell_id: Cell ID to include in the config

        Returns:
            CellConfig dataclass
        """
        return CellConfig(
            cell_id=cell_id,
            connection=self.connection_group.get_settings(),
            calibration=self.calibration_group.get_settings(),
            measurement=self.measurement_group.get_settings()
        )

    def update_values(self, config: CellConfig):
        """
        Update all groups from CellConfig dataclass.

        Args:
            config: CellConfig dataclass
        """
        self.connection_group.update_values(config.connection)
        self.calibration_group.update_values(config.calibration)
        self.measurement_group.update_values(config.measurement)

        # Also update thresholds in monitoring (if needed elsewhere)
        # This is called from the ConfigurationTab when measurement settings change

    def set_available_glue_types(self, glue_types: list):
        """
        Update available glue types in connection group.

        Args:
            glue_types: List of glue type names
        """
        self.connection_group.set_available_glue_types(glue_types)

    def set_buttons_enabled(self, enabled: bool):
        """
        Enable or disable control buttons (tare, reset).

        Args:
            enabled: True to enable, False to disable
        """
        self.calibration_group.set_buttons_enabled(enabled)
