import time
from enum import Enum

from PyQt6.QtCore import Qt, QThread, QObject, QRunnable, pyqtSlot
from PyQt6.QtWidgets import QScroller
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QHBoxLayout,
                             QSizePolicy, QComboBox,
                             QScrollArea, QGroupBox, QGridLayout, QTabWidget)
from frontend.widgets.MaterialButton import MaterialButton
from frontend.core.utils.localization import TranslationKeys, get_app_translator
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettingKey
from applications.glue_dispensing_application.services.glueSprayService.GlueSprayService import GlueSprayService
from frontend.widgets.SwitchButton import QToggle
from frontend.widgets.ToastWidget import ToastWidget
from plugins.core.glue_settings_plugin.ui.generator_workers import GeneratorWorker, RefreshGeneratorWorker
from plugins.core.glue_settings_plugin.ui.motor_workers import MotorWorker, RefreshMotorsWorker
from plugins.core.glue_settings_plugin.ui.GlueTypeManagementTab import GlueTypeManagementTab

from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout
# import pyqtSignal
from PyQt6.QtCore import pyqtSignal
from applications.glue_dispensing_application.config.cell_hardware_config import CellHardwareConfig

from applications.glue_dispensing_application.services.glue.glue_type_migration import get_all_glue_type_names
from applications.glue_dispensing_application.services.glueSprayService.GlueDispatchService import GlueDispatchService


class GlueSettingsTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    value_changed_signal = pyqtSignal(str, object, str)  # key, value, className
    def __init__(self, parent_widget,glueSettings):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)

        self.dropdown = None
        self.parent_widget = parent_widget

        self.glueSprayService = GlueSprayService(glueSettings)
        self.glueDispatchService = GlueDispatchService(self.glueSprayService)
        self.translator = get_app_translator()
        self.translator.language_changed.connect(self.translate)
        self.create_main_content()
        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

    def translate(self):
            """Update UI text based on current language"""
            # Update styling to ensure responsive fonts are applied
            self.setup_styling()

            # Spray settings group
            if hasattr(self, 'spray_group'):
                self.spray_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.SPRAY_SETTINGS))
                if hasattr(self, 'spray_layout'):
                    if self.spray_layout.itemAtPosition(0, 0):
                        self.spray_layout.itemAtPosition(0, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.SPRAY_WIDTH))
                    if self.spray_layout.itemAtPosition(1, 0):
                        self.spray_layout.itemAtPosition(1, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.SPRAYING_HEIGHT))
                    if self.spray_layout.itemAtPosition(2, 0):
                        self.spray_layout.itemAtPosition(2, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.FAN_SPEED))
                    if self.spray_layout.itemAtPosition(3, 0):
                        self.spray_layout.itemAtPosition(3, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.GENERATOR_TO_GLUE_DELAY))

            # Motor settings group
            if hasattr(self, 'motor_group'):
                self.motor_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.MOTOR_SETTINGS))
                if hasattr(self, 'motor_layout'):
                    if self.motor_layout.itemAtPosition(0, 0):
                        self.motor_layout.itemAtPosition(0, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.MOTOR_SPEED))
                    if self.motor_layout.itemAtPosition(1, 0):
                        self.motor_layout.itemAtPosition(1, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.REVERSE_DURATION))
                    if self.motor_layout.itemAtPosition(2, 0):
                        self.motor_layout.itemAtPosition(2, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.REVERSE_SPEED))

            # General settings group
            if hasattr(self, 'general_group'):
                self.general_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.GENERAL_SETTINGS))
                if hasattr(self, 'general_layout'):
                    if self.general_layout.itemAtPosition(0, 0):
                        self.general_layout.itemAtPosition(0, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.RZ_ANGLE))
                    if self.general_layout.itemAtPosition(2, 0):
                        self.general_layout.itemAtPosition(2, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.GLUE_TYPE))

            # Device control groups
            if hasattr(self, 'motor_control_group'):
                self.motor_control_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.MOTOR_CONTROL))
            if hasattr(self, 'other_control_group'):
                self.other_control_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.OTHER_SETTINGS))

            # Update toggle button texts
            if hasattr(self, 'generator_toggle_btn'):
                self.generator_toggle_btn.setText(self.translator.get(TranslationKeys.GlueSettings.GENERATOR))
            if hasattr(self, 'fan_toggle_btn'):
                self.fan_toggle_btn.setText(self.translator.get(TranslationKeys.GlueSettings.FAN))

            # Update motor toggles
            if hasattr(self, 'motor_toggles'):
                for i, motor_toggle in enumerate(self.motor_toggles, start=1):
                    motor_toggle.setText(f"{self.translator.get(TranslationKeys.GlueSettings.MOTOR)} {i}")

            # Glue dispensing group
            if hasattr(self, 'glue_dispensing_group'):
                self.glue_dispensing_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.DISPENSE_GLUE))
    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def update_layout_for_screen_size(self):
        """Update layout based on current screen size"""
        # Clear and recreate the main content
        self.clear_layout()
        self.create_main_content()

    def clear_layout(self):
        """Clear all widgets from the layout"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    def create_main_content(self):
        """Create the main content with tab widget structure"""
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setContentsMargins(0, 0, 0, 0)

        # Create the main settings tab (contains all current content)
        main_tab = self._create_main_settings_tab()
        self.tab_widget.addTab(main_tab, "Glue Settings")

        # Create and add the Glue Type Management tab
        self.glue_type_tab = GlueTypeManagementTab(self.parent_widget)
        self.tab_widget.addTab(self.glue_type_tab, "Glue Type Management")

        # Connect signals from GlueTypeManagementTab if needed
        self.glue_type_tab.glue_type_added.connect(self._on_glue_type_added)
        self.glue_type_tab.glue_type_removed.connect(self._on_glue_type_removed)
        self.glue_type_tab.glue_type_edited.connect(self._on_glue_type_edited)

        # Add tab widget to main layout
        self.addWidget(self.tab_widget)

    def _create_main_settings_tab(self):
        """Create the main settings tab content with all existing sections"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        QScroller.grabGesture(scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Add all existing content sections
        self.add_settings_desktop(content_layout)
        self.add_device_control_group(content_layout)
        self.add_glue_dispensing_group(content_layout)
        self.connectDeviceControlCallbacks()
        self.addRobotMotionButtonsGroup(content_layout)

        # Add stretch at the end
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        return scroll_area

    def create_settings_control_groups(self):
        self.spray_group = self.create_spray_settings_group()
        self.motor_group = self.create_motor_settings_group()
        self.general_group = self.create_general_settings_group()

        return self.spray_group, self.motor_group, self.general_group
    def add_settings_desktop(self, parent_layout):
        """Add settings in desktop layout (3 columns)"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)

        groups = self.create_settings_control_groups()

        for group in groups:
            row_layout.addWidget(group)

        parent_layout.addLayout(row_layout)

    def create_spray_settings_group(self):
        """Create spray-related settings group with responsive layout"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.SPRAY_SETTINGS))
        layout = QGridLayout(group)


        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.spray_layout = layout

        # Spray Width
        row = 0
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.SPRAY_WIDTH))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.spray_width_input = self.create_double_spinbox(0.0, 100.0, 5.0, " mm")
        layout.addWidget(self.spray_width_input, row, 1)

        # Spraying Height
        row += 1
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.SPRAYING_HEIGHT))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.spraying_height_input = self.create_double_spinbox(0.0, 500.0, 120.0, " mm")
        layout.addWidget(self.spraying_height_input, row, 1)

        # Fan Speed
        row += 1
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.FAN_SPEED))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.fan_speed_input = self.create_double_spinbox(0.0, 100.0, 100.0, " %")
        layout.addWidget(self.fan_speed_input, row, 1)

        # Time Between Generator and Glue
        row += 1
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.GENERATOR_TO_GLUE_DELAY))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.time_between_generator_and_glue_input = self.create_double_spinbox(0.0, 10.0, 1.0, " s")
        layout.addWidget(self.time_between_generator_and_glue_input, row, 1)


        row+=1
        label = QLabel("Timeout before motion")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.time_before_motion = self.create_double_spinbox(0.0,10,1.0,"s")
        layout.addWidget(self.time_before_motion, row, 1)
        # Set column stretch to make inputs expand
        layout.setColumnStretch(1, 1)

        row += 1
        label = QLabel("Reach Start Threshold")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.reach_pos_thresh = self.create_double_spinbox(0.0, 10, 1.0, "mm")
        layout.addWidget(self.reach_pos_thresh, row, 1)
        # Set column stretch to make inputs expand
        layout.setColumnStretch(1, 1)

        return group

    def create_motor_settings_group(self):
        """Create motor-related settings group with organized subsections"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.MOTOR_SETTINGS))
        main_layout = QVBoxLayout(group)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 25, 20, 20)

        # Forward Motion Settings Subsection
        forward_group = QGroupBox("Forward Motion")
        forward_layout = QGridLayout(forward_group)
        forward_layout.setSpacing(10)
        forward_layout.setContentsMargins(15, 15, 15, 15)

        row = 0
        # Motor Speed (Forward)
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.MOTOR_SPEED))
        label.setWordWrap(True)
        forward_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.motor_speed_input = self.create_double_spinbox(0.0, 100000.0, 3000.0, " Hz")
        forward_layout.addWidget(self.motor_speed_input, row, 1)

        row += 1
        # Forward Ramp Steps
        label = QLabel("Forward Ramp Steps")
        label.setWordWrap(True)
        forward_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.forward_ramp_steps = self.create_spinbox(1, 100, 1, " step(s)")
        forward_layout.addWidget(self.forward_ramp_steps, row, 1)

        row += 1
        # Initial Ramp Speed
        label = QLabel("Initial Ramp Speed")
        label.setWordWrap(True)
        forward_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.initial_ramp_speed = self.create_double_spinbox(0.0, 100000.0, 1000.0, " Hz")
        forward_layout.addWidget(self.initial_ramp_speed, row, 1)

        row += 1
        # Initial Ramp Speed Duration
        label = QLabel("Initial Ramp Speed Duration")
        label.setWordWrap(True)
        forward_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.initial_ramp_speed_duration = self.create_double_spinbox(0.0, 10.0, 1.0, " s")
        forward_layout.addWidget(self.initial_ramp_speed_duration, row, 1)

        forward_layout.setColumnStretch(1, 1)

        # Reverse Motion Settings Subsection
        reverse_group = QGroupBox("Reverse Motion")
        reverse_layout = QGridLayout(reverse_group)
        reverse_layout.setSpacing(10)
        reverse_layout.setContentsMargins(15, 15, 15, 15)

        row = 0
        # Reverse Speed
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.REVERSE_SPEED))
        label.setWordWrap(True)
        reverse_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.speed_reverse_input = self.create_double_spinbox(0.0, 100000.0, 10000.0, " Hz")
        reverse_layout.addWidget(self.speed_reverse_input, row, 1)

        row += 1
        # Reverse Duration
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.REVERSE_DURATION))
        label.setWordWrap(True)
        reverse_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.reverse_duration_input = self.create_double_spinbox(0.0, 100000.0, 1500.0, " s")
        reverse_layout.addWidget(self.reverse_duration_input, row, 1)

        row += 1
        # Reverse Ramp Steps
        label = QLabel("Reverse Ramp Steps")
        label.setWordWrap(True)
        reverse_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.reverse_ramp_steps = self.create_spinbox(1, 100, 1, " step(s)")
        reverse_layout.addWidget(self.reverse_ramp_steps, row, 1)

        reverse_layout.setColumnStretch(1, 1)

        # Add subsections to main layout
        main_layout.addWidget(forward_group)
        main_layout.addWidget(reverse_group)

        # Keep reference to main layout for compatibility
        self.motor_layout = forward_layout  # For any existing code that might reference it
        
        return group

    def create_general_settings_group(self):
        """Create general settings group with responsive layout"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.GENERAL_SETTINGS))
        layout = QGridLayout(group)


        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.general_layout = layout

        # RZ Angle
        row = 0
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.RZ_ANGLE))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.rz_angle_input = self.create_double_spinbox(-180.0, 180.0, 0.0, "°")
        layout.addWidget(self.rz_angle_input, row, 1)

        # generator timeout
        row += 1
        label = QLabel("GENERATOR_TIMEOUT")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.generator_timeout_input = self.create_double_spinbox(0.0, 600.0, 300, " s")
        layout.addWidget(self.generator_timeout_input, row, 1)

        # Spray On
        row += 1
        label = QLabel("Spray On")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.spray_on_toggle = QToggle("")
        self.spray_on_toggle.setMinimumHeight(40)
        layout.addWidget(self.spray_on_toggle, row, 1)

        # Glue Type
        row += 1
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.GLUE_TYPE))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dropdown = QComboBox()
        self.dropdown.setMinimumHeight(40)
        self.dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Populate with glue types from API (supports custom types)
        try:
            glue_type_names = get_all_glue_type_names()
        except Exception as e:
            print(f"Failed to load glue types from API: {e}, using defaults")
            glue_type_names = ["Type A", "Type B", "Type C", "Type D"]

        self.dropdown.addItems(glue_type_names)

        self.dropdown.setCurrentIndex(0)
        layout.addWidget(self.dropdown, row, 1)
        setattr(self, f"Type A_combo", self.dropdown)

        layout.setColumnStretch(1, 1)
        return group

    def add_device_control_group(self, parent_layout):
        """Add device control group with responsive layout"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.DEVICE_CONTROL))

        # Choose layout based on screen size

        main_layout = QHBoxLayout(group)
        main_layout.setSpacing(20)

        main_layout.setContentsMargins(20, 25, 20, 20)
        self.device_control_layout = main_layout

        # Motor Control Section
        motor_control_group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.MOTOR_CONTROL))
        motor_layout = QGridLayout(motor_control_group)
        motor_layout.setSpacing(10)
        motor_layout.setContentsMargins(15, 20, 15, 15)
        self.motor_control_group = motor_control_group

        self.motor_toggles = []

        # Initialize all motor toggles as disabled (loading state)
        for i in range(4):
            motor_toggle = QToggle(f"M{i + 1}")
            motor_toggle.setCheckable(True)
            motor_toggle.setMinimumHeight(35)

            # Initialize as disabled with gray style (loading state)
            motor_toggle.setEnabled(False)
            motor_toggle.setChecked(False)
            motor_toggle.setStyleSheet("QToggle { color: gray; }")  # Gray = loading

            # Responsive grid layout
            motor_layout.addWidget(motor_toggle, i // 2, i % 2)  # Two columns

            setattr(self, f"motor_{i + 1}_toggle", motor_toggle)
            self.motor_toggles.append(motor_toggle)

        # Motor states will be initialized when tab is first shown
        # (see on_tab_selected method)



        # Other Control Section
        other_control_group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.OTHER_SETTINGS))
        other_layout = QVBoxLayout(other_control_group)
        other_layout.setSpacing(10)
        other_layout.setContentsMargins(15, 20, 15, 15)
        self.other_control_group = other_control_group

        # Generator toggle
        generator_toggle = QToggle(self.translator.get(TranslationKeys.GlueSettings.GENERATOR))
        generator_toggle.setCheckable(True)
        generator_toggle.setMinimumHeight(35)

        # Initialize as disabled with gray style (loading state)
        generator_toggle.setEnabled(False)
        generator_toggle.setChecked(False)
        generator_toggle.setStyleSheet("QToggle { color: gray; }")  # Gray = loading

        other_layout.addWidget(generator_toggle)
        setattr(self, "generator_toggle", generator_toggle)
        self.generator_toggle_btn = generator_toggle

        # Fan toggle
        fan_toggle = QToggle(self.translator.get(TranslationKeys.GlueSettings.FAN))
        fan_toggle.setCheckable(True)
        fan_toggle.setMinimumHeight(35)

        # Initialize as disabled with gray style (loading state)
        fan_toggle.setEnabled(False)
        fan_toggle.setChecked(False)
        fan_toggle.setStyleSheet("QToggle { color: gray; }")  # Gray = loading

        other_layout.addWidget(fan_toggle)
        setattr(self, "fan_toggle", fan_toggle)
        self.fan_toggle_btn = fan_toggle

        # Generator and fan states will be initialized when tab is first shown
        # (see on_tab_selected method)

        # Add refresh button for generator state
        refresh_generator_button = MaterialButton("Refresh Generator")
        refresh_generator_button.setMinimumHeight(35)
        refresh_generator_button.clicked.connect(self.refresh_generator_state)
        other_layout.addWidget(refresh_generator_button)

        # Add refresh button for fan state
        refresh_fan_button = MaterialButton("Refresh Fan")
        refresh_fan_button.setMinimumHeight(35)
        refresh_fan_button.clicked.connect(self.refresh_fan_state)
        other_layout.addWidget(refresh_fan_button)

        # Add refresh button for motor states
        refresh_button = MaterialButton("Refresh Motor States")
        refresh_button.setMinimumHeight(35)
        refresh_button.clicked.connect(self.refresh_motor_states)
        motor_layout.addWidget(refresh_button, 2, 0, 1, 2)  # Span across both columns


        # Add all sections to main layout
        main_layout.addWidget(motor_control_group)

        main_layout.addWidget(other_control_group)

        parent_layout.addWidget(group)

    def add_glue_dispensing_group(self, parent_layout):
        """Add glue dispensing-related settings group"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.DISPENSE_GLUE))
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.glue_dispensing_group = group
        self.glue_dispensing_layout = layout

        self.glueDispenseButton = QToggle("")
        self.glueDispenseButton.setMinimumHeight(35)
        layout.addWidget(self.glueDispenseButton)

        parent_layout.addWidget(group)

    def addRobotMotionButtonsGroup(self, parent_layout):
        # Robot motion buttons group
        group = QGroupBox("Robot Motion Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Move to Start
        btn_move_start = MaterialButton("Move to Start")
        btn_move_start.setMinimumHeight(35)
        layout.addWidget(btn_move_start)

        # Move to Login
        btn_move_login = MaterialButton("Move to Login")
        btn_move_login.setMinimumHeight(35)
        layout.addWidget(btn_move_login)

        # Move to Calibration
        btn_move_calib = MaterialButton("Move to Calibration")
        btn_move_calib.setMinimumHeight(35)
        layout.addWidget(btn_move_calib)

        # Clean
        btn_clean = MaterialButton("Clean")
        btn_clean.setMinimumHeight(35)
        layout.addWidget(btn_clean)
        parent_layout.addWidget(group)

    def handleMotorFinished(self, motor_number, state, result):
        # This runs on UI thread — SAFE TO TOUCH WIDGETS
        toggle_btn = getattr(self, f"motor_{motor_number}_toggle", None)

        if result is False:
            self.showToast(f"Error toggling motor {motor_number}")
            if toggle_btn:
                toggle_btn.blockSignals(True)
                toggle_btn.setChecked(not state)
                toggle_btn.blockSignals(False)

        # Always re-enable the toggle button after operation completes
        if toggle_btn:
            toggle_btn.setEnabled(True)

    def toggleMotor(self, motor_number, state):
        # Disable the toggle button immediately to prevent rapid clicks
        toggle_btn = getattr(self, f"motor_{motor_number}_toggle", None)
        if toggle_btn:
            toggle_btn.setEnabled(False)

        # --- Prepare "ui_refs" to pass values to thread safely ---
        ui_refs = {
            "speed": self.motor_speed_input.value,
            "fwd_ramp": self.forward_ramp_steps.value,
            "initial_ramp_speed": self.initial_ramp_speed.value,
            "initial_ramp_time": self.initial_ramp_speed_duration.value,
            "speed_rev": self.speed_reverse_input.value,
            "rev_time": self.reverse_duration_input.value,
            "rev_ramp": self.reverse_ramp_steps.value
        }

        # Use motor-specific thread/worker to avoid conflicts with other motors
        thread = QThread()
        worker = MotorWorker(self.glueSprayService, motor_number, state, ui_refs)
        worker.moveToThread(thread)

        # Store references with motor-specific names to prevent overwriting
        setattr(self, f"motor_{motor_number}_thread", thread)
        setattr(self, f"motor_{motor_number}_worker", worker)

        # Connect signals
        thread.started.connect(worker.run)
        worker.finished.connect(self.handleMotorFinished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Start thread
        thread.start()

    def toggleGenerator(self, state):
        # Disable the toggle button immediately
        toggle_btn = getattr(self, "generator_toggle", None)
        if toggle_btn:
            toggle_btn.setEnabled(False)

        # Start worker thread
        self.generator_thread = QThread()
        self.generator_worker = GeneratorWorker(self.glueSprayService, state)
        self.generator_worker.moveToThread(self.generator_thread)

        # Connect signals
        self.generator_thread.started.connect(self.generator_worker.run)
        self.generator_worker.finished.connect(self.handleGeneratorFinished)
        self.generator_worker.finished.connect(self.generator_thread.quit)
        self.generator_worker.finished.connect(self.generator_worker.deleteLater)
        self.generator_thread.finished.connect(self.generator_thread.deleteLater)

        self.generator_thread.start()

    def handleGeneratorFinished(self, generator_state, result):
        toggle_btn = getattr(self, "generator_toggle", None)

        if result is False or generator_state is None:
            self.showToast("Error toggling generator state")
            if toggle_btn:
                toggle_btn.blockSignals(True)
                # Revert to opposite state if there was an error
                toggle_btn.setChecked(not toggle_btn.isChecked())
                toggle_btn.blockSignals(False)
        else:
            # Operation succeeded - sync with actual generator state after 500ms delay
            if toggle_btn and hasattr(generator_state, 'is_on'):
                actual_state = generator_state.is_on
                toggle_btn.blockSignals(True)
                toggle_btn.setChecked(actual_state)
                toggle_btn.blockSignals(False)

                # Log if there's a mismatch (hardware didn't respond as expected)
                expected_state = self.generator_worker.state if hasattr(self, 'generator_worker') else None
                if expected_state is not None and actual_state != expected_state:
                    print(f"WARNING: Generator state mismatch! Expected: {expected_state}, Actual: {actual_state}")
                    self.showToast(f"Generator may not have responded to command. Current state: {'ON' if actual_state else 'OFF'}")

        # Always re-enable the toggle button after operation completes
        if toggle_btn:
            toggle_btn.setEnabled(True)


    def toggleFan(self, state):
        result = False
        if state:
            print("Fan turned On")
            result = self.glueSprayService.fanOn(self.fan_speed_input.value())
        else:
            print("Fan turned Off")
            result = self.glueSprayService.fanOff()

        if result is False:
            self.showToast("Error toggling fan state")
            toggle_btn = getattr(self, "fan_toggle", None)
            if toggle_btn:
                toggle_btn.blockSignals(True)
                toggle_btn.setChecked(not state)
                toggle_btn.blockSignals(False)

    def toggleGlueDispense(self, state):
        glue_type = getattr(self, f"Type A_combo").currentText()
        print(f"Glue Type: {glue_type}")

        result = False
        if state:
            # Start dispensing using GlueDispatchService
            success, message = self.glueDispatchService.start_glue_dispensing_by_type(
                glue_type=glue_type,
                speed=self.motor_speed_input.value(),
                reverse_time=self.reverse_duration_input.value(),
                speed_reverse=self.speed_reverse_input.value(),
                gen_pump_delay=self.time_between_generator_and_glue_input.value(),
                fan_speed=self.fan_speed_input.value(),
                ramp_steps=self.forward_ramp_steps.value()
            )

            if success:
                print(f"✅ {message}")
                result = True
            else:
                print(f"❌ {message}")
                self.showToast(message)
                result = False
        else:
            # Stop dispensing using GlueDispatchService
            success, message = self.glueDispatchService.stop_glue_dispensing_by_type(
                glue_type=glue_type,
                speed_reverse=self.speed_reverse_input.value(),
                pump_reverse_time=self.reverse_duration_input.value(),
                ramp_steps=self.reverse_ramp_steps.value(),
                pump_gen_delay=self.time_between_generator_and_glue_input.value()
            )

            if success:
                print(f"✅ {message}")
                result = True
            else:
                print(f"❌ {message}")
                self.showToast(message)
                result = False

        # Handle UI feedback
        if result is False:
            toggle_btn = getattr(self, "glueDispenseButton", None)
            if toggle_btn:
                toggle_btn.blockSignals(True)
                toggle_btn.setChecked(not state)
                toggle_btn.blockSignals(False)

    def connectDeviceControlCallbacks(self):
        # Motor toggles
        self.motor_1_toggle.toggled.connect(lambda state: self.toggleMotor(1, state))
        self.motor_2_toggle.toggled.connect(lambda state: self.toggleMotor(2, state))
        self.motor_3_toggle.toggled.connect(lambda state: self.toggleMotor(3, state))
        self.motor_4_toggle.toggled.connect(lambda state: self.toggleMotor(4, state))

        # Generator toggle
        self.generator_toggle.toggled.connect(lambda state: self.toggleGenerator(state))
        self.fan_toggle_btn.toggled.connect(lambda state: self.toggleFan(state))
        self.glueDispenseButton.toggled.connect(lambda state: self.toggleGlueDispense(state))
        
        # Connect all setting widgets to emit unified signals - eliminates callback duplication!
        self._connect_widget_signals()

    def _connect_widget_signals(self):
        """
        Connect all widget signals to emit the unified value_changed_signal.
        This eliminates the need for individual callback connections!
        """
        # Settings widgets mapping (widget -> setting_key)
        widget_mappings = [
            (self.spray_width_input, GlueSettingKey.SPRAY_WIDTH.value),
            (self.spraying_height_input, GlueSettingKey.SPRAYING_HEIGHT.value),
            (self.fan_speed_input, GlueSettingKey.FAN_SPEED.value),
            (self.time_between_generator_and_glue_input, GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value),
            (self.motor_speed_input, GlueSettingKey.MOTOR_SPEED.value),
            (self.reverse_duration_input, GlueSettingKey.REVERSE_DURATION.value),
            (self.speed_reverse_input, GlueSettingKey.SPEED_REVERSE.value),
            (self.rz_angle_input, "RZ Angle"),  # Legacy key
            (self.time_before_motion, GlueSettingKey.TIME_BEFORE_MOTION.value),
            (self.reach_pos_thresh, GlueSettingKey.REACH_START_THRESHOLD.value),
            (self.forward_ramp_steps, GlueSettingKey.FORWARD_RAMP_STEPS.value),
            (self.reverse_ramp_steps, GlueSettingKey.REVERSE_RAMP_STEPS.value),
            (self.initial_ramp_speed, GlueSettingKey.INITIAL_RAMP_SPEED.value),
            (self.initial_ramp_speed_duration, GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value),
        ]
        
        # Connect numeric input widgets
        for widget, setting_key in widget_mappings:
            if hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(
                    lambda value, key=setting_key: self._emit_setting_change(key, value)
                )
        
        # Connect special widgets
        if hasattr(self, 'dropdown') and self.dropdown:
            self.dropdown.currentTextChanged.connect(
                lambda value: self._emit_setting_change(GlueSettingKey.GLUE_TYPE.value, value)
            )
        
        if hasattr(self, 'spray_on_toggle') and self.spray_on_toggle:
            self.spray_on_toggle.toggled.connect(
                lambda value: self._emit_setting_change(GlueSettingKey.SPRAY_ON.value, value)
            )
            
        if hasattr(self, 'generator_timeout_input') and self.generator_timeout_input:
            self.generator_timeout_input.valueChanged.connect(
                lambda value: self._emit_setting_change(GlueSettingKey.GENERATOR_TIMEOUT.value, value)
            )
    
    def _emit_setting_change(self, key: str, value):
        """
        Emit the unified setting change signal.
        
        Args:
            key: The setting key
            value: The new value
        """
        class_name = self.className
        print(f"🔧 Setting changed in {class_name}: {key} = {value}")
        self.value_changed_signal.emit(key, value, class_name)
    
    def connectValueChangeCallbacks(self, callback):
        """
        DEPRECATED: Use value_changed_signal.connect() instead!
        
        This method is kept for backward compatibility but should be migrated to signals.
        
        Migration:
        OLD: layout.connectValueChangeCallbacks(callback)
        NEW: layout.value_changed_signal.connect(callback)
        """
        print("⚠️  WARNING: connectValueChangeCallbacks is deprecated. Use value_changed_signal instead!")
        self.value_changed_signal.connect(callback)


    def connectRobotMotionCallbacks(self, move_start_cb=None, move_login_cb=None, move_calib_cb=None, clean_cb=None,
                                    pickup_cb=None, dropoff_cb=None):
        """
        Connects robot motion button callbacks.
        Each argument is a callable or None.
        pickup_cb and dropoff_cb should be single functions taking gripper_id as an argument.
        """
        # Find the group and layout
        if not hasattr(self, 'robot_motion_buttons_group'):
            for i in range(self.count()):
                widget = self.itemAt(i).widget()
                if isinstance(widget, QWidget):
                    for child in widget.findChildren(QGroupBox):
                        if child.title() == "Robot Motion Controls":
                            self.robot_motion_buttons_group = child
                            break

        group = getattr(self, 'robot_motion_buttons_group', None)
        if not group:
            return

        layout = group.layout()
        if not layout:
            return

        btn_idx = 0

        # Move to Start
        if move_start_cb:
            btn = layout.itemAt(btn_idx).widget()
            btn.clicked.connect(move_start_cb)
        btn_idx += 1

        # Move to Login
        if move_login_cb:
            btn = layout.itemAt(btn_idx).widget()
            btn.clicked.connect(move_login_cb)
        btn_idx += 1

        # Move to Calibration
        if move_calib_cb:
            btn = layout.itemAt(btn_idx).widget()
            btn.clicked.connect(move_calib_cb)
        btn_idx += 1

        # Clean
        if clean_cb:
            btn = layout.itemAt(btn_idx).widget()
            btn.clicked.connect(clean_cb)
        btn_idx += 1

        # # Pickup Tool 0, 1, 2
        # if pickup_cb:
        #     for i in range(3):
        #         btn = layout.itemAt(btn_idx).widget()
        #         btn.clicked.connect(lambda _, idx=i: pickup_cb(idx))
        #         btn_idx += 1
        # else:
        #     btn_idx += 3
        #
        # # Drop Off Tool 0, 1, 2 — ✅ Fixed Here
        # if dropoff_cb:
        #     for i in range(3):
        #         btn = layout.itemAt(btn_idx).widget()
        #         btn.clicked.connect(lambda _, idx=i: dropoff_cb(idx))
        #         btn_idx += 1
        # else:
        #     btn_idx += 3

    def onTimeoutChanged(self, value,callback):
        """Handle timeout value changes."""
        value = value / 60  # Convert seconds to minutes
        self.glueSprayService.generatorTurnOffTimeout = value
        callback(GlueSettingKey.GENERATOR_TIMEOUT.value, value, "GlueSettingsTabLayout")

    def updateValues(self, glueSettings):
        """Updates input field values from glue settings object."""
        self.spray_width_input.setValue(glueSettings.get_spray_width())
        self.spraying_height_input.setValue(glueSettings.get_spraying_height())
        self.fan_speed_input.setValue(glueSettings.get_fan_speed())
        self.time_between_generator_and_glue_input.setValue(glueSettings.get_time_between_generator_and_glue())
        self.motor_speed_input.setValue(glueSettings.get_motor_speed())
        self.reverse_duration_input.setValue(glueSettings.get_steps_reverse())
        self.speed_reverse_input.setValue(glueSettings.get_speed_reverse())
        self.rz_angle_input.setValue(glueSettings.get_rz_angle())
        self.generator_timeout_input.setValue(glueSettings.get_generator_timeout()*60) # Convert minutes to seconds
        self.time_before_motion.setValue(glueSettings.get_time_before_motion())
        self.reach_pos_thresh.setValue(glueSettings.get_reach_position_threshold())
        self.forward_ramp_steps.setValue(glueSettings.get_forward_ramp_steps())
        self.reverse_ramp_steps.setValue(glueSettings.get_reverse_ramp_steps())
        self.initial_ramp_speed.setValue(glueSettings.get_initial_ramp_speed())
        self.initial_ramp_speed_duration.setValue(glueSettings.get_initial_ramp_speed_duration())
        self.spray_on_toggle.setChecked(glueSettings.get_spray_on())
        self.glueSprayService.settings=glueSettings

    def getInputFields(self):
        """Returns the list of input fields."""
        return self.input_fields

    def getSliders(self):
        """Deprecated: Returns input fields for backward compatibility."""
        return self.getInputFields()

    def getValues(self):
        """Returns a dictionary of current values from all input fields."""
        return {
            GlueSettingKey.SPRAY_WIDTH.value: self.spray_width_input.value(),
            GlueSettingKey.SPRAYING_HEIGHT.value: self.spraying_height_input.value(),
            GlueSettingKey.FAN_SPEED.value: self.fan_speed_input.value(),
            GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: self.time_between_generator_and_glue_input.value(),
            GlueSettingKey.MOTOR_SPEED.value: self.motor_speed_input.value(),
            GlueSettingKey.REVERSE_DURATION.value: self.reverse_duration_input.value(),
            GlueSettingKey.SPEED_REVERSE.value: self.speed_reverse_input.value(),
            GlueSettingKey.RZ_ANGLE.value: self.rz_angle_input.value(),
            GlueSettingKey.GLUE_TYPE.value: getattr(self, f"Type A_combo").currentText(),
            GlueSettingKey.GENERATOR_TIMEOUT.value: self.generator_timeout_input.value() / 60 ,  # Convert seconds to minutes
            GlueSettingKey.TIME_BEFORE_MOTION.value: self.time_before_motion.value(),
            GlueSettingKey.INITIAL_RAMP_SPEED.value: self.initial_ramp_speed.value(),
            GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: self.initial_ramp_speed_duration.value(),
            GlueSettingKey.FORWARD_RAMP_STEPS.value: self.forward_ramp_steps.value(),
            GlueSettingKey.REVERSE_RAMP_STEPS.value: self.reverse_ramp_steps.value(),
            GlueSettingKey.REACH_START_THRESHOLD.value: self.reach_pos_thresh.value(),
            GlueSettingKey.SPRAY_ON.value: self.spray_on_toggle.isChecked(),

        }

    def refresh_motor_states(self):
        # Disable all motor toggles while refreshing
        for i in range(4):
            motor_toggle = getattr(self, f"motor_{i + 1}_toggle", None)
            if motor_toggle:
                motor_toggle.setEnabled(False)

        # Start worker in a new thread
        self.refresh_thread = QThread()
        self.refresh_worker = RefreshMotorsWorker(self.glueSprayService)
        self.refresh_worker.moveToThread(self.refresh_thread)

        self.refresh_thread.started.connect(self.refresh_worker.run)
        self.refresh_worker.finished.connect(self.handle_refresh_finished)
        self.refresh_worker.finished.connect(self.refresh_thread.quit)
        self.refresh_worker.finished.connect(self.refresh_worker.deleteLater)
        self.refresh_thread.finished.connect(self.refresh_thread.deleteLater)

        self.refresh_thread.start()

    def handle_refresh_finished(self, motors_healthy):
        """
        Handle the results from RefreshMotorsWorker and update motor toggle buttons.

        Args:
            motors_healthy (dict): Dictionary mapping motor addresses to True/False health state.
        """

        for i in range(4):
            cell_id = i + 1
            try:
                motor_addr = CellHardwareConfig.get_motor_address(cell_id)
            except ValueError:
                # Cell not configured, skip
                continue

            is_healthy = motors_healthy.get(motor_addr, False)

            motor_toggle = getattr(self, f"motor_{i + 1}_toggle", None)
            if motor_toggle:
                # Prevent signals from triggering motor control while updating
                motor_toggle.blockSignals(True)

                if is_healthy:
                    motor_toggle.setEnabled(True)  # Enable toggle for healthy motors
                    motor_toggle.setChecked(False)  # Don't auto-check
                    motor_toggle.setStyleSheet("")  # Reset any previous styling
                else:
                    motor_toggle.setEnabled(False)  # Disable toggle for unhealthy motors
                    motor_toggle.setChecked(False)  # Ensure it's unchecked
                    motor_toggle.setStyleSheet("QPushButton { color: red; }")  # Red styling

                motor_toggle.blockSignals(False)

        # Optionally, show a summary toast
        healthy_count = sum(motors_healthy.values())
        self.showToast(f"Motor states refreshed: {healthy_count}/4 healthy")

    def refresh_generator_state(self):
        # Disable generator toggle while refreshing
        generator_toggle = getattr(self, "generator_toggle", None)
        if generator_toggle:
            generator_toggle.setEnabled(False)

        # Start worker in a new thread
        self.refresh_generator_thread = QThread()
        self.refresh_generator_worker = RefreshGeneratorWorker(self.glueSprayService)
        self.refresh_generator_worker.moveToThread(self.refresh_generator_thread)

        self.refresh_generator_thread.started.connect(self.refresh_generator_worker.run)
        self.refresh_generator_worker.finished.connect(self.handle_refresh_generator_finished)
        self.refresh_generator_worker.finished.connect(self.refresh_generator_thread.quit)
        self.refresh_generator_worker.finished.connect(self.refresh_generator_worker.deleteLater)
        self.refresh_generator_thread.finished.connect(self.refresh_generator_thread.deleteLater)

        self.refresh_generator_thread.start()

    def handle_refresh_generator_finished(self, generator_state):
        """
        Handle results from GeneratorStateWorker and update generator toggle safely.

        Args:
            generator_state: Object containing generator health and state info.
        """
        generator_toggle = getattr(self, "generator_toggle", None)
        if not generator_toggle:
            return

        generator_toggle.blockSignals(True)

        # Generator unhealthy
        if not getattr(generator_state, "is_healthy", False):
            generator_toggle.setEnabled(False)
            generator_toggle.setChecked(False)
            generator_toggle.setStyleSheet("QPushButton { color: red; }")

            # Collect error info
            error_info = []
            if getattr(generator_state, "modbus_errors", None):
                error_info.extend(generator_state.modbus_errors)
            if getattr(generator_state, "error_code", None) and generator_state.error_code != 0:
                error_info.append(f"Error code: {generator_state.error_code}")

            error_text = ", ".join(error_info) if error_info else "Unknown errors"
            self.showToast(f"Generator unhealthy - {error_text}")
            print(f"Generator is unhealthy: {error_text}")

        # Generator healthy
        else:
            generator_toggle.setEnabled(True)
            generator_toggle.setChecked(getattr(generator_state, "is_on", False))
            generator_toggle.setStyleSheet("")

            state_text = "ON" if getattr(generator_state, "is_on", False) else "OFF"
            health_text = "Healthy"
            elapsed_time = getattr(generator_state, "elapsed_time", None)
            time_text = f", Runtime: {elapsed_time:.1f}s" if elapsed_time else ""

            self.showToast(f"Generator: {state_text}, {health_text}{time_text}")
            print(f"Generator state: {generator_state}")

        generator_toggle.blockSignals(False)

    def refresh_fan_state(self):
        """Refresh fan state and update toggle button using new FanState."""
        print("Refreshing fan state...")
        
        try:
            # Get comprehensive fan state using new FanState
            fan_state = self.glueSprayService.getFanState()
            
            fan_toggle = getattr(self, "fan_toggle", None)
            if fan_toggle:
                # Block signals to prevent triggering fan control
                fan_toggle.blockSignals(True)
                
                if not fan_state.is_healthy:
                    # Fan is unhealthy - disable toggle
                    fan_toggle.setEnabled(False)
                    fan_toggle.setChecked(False)
                    fan_toggle.setStyleSheet("QToggle { color: red; }")
                    
                    # Show specific error information
                    error_msg = "Fan unhealthy - disabled"
                    if fan_state.modbus_errors:
                        error_msg += f": {', '.join(fan_state.modbus_errors[:2])}"  # Show first 2 errors
                    
                    self.showToast(error_msg)
                    print(f"Fan unhealthy: {fan_state}")
                else:
                    # Fan is healthy - enable but don't auto-check
                    fan_toggle.setEnabled(True)
                    fan_toggle.setChecked(False)  # Enable but not checked as per requirement
                    fan_toggle.setStyleSheet("")  # Reset to default style
                    
                    # Show detailed state information
                    speed_info = ""
                    if fan_state.speed is not None and fan_state.speed_percentage is not None:
                        speed_info = f" (Speed: {fan_state.speed}, {fan_state.speed_percentage:.1f}%)"
                    
                    state_text = "ON" if fan_state.is_on else "OFF"
                    self.showToast(f"Fan healthy - {state_text}{speed_info}")
                    print(f"Fan state: {fan_state}")
                
                fan_toggle.blockSignals(False)
                
        except Exception as e:
            print(f"Error refreshing fan state: {e}")
            self.showToast(f"Error refreshing fan state: {str(e)}")
            
            # Mark fan as unknown/disabled on error
            fan_toggle = getattr(self, "fan_toggle", None)
            if fan_toggle:
                fan_toggle.blockSignals(True)
                fan_toggle.setEnabled(False)
                fan_toggle.setChecked(False)
                fan_toggle.setStyleSheet("QToggle { color: red; }")
                fan_toggle.blockSignals(False)

    def on_tab_selected(self):
        """
        Called when this tab becomes visible/selected.
        Triggers initialization of device states in background if not already done.
        """
        # Only initialize once
        if hasattr(self, '_states_initialized'):
            print("Device states already initialized, skipping...")
            return

        print("Glue settings tab selected - initializing device states in background...")
        self._states_initialized = True

        # Start all state initializations
        self._init_motor_states()
        self._init_generator_state()
        self._init_fan_state()


    def _init_motor_states(self):
        """Initialize motor states in background without blocking UI."""
        # Start worker in a new thread
        init_thread = QThread()
        init_worker = RefreshMotorsWorker(self.glueSprayService)
        init_worker.moveToThread(init_thread)

        # Store references to prevent premature garbage collection
        self._motor_init_thread = init_thread
        self._motor_init_worker = init_worker

        # Connect signals - use handle_refresh_finished to update toggles
        init_thread.started.connect(init_worker.run)
        init_worker.finished.connect(self.handle_refresh_finished)
        init_worker.finished.connect(init_thread.quit)
        init_worker.finished.connect(init_worker.deleteLater)
        init_thread.finished.connect(init_thread.deleteLater)

        init_thread.start()
        print("Motor state initialization started in background...")

    def _init_generator_state(self):
        """Initialize generator state in background without blocking UI."""
        # Start worker in a new thread
        init_thread = QThread()
        init_worker = RefreshGeneratorWorker(self.glueSprayService)
        init_worker.moveToThread(init_thread)

        # Store references to prevent premature garbage collection
        self._generator_init_thread = init_thread
        self._generator_init_worker = init_worker

        # Connect signals - use handle_refresh_generator_finished to update toggle
        init_thread.started.connect(init_worker.run)
        init_worker.finished.connect(self.handle_refresh_generator_finished)
        init_worker.finished.connect(init_thread.quit)
        init_worker.finished.connect(init_worker.deleteLater)
        init_thread.finished.connect(init_thread.deleteLater)

        init_thread.start()
        print("Generator state initialization started in background...")

    def _init_fan_state(self):
        """Initialize fan state in background without blocking UI."""
        # Since fan state is quick, we can use refresh_fan_state directly
        # But wrap it in a simple thread to avoid blocking
        from PyQt6.QtCore import QTimer
        # Use a timer to defer execution slightly so UI can render first
        QTimer.singleShot(100, self.refresh_fan_state)
        print("Fan state initialization scheduled...")

    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 5)
            toast.show()

    # Signal handlers for Glue Type Management Tab
    def _on_glue_type_added(self, name: str, description: str):
        """Handle when a new custom glue type is added."""
        print(f"Glue type added: {name} - {description}")
        self._refresh_glue_type_dropdown()

    def _on_glue_type_removed(self, name: str):
        """Handle when a custom glue type is removed."""
        print(f"Glue type removed: {name}")
        self._refresh_glue_type_dropdown()

    def _on_glue_type_edited(self, old_name: str, new_name: str, description: str):
        """Handle when a custom glue type is edited."""
        print(f"Glue type edited: {old_name} -> {new_name} - {description}")
        self._refresh_glue_type_dropdown()

    def _refresh_glue_type_dropdown(self):
        """Refresh the glue type dropdown with current types from API."""
        if not hasattr(self, 'dropdown') or self.dropdown is None:
            return

        # Remember current selection
        current_text = self.dropdown.currentText()

        # Clear and repopulate
        self.dropdown.clear()

        try:
            glue_type_names = get_all_glue_type_names()
        except Exception as e:
            print(f"Failed to refresh glue types: {e}, using defaults")
            glue_type_names = ["Type A", "Type B", "Type C", "Type D"]

        self.dropdown.addItems(glue_type_names)

        # Restore selection if still exists
        index = self.dropdown.findText(current_text)
        if index >= 0:
            self.dropdown.setCurrentIndex(index)
        else:
            self.dropdown.setCurrentIndex(0)

        print(f"Glue type dropdown refreshed with {len(glue_type_names)} types")


