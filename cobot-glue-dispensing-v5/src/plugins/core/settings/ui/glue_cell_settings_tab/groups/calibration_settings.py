"""
Calibration settings group - offset and scale configuration with tare button.

DUMB component - only emits signals, no business logic or API calls.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QLabel, QVBoxLayout

from plugins.core.settings.ui.glue_cell_settings_tab.groups.base import GlueCellSettingGroupBox
from plugins.core.settings.ui.glue_cell_settings_tab.models.cell_config import CalibrationSettings
from frontend.widgets.MaterialButton import MaterialButton


class CalibrationSettingsGroup(GlueCellSettingGroupBox):
    """
    Calibration settings group - DUMB UI component.

    Emits signals for field changes and tare requests.
    Parent is responsible for:
    - Making API calls to update calibration
    - Handling tare operation
    - Updating UI with new values after tare
    """

    # Signal emitted when any calibration field changes
    calibration_changed_signal = pyqtSignal(str, object)  # field_name, value

    # Signal emitted when user clicks tare button
    tare_requested_signal = pyqtSignal()

    # Signal emitted when user clicks reset button
    reset_requested_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Calibration Settings", parent)
        self.build_ui()

    def build_ui(self):
        """Build the UI layout"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 25, 20, 20)

        # Settings grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        row = 0

        # Zero Offset
        label = QLabel("Zero Offset:")
        label.setWordWrap(True)
        grid_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.zero_offset_input = self.create_double_spinbox(
            -100000000.0, 100000000.0, 0.0, " g", decimals=2
        )
        self.zero_offset_input.valueChanged.connect(
            lambda val: self.calibration_changed_signal.emit("zero_offset", val)
        )
        grid_layout.addWidget(self.zero_offset_input, row, 1)
        row += 1

        # Scale Factor
        label = QLabel("Scale Factor:")
        label.setWordWrap(True)
        grid_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.scale_factor_input = self.create_double_spinbox(
            0.001, 1000.0, 1.0, " units", decimals=3
        )
        self.scale_factor_input.valueChanged.connect(
            lambda val: self.calibration_changed_signal.emit("scale_factor", val)
        )
        grid_layout.addWidget(self.scale_factor_input, row, 1)

        grid_layout.setColumnStretch(1, 1)
        main_layout.addLayout(grid_layout)

        # Control buttons
        self.tare_button = MaterialButton("Tare (Zero)")
        self.tare_button.setMinimumHeight(35)
        self.tare_button.clicked.connect(self.tare_requested_signal.emit)
        main_layout.addWidget(self.tare_button)

        self.reset_button = MaterialButton("Reset to Defaults")
        self.reset_button.setMinimumHeight(35)
        self.reset_button.clicked.connect(self.reset_requested_signal.emit)
        main_layout.addWidget(self.reset_button)

        self.setLayout(main_layout)

    def get_settings(self) -> CalibrationSettings:
        """
        Get current calibration settings from UI widgets.

        Returns:
            CalibrationSettings dataclass
        """
        return CalibrationSettings(
            zero_offset=self.zero_offset_input.value(),
            scale_factor=self.scale_factor_input.value(),
            temperature_compensation=False  # Not implemented in UI yet
        )

    def update_values(self, settings: CalibrationSettings):
        """
        Update UI widgets from CalibrationSettings dataclass.

        Blocks signals during update to prevent triggering change events.

        Args:
            settings: CalibrationSettings dataclass
        """
        # Block signals
        self.zero_offset_input.blockSignals(True)
        self.scale_factor_input.blockSignals(True)

        try:
            self.zero_offset_input.setValue(settings.zero_offset)
            self.scale_factor_input.setValue(settings.scale_factor)
        finally:
            # Always unblock signals
            self.zero_offset_input.blockSignals(False)
            self.scale_factor_input.blockSignals(False)

    def set_buttons_enabled(self, enabled: bool):
        """
        Enable or disable control buttons.

        Args:
            enabled: True to enable buttons, False to disable
        """
        self.tare_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
