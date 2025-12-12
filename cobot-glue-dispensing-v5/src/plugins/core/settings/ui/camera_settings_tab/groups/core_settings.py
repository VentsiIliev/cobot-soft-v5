"""
Core camera settings group.

Provides basic camera configuration options (index, width, height, etc.).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QGridLayout

from core.model.settings.CameraSettings import CameraSettings
from .base import CameraSettingGroupBase


class CoreSettingsGroup(CameraSettingGroupBase):
    """Core camera settings group box"""

    def __init__(self, camera_settings: CameraSettings):
        super().__init__("Camera Settings")  # TODO: TRANSLATE

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

        # Camera Index
        label = QLabel("Camera Index:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.camera_index_input = self.create_spinbox(
            0, 10, self.camera_settings.get_camera_index()
        )
        layout.addWidget(self.camera_index_input, row, 1)

        # Width
        row += 1
        label = QLabel("Width:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.width_input = self.create_spinbox(
            320, 4096, self.camera_settings.get_camera_width(), " px"
        )
        layout.addWidget(self.width_input, row, 1)

        # Height
        row += 1
        label = QLabel("Height:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.height_input = self.create_spinbox(
            240, 2160, self.camera_settings.get_camera_height(), " px"
        )
        layout.addWidget(self.height_input, row, 1)

        # Skip Frames
        row += 1
        label = QLabel("Skip Frames:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.skip_frames_input = self.create_spinbox(
            0, 100, self.camera_settings.get_skip_frames()
        )
        layout.addWidget(self.skip_frames_input, row, 1)

        # Capture Position Offset
        row += 1
        label = QLabel("Capture Pos Offset:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.capture_pos_offset_input = self.create_spinbox(
            -100, 100, self.camera_settings.get_capture_pos_offset(), " mm"
        )
        layout.addWidget(self.capture_pos_offset_input, row, 1)