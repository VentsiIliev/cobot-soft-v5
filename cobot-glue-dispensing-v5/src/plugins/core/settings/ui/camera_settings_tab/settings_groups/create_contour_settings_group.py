from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QGridLayout, QGroupBox

from frontend.widgets.SwitchButton import QToggle


def create_contour_settings_group(self):
    """Create contour detection settings group"""
    group = QGroupBox("Contour Detection")  # TODO TRANSLATE
    layout = QGridLayout(group)

    layout.setSpacing(15)
    layout.setContentsMargins(20, 25, 20, 20)

    row = 0

    # Contour Detection Toggle
    label = QLabel("Enable Detection:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.contour_detection_toggle = QToggle()
    self.contour_detection_toggle.setCheckable(True)
    self.contour_detection_toggle.setMinimumHeight(35)
    self.contour_detection_toggle.setChecked(self.camera_settings.get_contour_detection())
    layout.addWidget(self.contour_detection_toggle, row, 1)

    # Draw Contours Toggle
    row += 1
    label = QLabel("Draw Contours:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.draw_contours_toggle = QToggle()
    self.draw_contours_toggle.setCheckable(True)
    self.draw_contours_toggle.setMinimumHeight(35)
    self.draw_contours_toggle.setChecked(self.camera_settings.get_draw_contours())
    layout.addWidget(self.draw_contours_toggle, row, 1)

    # Threshold
    row += 1
    label = QLabel("Threshold:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.threshold_input = self.create_spinbox(0, 255, self.camera_settings.get_threshold())
    layout.addWidget(self.threshold_input, row, 1)

    row += 1
    label = QLabel("Threshold 2:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.threshold_pickup_area_input = self.create_spinbox(0, 255, self.camera_settings.get_threshold_pickup_area())
    layout.addWidget(self.threshold_pickup_area_input, row, 1)

    # Epsilon
    row += 1
    label = QLabel("Epsilon:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.epsilon_input = self.create_double_spinbox(0.0, 1.0, self.camera_settings.get_epsilon())
    layout.addWidget(self.epsilon_input, row, 1)

    row += 1
    label = QLabel("Min Contour Area:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.min_contour_area_input = self.create_spinbox(0, 100000, self.camera_settings.get_min_contour_area())
    layout.addWidget(self.min_contour_area_input)

    row += 1
    label = QLabel("Max Contour Area:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.max_contour_area_input = self.create_spinbox(0, 10000000, self.camera_settings.get_max_contour_area())
    layout.addWidget(self.max_contour_area_input)

    layout.setColumnStretch(1, 1)
    return group
