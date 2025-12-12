"""
Calibration settings group.

Provides camera calibration configuration options.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QGridLayout

from core.model.settings.CameraSettings import CameraSettings
from .base import CameraSettingGroupBase


class CalibrationSettingsGroup(CameraSettingGroupBase):
    """Calibration settings group box"""

    def __init__(self, camera_settings: CameraSettings):
        super().__init__("Calibration")  # TODO: TRANSLATE

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

        # Chessboard Width
        label = QLabel("Chessboard Width:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.chessboard_width_input = self.create_spinbox(
            1, 100, self.camera_settings.get_chessboard_width()
        )
        layout.addWidget(self.chessboard_width_input, row, 1)

        # Chessboard Height
        row += 1
        label = QLabel("Chessboard Height:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.chessboard_height_input = self.create_spinbox(
            1, 100, self.camera_settings.get_chessboard_height()
        )
        layout.addWidget(self.chessboard_height_input, row, 1)

        # Square Size
        row += 1
        label = QLabel("Square Size:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.square_size_input = self.create_double_spinbox(
            1.0, 1000.0, self.camera_settings.get_square_size_mm(), " mm"
        )
        layout.addWidget(self.square_size_input, row, 1)

        # Calibration Skip Frames
        row += 1
        label = QLabel("Skip Frames:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.calib_skip_frames_input = self.create_spinbox(
            0, 100, self.camera_settings.get_calibration_skip_frames()
        )
        layout.addWidget(self.calib_skip_frames_input, row, 1)

        # Calibration Buttons
        row += 1
        self.start_calibration_button = self.create_button("Start Calibration")  # TODO: TRANSLATE
        layout.addWidget(self.start_calibration_button, row, 0, 1, 2)

        row += 1
        self.save_calibration_button = self.create_button("Save Calibration")  # TODO: TRANSLATE
        layout.addWidget(self.save_calibration_button, row, 0, 1, 2)

        row += 1
        self.load_calibration_button = self.create_button("Load Calibration")  # TODO: TRANSLATE
        layout.addWidget(self.load_calibration_button, row, 0, 1, 2)
