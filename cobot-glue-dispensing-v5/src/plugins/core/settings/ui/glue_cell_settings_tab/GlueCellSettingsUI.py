"""
Main glue cell settings UI widget - tab-based organization.

DUMB component - only emits signals and displays data, no business logic.
All controller_service calls happen in SettingsAppWidget.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QTabWidget, QScrollArea, QWidget

from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout
from plugins.core.settings.ui.glue_cell_settings_tab.groups.cell_selector import CellSelectorGroup
from plugins.core.settings.ui.glue_cell_settings_tab.sub_tabs.configuration_tab import ConfigurationTab
from plugins.core.settings.ui.glue_cell_settings_tab.sub_tabs.monitoring_tab import MonitoringTab
from plugins.core.settings.ui.glue_cell_settings_tab.models.cell_config import CellConfig
from plugins.core.settings.ui.glue_cell_settings_tab.utils.validators import parse_glue_cell_key, get_field_section_mapping

from modules.shared.MessageBroker import MessageBroker
from communication_layer.api.v1.topics import GlueCellTopics


class GlueCellSettingsUI(BaseSettingsTabLayout, QVBoxLayout):
    """
    Main glue cell settings widget - DUMB UI component.

    Provides tab-based organization with:
    - Cell selector (always visible at top)
    - Configuration tab (connection, calibration, measurement)
    - Monitoring tab (real-time weight display)

    All signals propagate upward to SettingsAppWidget, which handles business logic.
    NO controller_service usage here - this is pure presentation.
    """

    # CRITICAL: Backward compatibility signal
    value_changed_signal = pyqtSignal(str, object, str)  # key, value, className

    # New signals for cleaner architecture
    cell_changed_signal = pyqtSignal(int)  # cell_id
    tare_requested_signal = pyqtSignal(int)  # cell_id
    reset_requested_signal = pyqtSignal(int)  # cell_id

    def __init__(self, parent_widget=None, available_glue_types: list = None):
        """
        Initialize GlueCellSettingsUI.

        Args:
            parent_widget: Parent widget
            available_glue_types: List of glue type names (loaded by SettingsAppWidget)
        """
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)

        self.parent_widget = parent_widget
        self.current_cell = 1
        self.available_glue_types = available_glue_types or []

        # MessageBroker for weight updates (UI responsibility)
        self.broker = MessageBroker()
        self.weight_subscriptions = []

        # Create UI
        self.create_main_content()

        # Subscribe to weight updates
        self._subscribe_to_weights()

    def create_main_content(self):
        """Create the main UI layout"""
        self.setContentsMargins(0, 0, 0, 0)

        # Cell selector at top (always visible)
        self.cell_selector = CellSelectorGroup()
        self.cell_selector.cell_changed_signal.connect(self._on_cell_changed)
        self.addWidget(self.cell_selector)

        # Tab widget for configuration and monitoring
        self.tab_widget = QTabWidget()

        # Configuration tab (scrollable)
        config_scroll = self._create_scrollable_tab()
        self.config_tab = ConfigurationTab(self.available_glue_types)
        self.config_tab.config_changed_signal.connect(self._on_config_changed)
        self.config_tab.tare_requested_signal.connect(self._on_tare_requested)
        self.config_tab.reset_requested_signal.connect(self._on_reset_requested)
        config_scroll.setWidget(self.config_tab)
        self.tab_widget.addTab(config_scroll, "Configuration")

        # Monitoring tab (scrollable)
        monitor_scroll = self._create_scrollable_tab()
        self.monitoring_tab = MonitoringTab()
        monitor_scroll.setWidget(self.monitoring_tab)
        self.tab_widget.addTab(monitor_scroll, "Monitoring & Diagnostics")

        self.addWidget(self.tab_widget)

    def _create_scrollable_tab(self) -> QScrollArea:
        """
        Create a scroll area for tab content.

        Returns:
            QScrollArea configured for tab content
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        return scroll

    def _subscribe_to_weights(self):
        """Subscribe to MessageBroker for weight updates"""
        for cell_id in [1, 2, 3]:
            topic = GlueCellTopics.cell_weight(cell_id)
            # Use lambda with default argument to capture cell_id
            callback = lambda weight, cid=cell_id: self._on_weight_updated(cid, weight)
            self.broker.subscribe(topic, callback)
            self.weight_subscriptions.append((topic, callback))

    def _on_cell_changed(self, cell_id: int):
        """
        Handle cell selection change (DUMB - just emit signal).

        Args:
            cell_id: Selected cell ID (1, 2, or 3)
        """
        self.current_cell = cell_id
        self.cell_changed_signal.emit(cell_id)

    def _on_config_changed(self, field_path: str, value):
        """
        Handle configuration change from sub-tabs.

        Translates modern signal format to legacy format for backward compatibility.

        Args:
            field_path: Modern format "section.field" (e.g., "calibration.zero_offset")
            value: New value
        """
        try:
            section, field = field_path.split(".")
        except ValueError:
            print(f"Invalid field_path format: {field_path}")
            return

        # Emit backward compatibility signal
        # Format: "load_cell_1_zero_offset"
        legacy_key = f"load_cell_{self.current_cell}_{field}"
        self.value_changed_signal.emit(legacy_key, value, "GlueCellSettingsUI")

    def _on_tare_requested(self):
        """Handle tare request (DUMB - just emit with current cell)"""
        self.tare_requested_signal.emit(self.current_cell)

    def _on_reset_requested(self):
        """Handle reset request (DUMB - just emit with current cell)"""
        self.reset_requested_signal.emit(self.current_cell)

    def _on_weight_updated(self, cell_id: int, weight: float):
        """
        Handle weight update from MessageBroker.

        Args:
            cell_id: Cell ID that was updated
            weight: New weight value
        """
        # Only update if this is the currently displayed cell
        if cell_id == self.current_cell:
            self.monitoring_tab.set_weight(weight, is_connected=True)

    def set_cell_config(self, config: CellConfig):
        """
        Update UI with cell configuration (called from SettingsAppWidget).

        Args:
            config: CellConfig dataclass with all settings
        """
        # Update configuration tab
        self.config_tab.update_values(config)

        # Update monitoring tab thresholds
        self.monitoring_tab.update_from_config(
            config.measurement.min_weight_threshold,
            config.measurement.max_weight_threshold
        )

        # Update cell selector label
        self.cell_selector.update_cell_label(
            config.cell_id,
            config.connection.glue_type,
            config.connection.motor_address
        )

        # Update cell selector status (would come from parent in real implementation)
        self.cell_selector.set_status("connected")

    def set_cell_status(self, cell_id: int, status: str):
        """
        Update cell status display (called from SettingsAppWidget).

        Args:
            cell_id: Cell ID
            status: Status string
        """
        if cell_id == self.current_cell:
            self.cell_selector.set_status(status)

    def set_weight(self, weight: float | None, is_connected: bool = True):
        """
        Update weight display (called from SettingsAppWidget or MessageBroker).

        Args:
            weight: Current weight
            is_connected: Whether cell is connected
        """
        self.monitoring_tab.set_weight(weight, is_connected)

    def set_available_glue_types(self, glue_types: list):
        """
        Update available glue types (called from SettingsAppWidget).

        Args:
            glue_types: List of glue type names
        """
        self.available_glue_types = glue_types
        self.config_tab.set_available_glue_types(glue_types)

    def cleanup(self):
        """
        Cleanup resources - CRITICAL for MessageBroker.

        MUST be called by parent widget before destruction.
        """
        # Unsubscribe from all MessageBroker topics
        for topic, callback in self.weight_subscriptions:
            try:
                self.broker.unsubscribe(topic, callback)
            except Exception as e:
                print(f"Error unsubscribing from {topic}: {e}")

        self.weight_subscriptions.clear()
        print(f"[GlueCellSettingsUI] Cleanup complete - unsubscribed from {len(self.weight_subscriptions)} topics")

    def getValues(self):
        """
        Get current values (backward compatibility with old interface).

        Returns:
            Dict with current settings
        """
        config = self.config_tab.get_settings(self.current_cell)

        return {
            f"load_cell_{self.current_cell}_zero_offset": config.calibration.zero_offset,
            f"load_cell_{self.current_cell}_scale_factor": config.calibration.scale_factor,
            f"load_cell_{self.current_cell}_sampling_rate": config.measurement.sampling_rate,
            f"load_cell_{self.current_cell}_filter_cutoff": config.measurement.filter_cutoff,
            f"load_cell_{self.current_cell}_averaging_samples": config.measurement.averaging_samples,
            f"load_cell_{self.current_cell}_min_weight_threshold": config.measurement.min_weight_threshold,
            f"load_cell_{self.current_cell}_max_weight_threshold": config.measurement.max_weight_threshold,
            "selected_load_cell": self.current_cell,
        }
