from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy, QComboBox, QGridLayout, QGroupBox

from frontend.widgets.SwitchButton import QToggle


def create_preprocessing_settings_group(self):
    """Create a preprocessing settings group"""
    group = QGroupBox("Preprocessing")  # TODO TRANSLATE
    layout = QGridLayout(group)

    layout.setSpacing(15)
    layout.setContentsMargins(20, 25, 20, 20)

    row = 0

    # Gaussian Blur
    label = QLabel("Gaussian Blur:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.gaussian_blur_toggle = QToggle()
    self.gaussian_blur_toggle.setCheckable(True)
    self.gaussian_blur_toggle.setMinimumHeight(35)
    self.gaussian_blur_toggle.setChecked(self.camera_settings.get_gaussian_blur())
    layout.addWidget(self.gaussian_blur_toggle, row, 1)

    # Blur Kernel Size
    row += 1
    label = QLabel("Blur Kernel Size:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.blur_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_blur_kernel_size())
    layout.addWidget(self.blur_kernel_input, row, 1)

    # Threshold Type
    row += 1
    label = QLabel("Threshold Type:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.threshold_type_combo = QComboBox()
    self.threshold_type_combo.setMinimumHeight(40)
    self.threshold_type_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    self.threshold_type_combo.addItems(["binary", "binary_inv", "trunc", "tozero", "tozero_inv"])
    self.threshold_type_combo.setCurrentText(self.camera_settings.get_threshold_type())
    layout.addWidget(self.threshold_type_combo, row, 1)

    # Dilate Enabled
    row += 1
    label = QLabel("Dilate:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.dilate_enabled_toggle = QToggle()
    self.dilate_enabled_toggle.setCheckable(True)
    self.dilate_enabled_toggle.setMinimumHeight(35)
    self.dilate_enabled_toggle.setChecked(self.camera_settings.get_dilate_enabled())
    layout.addWidget(self.dilate_enabled_toggle, row, 1)

    # Dilate Kernel Size
    row += 1
    label = QLabel("Dilate Kernel:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.dilate_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_dilate_kernel_size())
    layout.addWidget(self.dilate_kernel_input, row, 1)

    # Dilate Iterations
    row += 1
    label = QLabel("Dilate Iterations:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.dilate_iterations_input = self.create_spinbox(0, 20, self.camera_settings.get_dilate_iterations())
    layout.addWidget(self.dilate_iterations_input, row, 1)

    # Erode Enabled
    row += 1
    label = QLabel("Erode:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.erode_enabled_toggle = QToggle()
    self.erode_enabled_toggle.setCheckable(True)
    self.erode_enabled_toggle.setMinimumHeight(35)
    self.erode_enabled_toggle.setChecked(self.camera_settings.get_erode_enabled())
    layout.addWidget(self.erode_enabled_toggle, row, 1)

    # Erode Kernel Size
    row += 1
    label = QLabel("Erode Kernel:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.erode_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_erode_kernel_size())
    layout.addWidget(self.erode_kernel_input, row, 1)

    # Erode Iterations
    row += 1
    label = QLabel("Erode Iterations:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.erode_iterations_input = self.create_spinbox(0, 20, self.camera_settings.get_erode_iterations())
    layout.addWidget(self.erode_iterations_input, row, 1)

    layout.setColumnStretch(1, 1)
    return group
