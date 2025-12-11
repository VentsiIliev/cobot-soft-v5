from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QGroupBox, QGridLayout


def create_core_settings_group(self):
    """Create core camera settings group"""
    group = QGroupBox("Camera Settings")  # TODO TRANSLATE
    layout = QGridLayout(group)

    layout.setSpacing(15)
    layout.setContentsMargins(20, 25, 20, 20)

    row = 0

    # Camera Index
    label = QLabel("Camera Index:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.camera_index_input = self.create_spinbox(0, 10, self.camera_settings.get_camera_index())
    layout.addWidget(self.camera_index_input, row, 1)

    # Width
    row += 1
    label = QLabel("Width:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.width_input = self.create_spinbox(320, 4096, self.camera_settings.get_camera_width(), " px")
    layout.addWidget(self.width_input, row, 1)

    # Height
    row += 1
    label = QLabel("Height:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.height_input = self.create_spinbox(240, 2160, self.camera_settings.get_camera_height(), " px")
    layout.addWidget(self.height_input, row, 1)

    # Skip Frames
    row += 1
    label = QLabel("Skip Frames:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.skip_frames_input = self.create_spinbox(0, 100, self.camera_settings.get_skip_frames())
    layout.addWidget(self.skip_frames_input, row, 1)

    row += 1
    label = QLabel("Capture Pos Offset:")  # TODO TRANSLATE
    label.setWordWrap(True)
    layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    self.capture_pos_offset_input = self.create_spinbox(-100, 100, self.camera_settings.get_capture_pos_offset(),
                                                        " mm")
    layout.addWidget(self.capture_pos_offset_input, row, 1)

    layout.setColumnStretch(1, 1)
    return group
