"""
Connection settings group - hardware and connection configuration.

DUMB component - only emits signals, no business logic or API calls.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QLabel, QComboBox, QSizePolicy, QLineEdit, QHBoxLayout

from plugins.core.settings.ui.glue_cell_settings_tab.groups.base import GlueCellSettingGroupBox
from plugins.core.settings.ui.glue_cell_settings_tab.models.cell_config import ConnectionSettings
from plugins.core.settings.ui.glue_cell_settings_tab.utils.validators import parse_ip_from_url
from plugins.core.settings.ui.glue_cell_settings_tab.utils.styling import get_mode_style
from frontend.widgets.SwitchButton import QToggle


class ConnectionSettingsGroup(GlueCellSettingGroupBox):
    """
    Connection settings group - DUMB UI component.

    Emits signals for all field changes. Parent is responsible for:
    - Validating motor address conflicts
    - Saving to backend
    - Loading available glue types
    """

    # Signal emitted when any connection field changes
    connection_changed_signal = pyqtSignal(str, object)  # field_name, value

    def __init__(self, available_glue_types: list = None, parent=None):
        """
        Initialize connection settings group.

        Args:
            available_glue_types: List of glue type names (loaded by parent from API)
            parent: Parent widget
        """
        super().__init__("Connection & Hardware Settings", parent)
        self.available_glue_types = available_glue_types or []
        self.build_ui()

    def build_ui(self):
        """Build the UI layout"""
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Mode Toggle (Test/Production)
        label = QLabel("Mode:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        mode_layout = QHBoxLayout()
        self.mode_label = QLabel("Production")
        self.mode_label.setStyleSheet(get_mode_style("production"))
        self.mode_toggle = QToggle()
        self.mode_toggle.setChecked(False)  # Default to production
        self.mode_toggle.stateChanged.connect(self._on_mode_changed)

        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_toggle)
        mode_layout.addStretch()

        layout.addLayout(mode_layout, row, 1)
        row += 1

        # Glue Type
        label = QLabel("Glue Type:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.glue_type_dropdown = QComboBox()
        self.glue_type_dropdown.setMinimumHeight(40)
        self.glue_type_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.glue_type_dropdown.addItems(self.available_glue_types)
        self.glue_type_dropdown.currentTextChanged.connect(
            lambda val: self.connection_changed_signal.emit("glue_type", val)
        )
        layout.addWidget(self.glue_type_dropdown, row, 1)
        row += 1

        # Motor Address
        label = QLabel("Motor Address:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.motor_address_dropdown = QComboBox()
        self.motor_address_dropdown.setMinimumHeight(40)
        self.motor_address_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.motor_address_dropdown.addItems(["0", "2", "4", "6", "8", "10"])
        self.motor_address_dropdown.currentTextChanged.connect(
            lambda val: self.connection_changed_signal.emit("motor_address", int(val))
        )
        layout.addWidget(self.motor_address_dropdown, row, 1)
        row += 1

        # Capacity
        label = QLabel("Capacity:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.capacity_input = self.create_spinbox(100, 50000, 10000, " g")
        self.capacity_input.valueChanged.connect(
            lambda val: self.connection_changed_signal.emit("capacity", val)
        )
        layout.addWidget(self.capacity_input, row, 1)
        row += 1

        # URL
        label = QLabel("URL:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.url_input = QLineEdit()
        self.url_input.setMinimumHeight(40)
        self.url_input.setPlaceholderText("http://192.168.222.143/weight1")
        self.url_input.textChanged.connect(self._on_url_changed)
        layout.addWidget(self.url_input, row, 1)
        row += 1

        # IP Address (extracted from URL)
        label = QLabel("IP Address:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.ip_address_label = QLabel("--")
        self.ip_address_label.setStyleSheet("QLabel { font-family: monospace; color: #555555; }")
        layout.addWidget(self.ip_address_label, row, 1)
        row += 1

        # Fetch Timeout
        label = QLabel("Fetch Timeout:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.fetch_timeout_input = self.create_spinbox(1, 30, 5, " seconds")
        self.fetch_timeout_input.valueChanged.connect(
            lambda val: self.connection_changed_signal.emit("fetch_timeout", val)
        )
        layout.addWidget(self.fetch_timeout_input, row, 1)

        layout.setColumnStretch(1, 1)
        self.setLayout(layout)

    def _on_mode_changed(self, state: bool):
        """Handle mode toggle change (DUMB - just update UI and emit signal)"""
        mode = "test" if state else "production"

        if state:  # Test mode
            self.mode_label.setText("Test (Mock Server)")
            self.mode_label.setStyleSheet(get_mode_style("test"))
        else:  # Production mode
            self.mode_label.setText("Production")
            self.mode_label.setStyleSheet(get_mode_style("production"))

        self.connection_changed_signal.emit("mode", mode)

    def _on_url_changed(self, url: str):
        """Handle URL change (update IP display and emit signal)"""
        # Update IP display
        ip = parse_ip_from_url(url)
        self.ip_address_label.setText(ip)

        # Emit signal
        self.connection_changed_signal.emit("url", url)

    def get_settings(self) -> ConnectionSettings:
        """
        Get current connection settings from UI widgets.

        Returns:
            ConnectionSettings dataclass
        """
        return ConnectionSettings(
            glue_type=self.glue_type_dropdown.currentText(),
            motor_address=int(self.motor_address_dropdown.currentText()),
            capacity=self.capacity_input.value(),
            url=self.url_input.text(),
            fetch_timeout=self.fetch_timeout_input.value(),
            mode="test" if self.mode_toggle.isChecked() else "production"
        )

    def update_values(self, settings: ConnectionSettings):
        """
        Update UI widgets from ConnectionSettings dataclass.

        Blocks signals during update to prevent triggering change events.

        Args:
            settings: ConnectionSettings dataclass
        """
        # Block all signals
        self.mode_toggle.blockSignals(True)
        self.glue_type_dropdown.blockSignals(True)
        self.motor_address_dropdown.blockSignals(True)
        self.capacity_input.blockSignals(True)
        self.url_input.blockSignals(True)
        self.fetch_timeout_input.blockSignals(True)

        try:
            # Update mode
            is_test_mode = settings.mode == "test"
            self.mode_toggle.setChecked(is_test_mode)
            if is_test_mode:
                self.mode_label.setText("Test (Mock Server)")
                self.mode_label.setStyleSheet(get_mode_style("test"))
            else:
                self.mode_label.setText("Production")
                self.mode_label.setStyleSheet(get_mode_style("production"))

            # Update glue type
            glue_type_index = self.glue_type_dropdown.findText(settings.glue_type)
            if glue_type_index >= 0:
                self.glue_type_dropdown.setCurrentIndex(glue_type_index)
            else:
                # Add missing type dynamically
                self.glue_type_dropdown.addItem(settings.glue_type)
                new_index = self.glue_type_dropdown.findText(settings.glue_type)
                self.glue_type_dropdown.setCurrentIndex(new_index)

            # Update motor address
            motor_str = str(settings.motor_address)
            motor_index = self.motor_address_dropdown.findText(motor_str)
            if motor_index >= 0:
                self.motor_address_dropdown.setCurrentIndex(motor_index)
            else:
                # Add missing address dynamically
                self.motor_address_dropdown.addItem(motor_str)
                new_index = self.motor_address_dropdown.findText(motor_str)
                self.motor_address_dropdown.setCurrentIndex(new_index)

            # Update other fields
            self.capacity_input.setValue(settings.capacity)
            self.url_input.setText(settings.url)
            self.fetch_timeout_input.setValue(settings.fetch_timeout)

            # Update IP display
            self.ip_address_label.setText(settings.ip_address)

        finally:
            # Always unblock signals
            self.mode_toggle.blockSignals(False)
            self.glue_type_dropdown.blockSignals(False)
            self.motor_address_dropdown.blockSignals(False)
            self.capacity_input.blockSignals(False)
            self.url_input.blockSignals(False)
            self.fetch_timeout_input.blockSignals(False)

    def set_available_glue_types(self, glue_types: list):
        """
        Update available glue types in dropdown.

        Args:
            glue_types: List of glue type names
        """
        current = self.glue_type_dropdown.currentText()
        self.glue_type_dropdown.blockSignals(True)
        self.glue_type_dropdown.clear()
        self.glue_type_dropdown.addItems(glue_types)

        # Restore current selection if still available
        index = self.glue_type_dropdown.findText(current)
        if index >= 0:
            self.glue_type_dropdown.setCurrentIndex(index)

        self.glue_type_dropdown.blockSignals(False)
