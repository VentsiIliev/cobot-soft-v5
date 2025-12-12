"""
Monitoring display group - real-time weight display.

DUMB component - only displays data, no business logic.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QLabel

from plugins.core.settings.ui.glue_cell_settings_tab.groups.base import GlueCellSettingGroupBox
from plugins.core.settings.ui.glue_cell_settings_tab.utils.styling import get_weight_style, WEIGHT_STYLE_DISCONNECTED
from plugins.core.settings.ui.glue_cell_settings_tab.utils.validators import format_weight_display


class MonitoringDisplayGroup(GlueCellSettingGroupBox):
    """
    Monitoring display group - DUMB UI component.

    Only displays weight data received from parent.
    Does NOT subscribe to MessageBroker or fetch data.
    """

    def __init__(self, parent=None):
        super().__init__("Real-time Monitoring", parent)
        self.min_threshold = 0.1
        self.max_threshold = 1000.0
        self.build_ui()

    def build_ui(self):
        """Build the UI layout"""
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        # Current Weight Display
        row = 0
        label = QLabel("Current Weight:")
        label.setWordWrap(True)
        label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; }")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.current_weight_label = QLabel("-- g")
        self.current_weight_label.setStyleSheet(WEIGHT_STYLE_DISCONNECTED)
        layout.addWidget(self.current_weight_label, row, 1)

        layout.setColumnStretch(1, 1)
        self.setLayout(layout)

    def set_weight(self, weight: float | None, is_connected: bool = True):
        """
        Update the weight display.

        Args:
            weight: Current weight value (or None if unavailable)
            is_connected: Whether the cell is connected
        """
        # Update text
        display_text = format_weight_display(weight, is_connected)
        self.current_weight_label.setText(display_text)

        # Update styling
        if weight is not None and is_connected:
            style = get_weight_style(weight, self.min_threshold, self.max_threshold, is_connected)
        else:
            style = WEIGHT_STYLE_DISCONNECTED

        self.current_weight_label.setStyleSheet(style)

    def set_thresholds(self, min_threshold: float, max_threshold: float):
        """
        Update the thresholds for weight styling.

        Args:
            min_threshold: Minimum acceptable weight
            max_threshold: Maximum acceptable weight
        """
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
