"""
Measurement settings group - sampling and filtering configuration.

DUMB component - only emits signals, no business logic or API calls.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QLabel

from plugins.core.settings.ui.glue_cell_settings_tab.groups.base import GlueCellSettingGroupBox
from plugins.core.settings.ui.glue_cell_settings_tab.models.cell_config import MeasurementSettings


class MeasurementSettingsGroup(GlueCellSettingGroupBox):
    """
    Measurement settings group - DUMB UI component.

    Emits signals for all field changes.
    Parent is responsible for saving changes to backend.
    """

    # Signal emitted when any measurement field changes
    measurement_changed_signal = pyqtSignal(str, object)  # field_name, value

    def __init__(self, parent=None):
        super().__init__("Measurement Settings", parent)
        self.build_ui()

    def build_ui(self):
        """Build the UI layout"""
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Sampling Rate
        label = QLabel("Sampling Rate:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.sampling_rate_input = self.create_spinbox(1, 1000, 10, " Hz")
        self.sampling_rate_input.valueChanged.connect(
            lambda val: self.measurement_changed_signal.emit("sampling_rate", val)
        )
        layout.addWidget(self.sampling_rate_input, row, 1)
        row += 1

        # Filter Cutoff Frequency
        label = QLabel("Filter Cutoff:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.filter_cutoff_input = self.create_double_spinbox(0.1, 100.0, 5.0, " Hz")
        self.filter_cutoff_input.valueChanged.connect(
            lambda val: self.measurement_changed_signal.emit("filter_cutoff", val)
        )
        layout.addWidget(self.filter_cutoff_input, row, 1)
        row += 1

        # Averaging Samples
        label = QLabel("Averaging Samples:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.averaging_samples_input = self.create_spinbox(1, 100, 5, " samples")
        self.averaging_samples_input.valueChanged.connect(
            lambda val: self.measurement_changed_signal.emit("averaging_samples", val)
        )
        layout.addWidget(self.averaging_samples_input, row, 1)
        row += 1

        # Min Weight Threshold
        label = QLabel("Min Weight Threshold:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.min_weight_threshold_input = self.create_double_spinbox(0.0, 100.0, 0.1, " g")
        self.min_weight_threshold_input.valueChanged.connect(
            lambda val: self.measurement_changed_signal.emit("min_weight_threshold", val)
        )
        layout.addWidget(self.min_weight_threshold_input, row, 1)
        row += 1

        # Max Weight Threshold
        label = QLabel("Max Weight Threshold:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.max_weight_threshold_input = self.create_double_spinbox(0.0, 50000.0, 1000.0, " g")
        self.max_weight_threshold_input.valueChanged.connect(
            lambda val: self.measurement_changed_signal.emit("max_weight_threshold", val)
        )
        layout.addWidget(self.max_weight_threshold_input, row, 1)

        layout.setColumnStretch(1, 1)
        self.setLayout(layout)

    def get_settings(self) -> MeasurementSettings:
        """
        Get current measurement settings from UI widgets.

        Returns:
            MeasurementSettings dataclass
        """
        return MeasurementSettings(
            sampling_rate=self.sampling_rate_input.value(),
            filter_cutoff=self.filter_cutoff_input.value(),
            averaging_samples=self.averaging_samples_input.value(),
            min_weight_threshold=self.min_weight_threshold_input.value(),
            max_weight_threshold=self.max_weight_threshold_input.value()
        )

    def update_values(self, settings: MeasurementSettings):
        """
        Update UI widgets from MeasurementSettings dataclass.

        Blocks signals during update to prevent triggering change events.

        Args:
            settings: MeasurementSettings dataclass
        """
        # Block all signals
        self.sampling_rate_input.blockSignals(True)
        self.filter_cutoff_input.blockSignals(True)
        self.averaging_samples_input.blockSignals(True)
        self.min_weight_threshold_input.blockSignals(True)
        self.max_weight_threshold_input.blockSignals(True)

        try:
            self.sampling_rate_input.setValue(settings.sampling_rate)
            self.filter_cutoff_input.setValue(settings.filter_cutoff)
            self.averaging_samples_input.setValue(settings.averaging_samples)
            self.min_weight_threshold_input.setValue(settings.min_weight_threshold)
            self.max_weight_threshold_input.setValue(settings.max_weight_threshold)
        finally:
            # Always unblock signals
            self.sampling_rate_input.blockSignals(False)
            self.filter_cutoff_input.blockSignals(False)
            self.averaging_samples_input.blockSignals(False)
            self.min_weight_threshold_input.blockSignals(False)
            self.max_weight_threshold_input.blockSignals(False)
