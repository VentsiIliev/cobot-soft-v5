"""
Contour detection settings group.

Provides configuration options for contour detection and filtering.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QGridLayout, QHBoxLayout

from core.model.settings.CameraSettings import CameraSettings
from .base import CameraSettingGroupBase


class ContourSettingsGroup(CameraSettingGroupBase):
    """Contour detection settings group box"""

    def __init__(self, camera_settings: CameraSettings):
        super().__init__("Contour Detection")  # TODO: TRANSLATE

        self.camera_settings = camera_settings

        # Create layout
        layout = QGridLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        # Create widgets
        self._create_widgets(layout)

        layout.setColumnStretch(1, 1)

    def _create_widgets(self, layout: QGridLayout):
        """Create all widgets for this group"""
        row = 0

        # Enable Contour Detection
        label = QLabel("Enable Contour Detection:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.contour_detection_toggle = self.create_toggle(
            self.camera_settings.get_contour_detection()
        )
        layout.addWidget(self.contour_detection_toggle, row, 1)

        # Draw Contours
        row += 1
        label = QLabel("Draw Contours:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.draw_contours_toggle = self.create_toggle(
            self.camera_settings.get_draw_contours()
        )
        layout.addWidget(self.draw_contours_toggle, row, 1)

        # Threshold
        row += 1
        label = QLabel("Threshold:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.threshold_input = self.create_spinbox(
            0, 255, self.camera_settings.get_threshold()
        )
        layout.addWidget(self.threshold_input, row, 1)

        # Threshold Pickup Area
        row += 1
        label = QLabel("Threshold Pickup Area:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.threshold_pickup_area_input = self.create_spinbox(
            0, 255, self.camera_settings.get_threshold_pickup_area()
        )
        layout.addWidget(self.threshold_pickup_area_input, row, 1)

        # Epsilon
        row += 1
        label = QLabel("Epsilon:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.epsilon_input = self.create_double_spinbox(
            0.0, 10.0, self.camera_settings.get_epsilon(), decimals=2
        )
        layout.addWidget(self.epsilon_input, row, 1)

        # Min Contour Area
        row += 1
        label = QLabel("Min Contour Area:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.min_contour_area_input = self.create_spinbox(
            0, 100000, self.camera_settings.get_min_contour_area(), " px²"
        )
        layout.addWidget(self.min_contour_area_input, row, 1)

        # Max Contour Area
        row += 1
        label = QLabel("Max Contour Area:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.max_contour_area_input = self.create_spinbox(
            0, 1000000, self.camera_settings.get_max_contour_area(), " px²"
        )
        layout.addWidget(self.max_contour_area_input, row, 1)

        # Test Contour Detection Button
        row += 1
        self.test_contour_button = self.create_button("Test Contour Detection")  # TODO: TRANSLATE
        layout.addWidget(self.test_contour_button, row, 0, 1, 2)