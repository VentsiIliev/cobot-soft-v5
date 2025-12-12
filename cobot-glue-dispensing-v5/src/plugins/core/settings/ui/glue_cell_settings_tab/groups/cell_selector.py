"""
Cell selector group - allows user to choose which glue cell to configure.

DUMB component - only emits signals, no business logic.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QLabel, QComboBox, QSizePolicy

from plugins.core.settings.ui.glue_cell_settings_tab.groups.base import GlueCellSettingGroupBox
from plugins.core.settings.ui.glue_cell_settings_tab.utils.styling import get_status_style


class CellSelectorGroup(GlueCellSettingGroupBox):
    """
    Cell selector group - DUMB UI component.

    Only emits signals when cell selection changes or status needs to be displayed.
    Does NOT fetch data or make any API calls.
    """

    # Signal emitted when user selects a different cell
    cell_changed_signal = pyqtSignal(int)  # cell_id (1, 2, or 3)

    def __init__(self, parent=None):
        super().__init__("Load Cell Selection", parent)
        self.build_ui()

    def build_ui(self):
        """Build the UI layout"""
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        # Cell selection dropdown
        row = 0
        label = QLabel("Select Load Cell:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.cell_dropdown = QComboBox()
        self.cell_dropdown.setMinimumHeight(40)
        self.cell_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cell_dropdown.addItems(["Load Cell 1", "Load Cell 2", "Load Cell 3"])
        self.cell_dropdown.setCurrentIndex(0)
        self.cell_dropdown.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self.cell_dropdown, row, 1)

        # Cell status indicator
        row += 1
        label = QLabel("Status:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        self.cell_status_label = QLabel("Unknown")
        self.cell_status_label.setStyleSheet(get_status_style("unknown"))
        layout.addWidget(self.cell_status_label, row, 1)

        layout.setColumnStretch(1, 1)
        self.setLayout(layout)

    def _on_selection_changed(self, index: int):
        """Handle cell selection change (DUMB - just emit signal)"""
        cell_id = index + 1  # Convert 0-based index to 1-based cell_id
        self.cell_changed_signal.emit(cell_id)

    def set_current_cell(self, cell_id: int):
        """
        Update the selected cell (called from parent).

        Args:
            cell_id: Cell ID (1, 2, or 3)
        """
        index = cell_id - 1  # Convert 1-based cell_id to 0-based index
        # Block signals to prevent triggering cell_changed_signal
        self.cell_dropdown.blockSignals(True)
        self.cell_dropdown.setCurrentIndex(index)
        self.cell_dropdown.blockSignals(False)

    def set_status(self, status: str):
        """
        Update the status display (called from parent).

        Args:
            status: Status string ("connected", "disconnected", "error", etc.)
        """
        self.cell_status_label.setText(status.capitalize())
        self.cell_status_label.setStyleSheet(get_status_style(status))

    def update_cell_label(self, cell_id: int, glue_type: str, motor_address: int):
        """
        Update the dropdown label for a specific cell.

        Args:
            cell_id: Cell ID (1, 2, or 3)
            glue_type: Glue type name
            motor_address: Motor address
        """
        index = cell_id - 1
        label = f"Cell {cell_id} ({glue_type}) - Motor {motor_address}"
        self.cell_dropdown.setItemText(index, label)
