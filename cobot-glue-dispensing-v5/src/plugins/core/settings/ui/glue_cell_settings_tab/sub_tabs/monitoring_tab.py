"""
Monitoring tab - displays real-time weight and diagnostics.

DUMB component - only displays data, no business logic.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from plugins.core.settings.ui.glue_cell_settings_tab.groups.monitoring_display import MonitoringDisplayGroup


class MonitoringTab(QWidget):
    """
    Monitoring tab - DUMB UI component.

    Displays real-time monitoring data.
    Does NOT subscribe to MessageBroker - parent handles that.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        """Build the UI layout"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # Monitoring display group
        self.monitoring_group = MonitoringDisplayGroup()
        layout.addWidget(self.monitoring_group)

        # Future: Could add more diagnostic groups here
        # - Connection diagnostics
        # - Historical weight chart
        # - Error log display
        # - Cell health indicators

        layout.addStretch()
        self.setLayout(layout)

    def set_weight(self, weight: float | None, is_connected: bool = True):
        """
        Update the weight display.

        Args:
            weight: Current weight value
            is_connected: Whether cell is connected
        """
        self.monitoring_group.set_weight(weight, is_connected)

    def set_thresholds(self, min_threshold: float, max_threshold: float):
        """
        Update thresholds for weight styling.

        Args:
            min_threshold: Minimum acceptable weight
            max_threshold: Maximum acceptable weight
        """
        self.monitoring_group.set_thresholds(min_threshold, max_threshold)

    def update_from_config(self, min_threshold: float, max_threshold: float):
        """
        Update monitoring display from configuration.

        Args:
            min_threshold: Min weight threshold from MeasurementSettings
            max_threshold: Max weight threshold from MeasurementSettings
        """
        self.set_thresholds(min_threshold, max_threshold)
