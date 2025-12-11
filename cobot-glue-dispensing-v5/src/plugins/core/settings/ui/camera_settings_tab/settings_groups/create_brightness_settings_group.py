from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGridLayout, QGroupBox

from frontend.widgets.MaterialButton import MaterialButton
from frontend.widgets.SwitchButton import QToggle


def create_brightness_settings_group(self):
    """Create a brightness control settings group"""
    group = QGroupBox("Brightness Control")  # TODO TRANSLATE
    layout = QGridLayout(group)

    layout.setSpacing(15)
    layout.setContentsMargins(20, 25, 20, 20)

    row = 0

    # Auto Brightness
    label = QLabel("Auto Brightness:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.brightness_auto_toggle = QToggle()
    self.brightness_auto_toggle.setCheckable(True)
    self.brightness_auto_toggle.setMinimumHeight(35)
    self.brightness_auto_toggle.setChecked(self.camera_settings.get_brightness_auto())
    layout.addWidget(self.brightness_auto_toggle, row, 1)

    # Kp
    row += 1
    label = QLabel("Kp:")
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.kp_input = self.create_double_spinbox(0.0, 10.0, self.camera_settings.get_brightness_kp())
    layout.addWidget(self.kp_input, row, 1)

    # Ki
    row += 1
    label = QLabel("Ki:")
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.ki_input = self.create_double_spinbox(0.0, 10.0, self.camera_settings.get_brightness_ki())
    layout.addWidget(self.ki_input, row, 1)

    # Kd
    row += 1
    label = QLabel("Kd:")
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.kd_input = self.create_double_spinbox(0.0, 10.0, self.camera_settings.get_brightness_kd())
    layout.addWidget(self.kd_input, row, 1)

    # Target Brightness
    row += 1
    label = QLabel("Target Brightness:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.target_brightness_input = self.create_spinbox(0, 255, self.camera_settings.get_target_brightness())
    layout.addWidget(self.target_brightness_input, row, 1)

    # Brightness Area Controls
    row += 1
    area_label = QLabel("Brightness Area:")  # TODO TRANSLATE
    area_label.setWordWrap(True)
    layout.addWidget(area_label, row, 0, Qt.AlignmentFlag.AlignLeft)

    # Area control buttons layout
    area_buttons_layout = QHBoxLayout()

    # Define Area button
    self.define_brightness_area_button = MaterialButton("Define Area")
    self.define_brightness_area_button.setMinimumHeight(35)
    self.define_brightness_area_button.clicked.connect(lambda: self.toggle_brightness_area_selection_mode(True))
    area_buttons_layout.addWidget(self.define_brightness_area_button)

    # Reset Area button
    self.reset_brightness_area_button = MaterialButton("Reset")
    self.reset_brightness_area_button.setMinimumHeight(35)
    self.reset_brightness_area_button.clicked.connect(self.reset_brightness_area)
    area_buttons_layout.addWidget(self.reset_brightness_area_button)

    # Create widget to hold button layout
    area_buttons_widget = QWidget()
    area_buttons_widget.setLayout(area_buttons_layout)
    layout.addWidget(area_buttons_widget, row, 1)

    # Show current area coordinates
    row += 1
    self.brightness_area_status_label = QLabel(self.get_brightness_area_status_text())
    self.brightness_area_status_label.setWordWrap(True)
    self.brightness_area_status_label.setStyleSheet("color: #666; font-size: 10px;")
    layout.addWidget(self.brightness_area_status_label, row, 0, 1, 2)

    # Update display after initialization
    QTimer.singleShot(100, self.refresh_brightness_area_display)

    layout.setColumnStretch(1, 1)
    return group
