from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout

from frontend.widgets.ClickableLabel import ClickableLabel
from plugins.core.dashboard.ui.widgets.MachineIndicatorsWidget import MaterialButton


def create_camera_preview_section(self):
    """Create the camera preview section with preview and controls"""
    preview_widget = QWidget()
    preview_widget.setFixedWidth(500)
    preview_widget.setStyleSheet("""
        QWidget {
            background-color: #f0f0f0;
            border: 2px solid #ccc;
            border-radius: 8px;
        }
    """)

    preview_layout = QVBoxLayout(preview_widget)
    preview_layout.setContentsMargins(20, 20, 20, 20)
    preview_layout.setSpacing(15)

    # Status label
    self.camera_status_label = QLabel("Camera Status: Disconnected")
    self.camera_status_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
    preview_layout.addWidget(self.camera_status_label)

    # Camera preview area
    self.camera_preview_label = ClickableLabel("Calibration Preview")
    self.camera_preview_label.clicked.connect(self.on_preview_clicked)
    self.camera_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.camera_preview_label.setStyleSheet("""
        QLabel {
            background-color: #333;
            color: white;
            font-size: 16px;
            border: 1px solid #666;
            border-radius: 4px;
        }
    """)
    self.camera_preview_label.setFixedSize(460, 259)
    self.camera_preview_label.setScaledContents(False)
    preview_layout.addWidget(self.camera_preview_label)

    # Set target size for worker thread
    if hasattr(self, 'frame_processor'):
        self.frame_processor.set_target_size(460, 259)

    # Threshold preview area
    self.threshold_preview_label = ClickableLabel("Threshold Preview")
    self.threshold_preview_label.clicked.connect(self.on_threshold_preview_clicked)
    self.threshold_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.threshold_preview_label.setStyleSheet("""
        QLabel {
            background-color: #222;
            color: white;
            font-size: 16px;
            border: 1px solid #666;
            border-radius: 4px;
        }
    """)
    self.threshold_preview_label.setFixedSize(460, 259)
    self.threshold_preview_label.setScaledContents(False)
    preview_layout.addWidget(self.threshold_preview_label)

    # set

    # Control buttons grid
    button_grid = QGridLayout()
    button_grid.setSpacing(10)

    # Row 0: Camera buttons
    self.capture_image_button = MaterialButton("Capture Image")
    self.show_raw_button = MaterialButton("Raw Mode")
    self.show_raw_button.setCheckable(True)
    self.show_raw_button.setChecked(self.raw_mode_active)

    cam_buttons = [self.capture_image_button, self.show_raw_button]
    for i, btn in enumerate(cam_buttons):
        btn.setMinimumHeight(40)
        button_grid.addWidget(btn, 0, i)

    # Row 1: Calibration buttons
    self.start_calibration_button = MaterialButton("Start Calibration")
    self.save_calibration_button = MaterialButton("Save Calibration")

    calib_buttons = [self.start_calibration_button, self.save_calibration_button]
    for i, btn in enumerate(calib_buttons):
        btn.setMinimumHeight(40)
        button_grid.addWidget(btn, 1, i)

    # Row 2: More buttons
    self.load_calibration_button = MaterialButton("Load Calibration")
    self.test_contour_button = MaterialButton("Test Contour")

    more_buttons = [self.load_calibration_button, self.test_contour_button]
    for i, btn in enumerate(more_buttons):
        btn.setMinimumHeight(40)
        button_grid.addWidget(btn, 2, i)

    # Row 3: Detection and ArUco
    self.test_aruco_button = MaterialButton("Test ArUco")
    spacer_btn = QWidget()

    detect_buttons = [self.test_aruco_button, spacer_btn]
    for i, widget in enumerate(detect_buttons):
        if isinstance(widget, MaterialButton):
            widget.setMinimumHeight(40)
        button_grid.addWidget(widget, 3, i)

    # Row 4: Settings buttons
    self.save_settings_button = MaterialButton("Save Settings")
    self.load_settings_button = MaterialButton("Load Settings")

    settings_buttons = [self.save_settings_button, self.load_settings_button]
    for i, btn in enumerate(settings_buttons):
        btn.setMinimumHeight(40)
        button_grid.addWidget(btn, 4, i)

    # Row 5: Reset button
    self.reset_settings_button = MaterialButton("Reset Defaults")
    self.reset_settings_button.setMinimumHeight(40)
    button_grid.addWidget(self.reset_settings_button, 5, 0, 1, 2)

    # preview_layout.addLayout(button_grid)
    preview_layout.addStretch()

    self.connect_default_callbacks()
    return preview_widget
