"""
ArUco detection settings group.

Provides ArUco marker detection configuration options.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QGridLayout

from core.model.settings.CameraSettings import CameraSettings
from .base import CameraSettingGroupBase


class ArucoSettingsGroup(CameraSettingGroupBase):
    """ArUco detection settings group box"""

    def __init__(self, camera_settings: CameraSettings):
        super().__init__("ArUco Detection")  # TODO: TRANSLATE

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

        # ArUco Enabled
        label = QLabel("Enable ArUco:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_enabled_toggle = self.create_toggle(
            self.camera_settings.get_aruco_enabled()
        )
        layout.addWidget(self.aruco_enabled_toggle, row, 1)

        # ArUco Dictionary
        row += 1
        label = QLabel("Dictionary:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        aruco_dicts = [
            "DICT_4X4_50", "DICT_4X4_100", "DICT_4X4_250", "DICT_4X4_1000",
            "DICT_5X5_50", "DICT_5X5_100", "DICT_5X5_250", "DICT_5X5_1000",
            "DICT_6X6_50", "DICT_6X6_100", "DICT_6X6_250", "DICT_6X6_1000",
            "DICT_7X7_50", "DICT_7X7_100", "DICT_7X7_250", "DICT_7X7_1000"
        ]
        self.aruco_dictionary_combo = self.create_combo(
            aruco_dicts,
            self.camera_settings.get_aruco_dictionary()
        )
        layout.addWidget(self.aruco_dictionary_combo, row, 1)

        # Flip Image
        row += 1
        label = QLabel("Flip Image:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_flip_toggle = self.create_toggle(
            self.camera_settings.get_aruco_flip_image()
        )
        layout.addWidget(self.aruco_flip_toggle, row, 1)

        # Test ArUco Detection Button
        row += 1
        self.test_aruco_button = self.create_button("Test ArUco Detection")  # TODO: TRANSLATE
        layout.addWidget(self.test_aruco_button, row, 0, 1, 2)
