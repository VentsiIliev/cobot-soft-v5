from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy, QComboBox, QGridLayout, QGroupBox

from frontend.widgets.SwitchButton import QToggle


def create_aruco_settings_group(self):
    """Create ArUco detection settings group"""
    group = QGroupBox("ArUco Detection")  # TODO TRANSLATE
    layout = QGridLayout(group)

    layout.setSpacing(15)
    layout.setContentsMargins(20, 25, 20, 20)

    row = 0

    # ArUco Enabled
    label = QLabel("Enable ArUco:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.aruco_enabled_toggle = QToggle()
    self.aruco_enabled_toggle.setCheckable(True)
    self.aruco_enabled_toggle.setMinimumHeight(35)
    self.aruco_enabled_toggle.setChecked(self.camera_settings.get_aruco_enabled())
    layout.addWidget(self.aruco_enabled_toggle, row, 1)

    # ArUco Dictionary
    row += 1
    label = QLabel("Dictionary:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.aruco_dictionary_combo = QComboBox()
    self.aruco_dictionary_combo.setMinimumHeight(40)
    self.aruco_dictionary_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    self.aruco_dictionary_combo.addItems([
        "DICT_4X4_50", "DICT_4X4_100", "DICT_4X4_250", "DICT_4X4_1000",
        "DICT_5X5_50", "DICT_5X5_100", "DICT_5X5_250", "DICT_5X5_1000",
        "DICT_6X6_50", "DICT_6X6_100", "DICT_6X6_250", "DICT_6X6_1000",
        "DICT_7X7_50", "DICT_7X7_100", "DICT_7X7_250", "DICT_7X7_1000"
    ])
    self.aruco_dictionary_combo.setCurrentText(self.camera_settings.get_aruco_dictionary())
    layout.addWidget(self.aruco_dictionary_combo, row, 1)

    # Flip Image
    row += 1
    label = QLabel("Flip Image:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.aruco_flip_toggle = QToggle()
    self.aruco_flip_toggle.setCheckable(True)
    self.aruco_flip_toggle.setMinimumHeight(35)
    self.aruco_flip_toggle.setChecked(self.camera_settings.get_aruco_flip_image())
    layout.addWidget(self.aruco_flip_toggle, row, 1)

    layout.setColumnStretch(1, 1)
    return group
