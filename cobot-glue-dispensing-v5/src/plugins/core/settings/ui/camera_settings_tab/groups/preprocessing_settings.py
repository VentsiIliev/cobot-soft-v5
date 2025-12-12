"""
Preprocessing settings group.

Provides image preprocessing configuration (blur, dilate, erode, etc.).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QGridLayout

from core.model.settings.CameraSettings import CameraSettings
from .base import CameraSettingGroupBase


class PreprocessingSettingsGroup(CameraSettingGroupBase):
    """Preprocessing settings group box"""

    def __init__(self, camera_settings: CameraSettings):
        super().__init__("Preprocessing")  # TODO: TRANSLATE

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

        # Gaussian Blur
        label = QLabel("Gaussian Blur:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.gaussian_blur_toggle = self.create_toggle(
            self.camera_settings.get_gaussian_blur()
        )
        layout.addWidget(self.gaussian_blur_toggle, row, 1)

        # Blur Kernel Size
        row += 1
        label = QLabel("Blur Kernel Size:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.blur_kernel_input = self.create_spinbox(
            1, 31, self.camera_settings.get_blur_kernel_size()
        )
        layout.addWidget(self.blur_kernel_input, row, 1)

        # Threshold Type
        row += 1
        label = QLabel("Threshold Type:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.threshold_type_combo = self.create_combo(
            ["binary", "binary_inv", "trunc", "tozero", "tozero_inv"],
            self.camera_settings.get_threshold_type()
        )
        layout.addWidget(self.threshold_type_combo, row, 1)

        # Dilate Enabled
        row += 1
        label = QLabel("Dilate:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_enabled_toggle = self.create_toggle(
            self.camera_settings.get_dilate_enabled()
        )
        layout.addWidget(self.dilate_enabled_toggle, row, 1)

        # Dilate Kernel Size
        row += 1
        label = QLabel("Dilate Kernel:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_kernel_input = self.create_spinbox(
            1, 31, self.camera_settings.get_dilate_kernel_size()
        )
        layout.addWidget(self.dilate_kernel_input, row, 1)

        # Dilate Iterations
        row += 1
        label = QLabel("Dilate Iterations:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_iterations_input = self.create_spinbox(
            0, 20, self.camera_settings.get_dilate_iterations()
        )
        layout.addWidget(self.dilate_iterations_input, row, 1)

        # Erode Enabled
        row += 1
        label = QLabel("Erode:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_enabled_toggle = self.create_toggle(
            self.camera_settings.get_erode_enabled()
        )
        layout.addWidget(self.erode_enabled_toggle, row, 1)

        # Erode Kernel Size
        row += 1
        label = QLabel("Erode Kernel:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_kernel_input = self.create_spinbox(
            1, 31, self.camera_settings.get_erode_kernel_size()
        )
        layout.addWidget(self.erode_kernel_input, row, 1)

        # Erode Iterations
        row += 1
        label = QLabel("Erode Iterations:")  # TODO: TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_iterations_input = self.create_spinbox(
            0, 20, self.camera_settings.get_erode_iterations()
        )
        layout.addWidget(self.erode_iterations_input, row, 1)
