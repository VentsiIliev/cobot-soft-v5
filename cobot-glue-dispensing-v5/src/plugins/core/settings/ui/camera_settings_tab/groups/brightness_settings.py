"""
Brightness control settings group.

Provides PID-based brightness control and area selection.
"""

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGridLayout

from core.model.settings.CameraSettings import CameraSettings
from frontend.widgets.MaterialButton import MaterialButton
from .base import CameraSettingGroupBase


class BrightnessSettingsGroup(CameraSettingGroupBase):
    """Brightness control settings group box"""

    def __init__(self, camera_settings: CameraSettings, parent_ui):
        super().__init__("Brightness Control")  # TODO: TRANSLATE

        self.camera_settings = camera_settings
        self.parent_ui = parent_ui  # Reference to parent CameraSettingsUI for callbacks

        # Create layout
        layout = QGridLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        # Create widgets
        self._create_widgets(layout)

        layout.setColumnStretch(1, 1)

        # Update display after initialization
        QTimer.singleShot(100, self._refresh_brightness_area_display)

    def _create_widgets(self, layout: QGridLayout):
        """Create all widgets for this group"""
        row = 0

        # Auto Brightness
        label = QLabel("Auto Brightness:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.brightness_auto_toggle = self.create_toggle(
            self.camera_settings.get_brightness_auto()
        )
        layout.addWidget(self.brightness_auto_toggle, row, 1)

        # Kp
        row += 1
        label = QLabel("Kp:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.kp_input = self.create_double_spinbox(
            0.0, 10.0, self.camera_settings.get_brightness_kp()
        )
        layout.addWidget(self.kp_input, row, 1)

        # Ki
        row += 1
        label = QLabel("Ki:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.ki_input = self.create_double_spinbox(
            0.0, 10.0, self.camera_settings.get_brightness_ki()
        )
        layout.addWidget(self.ki_input, row, 1)

        # Kd
        row += 1
        label = QLabel("Kd:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.kd_input = self.create_double_spinbox(
            0.0, 10.0, self.camera_settings.get_brightness_kd()
        )
        layout.addWidget(self.kd_input, row, 1)

        # Target Brightness
        row += 1
        label = QLabel("Target Brightness:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.target_brightness_input = self.create_spinbox(
            0, 255, self.camera_settings.get_target_brightness()
        )
        layout.addWidget(self.target_brightness_input, row, 1)

        # Brightness Area Controls
        row += 1
        area_label = QLabel("Brightness Area:")  # TODO: TRANSLATE
        area_label.setWordWrap(True)
        layout.addWidget(area_label, row, 0, Qt.AlignmentFlag.AlignLeft)

        # Area control buttons layout
        area_buttons_layout = QHBoxLayout()

        # Define Area button
        self.define_brightness_area_button = MaterialButton("Define Area")
        self.define_brightness_area_button.setMinimumHeight(35)
        self.define_brightness_area_button.clicked.connect(self._toggle_brightness_area_selection)
        area_buttons_layout.addWidget(self.define_brightness_area_button)

        # Reset Area button
        self.reset_brightness_area_button = MaterialButton("Reset")
        self.reset_brightness_area_button.setMinimumHeight(35)
        self.reset_brightness_area_button.clicked.connect(self._reset_brightness_area)
        area_buttons_layout.addWidget(self.reset_brightness_area_button)

        # Create widget to hold button layout
        area_buttons_widget = QWidget()
        area_buttons_widget.setLayout(area_buttons_layout)
        layout.addWidget(area_buttons_widget, row, 1)

        # Show current area coordinates
        row += 1
        self.brightness_area_status_label = QLabel(self._get_brightness_area_status_text())
        self.brightness_area_status_label.setWordWrap(True)
        self.brightness_area_status_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.brightness_area_status_label, row, 0, 1, 2)

    def _toggle_brightness_area_selection(self):
        """Toggle brightness area selection mode"""
        if hasattr(self.parent_ui, 'brightness_area_selection_mode'):
            new_mode = not self.parent_ui.brightness_area_selection_mode
            self.parent_ui.brightness_area_selection_mode = new_mode

            if new_mode:
                # Entering selection mode
                self.parent_ui.brightness_area_points = []
                self.define_brightness_area_button.setText("Cancel Selection")
                self.define_brightness_area_button.setStyleSheet("background-color: #ff6b6b;")
                if hasattr(self.parent_ui, 'showToast'):
                    self.parent_ui.showToast("Click 4 points on the camera preview to define brightness area")
            else:
                # Exiting selection mode
                self.define_brightness_area_button.setText("Define Area")
                self.define_brightness_area_button.setStyleSheet("")
                self.parent_ui.brightness_area_points = []

            self._refresh_brightness_area_display()

    def _reset_brightness_area(self):
        """Reset brightness area to empty"""
        if hasattr(self.parent_ui, 'camera_settings'):
            self.parent_ui.camera_settings.set_brightness_area_points([])
            self.parent_ui.brightness_area_points = []
            self.parent_ui.brightness_area_selection_mode = False
            self.define_brightness_area_button.setText("Define Area")
            self.define_brightness_area_button.setStyleSheet("")
            self._refresh_brightness_area_display()

            if hasattr(self.parent_ui, 'showToast'):
                self.parent_ui.showToast("Brightness area reset")

    def _get_brightness_area_status_text(self):
        """Get status text for brightness area"""
        if hasattr(self.parent_ui, 'camera_settings'):
            points = self.parent_ui.camera_settings.get_brightness_area_points()
            if points and len(points) == 4:
                return f"Area defined: {len(points)} points"
            elif hasattr(self.parent_ui, 'brightness_area_points') and self.parent_ui.brightness_area_points:
                return f"Selecting: {len(self.parent_ui.brightness_area_points)}/4 points"
            else:
                return "No area defined"
        return "No area defined"

    def _refresh_brightness_area_display(self):
        """Refresh the brightness area status display"""
        if hasattr(self, 'brightness_area_status_label'):
            self.brightness_area_status_label.setText(self._get_brightness_area_status_text())
