from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QHBoxLayout, 
                             QScrollArea, QGroupBox, QGridLayout, QLineEdit)

from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout
from plugins.core.settings.enums.RobotCalibrationSettingKeys import RobotCalibrationSettingKeys
from frontend.core.utils.localization import get_app_translator


class RobotCalibrationTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    """
    Robot calibration settings tab layout matching existing UI patterns.
    
    Provides UI for configuring robot calibration parameters including:
    - Adaptive movement settings (6 parameters)
    - General calibration settings (z_target, required_marker_ids)
    
    Follows exact same patterns as Camera and Glue settings tabs.
    """
    
    value_changed_signal = pyqtSignal(str, object, str)  # key, value, className

    def __init__(self, parent_widget):
        """
        Initialize robot calibration settings tab.
        
        Args:
            parent_widget: Parent widget for the settings interface
        """
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        
        self.parent_widget = parent_widget
        self.translator = get_app_translator()
        self.translator.language_changed.connect(self.translate)
        
        # Create main content with exact same pattern as existing tabs
        self.create_main_content()
        
        # Connect all widget signals to unified emission pattern
        self._connect_widget_signals()

    def create_main_content(self):
        """Create the main scrollable content area with responsive layout"""
        # Create scroll area - exact same properties as existing tabs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create main content widget - exact same pattern
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)  # Same as GlueSettings
        content_layout.setContentsMargins(20, 20, 20, 20)  # Same as GlueSettings
        
        # Add settings groups
        self.add_calibration_settings_groups(content_layout)
        
        # Add stretch at the end - same as existing
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        self.addWidget(scroll_area)

    def add_calibration_settings_groups(self, parent_layout):
        """Add settings in desktop layout (horizontal row) - exact same pattern"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)  # Same spacing as GlueSettings
        
        groups = self.create_calibration_control_groups()
        for group in groups:
            row_layout.addWidget(group)
        
        parent_layout.addLayout(row_layout)

    def create_calibration_control_groups(self):
        """Create all calibration settings groups"""
        return [
            self.create_adaptive_movement_group(),
            self.create_general_calibration_group()
        ]

    def create_adaptive_movement_group(self):
        """Create adaptive movement settings group with exact styling"""
        self.adaptive_group = QGroupBox("Adaptive Movement Settings")
        layout = QGridLayout(self.adaptive_group)
        layout.setSpacing(15)  # Same as existing
        layout.setContentsMargins(20, 25, 20, 20)  # Same as existing
        
        row = 0
        
        # Min Step MM
        layout.addWidget(QLabel("Min Step:"), row, 0)
        self.min_step_spinbox = self.create_double_spinbox(0.01, 100.0, 0.1, " mm")
        layout.addWidget(self.min_step_spinbox, row, 1)
        row += 1
        
        # Max Step MM  
        layout.addWidget(QLabel("Max Step:"), row, 0)
        self.max_step_spinbox = self.create_double_spinbox(0.1, 500.0, 25.0, " mm")
        layout.addWidget(self.max_step_spinbox, row, 1)
        row += 1
        
        # Target Error MM
        layout.addWidget(QLabel("Target Error:"), row, 0) 
        self.target_error_spinbox = self.create_double_spinbox(0.01, 10.0, 0.25, " mm")
        layout.addWidget(self.target_error_spinbox, row, 1)
        row += 1
        
        # Max Error Ref
        layout.addWidget(QLabel("Max Error Ref:"), row, 0)
        self.max_error_ref_spinbox = self.create_double_spinbox(1.0, 1000.0, 100.0, " mm")
        layout.addWidget(self.max_error_ref_spinbox, row, 1)
        row += 1
        
        # Responsiveness K
        layout.addWidget(QLabel("Responsiveness (K):"), row, 0)
        self.k_spinbox = self.create_double_spinbox(0.1, 10.0, 2.0)
        layout.addWidget(self.k_spinbox, row, 1)
        row += 1
        
        # Derivative Scaling
        layout.addWidget(QLabel("Derivative Scaling:"), row, 0)
        self.derivative_scaling_spinbox = self.create_double_spinbox(0.0, 2.0, 0.5)
        layout.addWidget(self.derivative_scaling_spinbox, row, 1)
        
        return self.adaptive_group

    def create_general_calibration_group(self):
        """Create general calibration settings group"""
        self.general_group = QGroupBox("General Settings")
        layout = QGridLayout(self.general_group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)
        
        # Z Target
        layout.addWidget(QLabel("Z Target:"), 0, 0)
        self.z_target_spinbox = self.create_spinbox(0, 1000, 300, " mm")
        layout.addWidget(self.z_target_spinbox, 0, 1)
        
        # Required Marker IDs - Simple line edit for now (will be enhanced later)
        layout.addWidget(QLabel("Required Marker IDs:"), 1, 0)
        self.required_ids_edit = QLineEdit()
        self.required_ids_edit.setText("0,1,2,3,4,5,6,8")  # Default from JSON
        self.required_ids_edit.setPlaceholderText("Comma-separated marker IDs (e.g., 0,1,2,3)")
        layout.addWidget(self.required_ids_edit, 1, 1)
        
        return self.general_group

    def _connect_widget_signals(self):
        """Connect all widget signals to unified emission pattern"""
        # Use the same component type as parent RobotConfigUI
        component_type = "plugins.core.settings.ui.robot_settings_tab.RobotConfigUI"
        
        # Adaptive movement signals
        self.min_step_spinbox.valueChanged.connect(
            lambda v: self.value_changed_signal.emit(RobotCalibrationSettingKeys.MIN_STEP_MM, v, component_type))
        self.max_step_spinbox.valueChanged.connect(
            lambda v: self.value_changed_signal.emit(RobotCalibrationSettingKeys.MAX_STEP_MM, v, component_type))
        self.target_error_spinbox.valueChanged.connect(
            lambda v: self.value_changed_signal.emit(RobotCalibrationSettingKeys.TARGET_ERROR_MM, v, component_type))
        self.max_error_ref_spinbox.valueChanged.connect(
            lambda v: self.value_changed_signal.emit(RobotCalibrationSettingKeys.MAX_ERROR_REF, v, component_type))
        self.k_spinbox.valueChanged.connect(
            lambda v: self.value_changed_signal.emit(RobotCalibrationSettingKeys.RESPONSIVENESS_K, v, component_type))
        self.derivative_scaling_spinbox.valueChanged.connect(
            lambda v: self.value_changed_signal.emit(RobotCalibrationSettingKeys.DERIVATIVE_SCALING, v, component_type))
        
        # General settings signals  
        self.z_target_spinbox.valueChanged.connect(
            lambda v: self.value_changed_signal.emit(RobotCalibrationSettingKeys.Z_TARGET, v, component_type))
        self.required_ids_edit.textChanged.connect(
            lambda text: self.value_changed_signal.emit(RobotCalibrationSettingKeys.REQUIRED_MARKER_IDS, 
                                                       self._parse_marker_ids(text), component_type))

    def _parse_marker_ids(self, text):
        """Parse comma-separated marker IDs to list of integers"""
        try:
            if not text.strip():
                return []
            return [int(id.strip()) for id in text.split(',') if id.strip().isdigit()]
        except (ValueError, AttributeError):
            return []

    def translate(self):
        """Update UI text based on current language - exact pattern"""
        # Refresh responsive styling
        self.setup_styling()
        
        # Update group titles (will add translation keys later)
        if hasattr(self, 'adaptive_group'):
            self.adaptive_group.setTitle("Adaptive Movement Settings")  # TODO: Add translation
        if hasattr(self, 'general_group'): 
            self.general_group.setTitle("General Settings")  # TODO: Add translation

    def get_current_values(self):
        """Get current values from all widgets - for future use"""
        return {
            RobotCalibrationSettingKeys.MIN_STEP_MM: self.min_step_spinbox.value(),
            RobotCalibrationSettingKeys.MAX_STEP_MM: self.max_step_spinbox.value(),
            RobotCalibrationSettingKeys.TARGET_ERROR_MM: self.target_error_spinbox.value(),
            RobotCalibrationSettingKeys.MAX_ERROR_REF: self.max_error_ref_spinbox.value(),
            RobotCalibrationSettingKeys.RESPONSIVENESS_K: self.k_spinbox.value(),
            RobotCalibrationSettingKeys.DERIVATIVE_SCALING: self.derivative_scaling_spinbox.value(),
            RobotCalibrationSettingKeys.Z_TARGET: self.z_target_spinbox.value(),
            RobotCalibrationSettingKeys.REQUIRED_MARKER_IDS: self._parse_marker_ids(self.required_ids_edit.text())
        }

    def update_values(self, settings_dict):
        """Update widget values from settings dictionary - for future use"""
        adaptive_config = settings_dict.get("adaptive_movement_config", {})
        
        if "min_step_mm" in adaptive_config:
            self.min_step_spinbox.setValue(adaptive_config["min_step_mm"])
        if "max_step_mm" in adaptive_config:
            self.max_step_spinbox.setValue(adaptive_config["max_step_mm"])
        if "target_error_mm" in adaptive_config:
            self.target_error_spinbox.setValue(adaptive_config["target_error_mm"])
        if "max_error_ref" in adaptive_config:
            self.max_error_ref_spinbox.setValue(adaptive_config["max_error_ref"])
        if "k" in adaptive_config:
            self.k_spinbox.setValue(adaptive_config["k"])
        if "derivative_scaling" in adaptive_config:
            self.derivative_scaling_spinbox.setValue(adaptive_config["derivative_scaling"])
            
        if "z_target" in settings_dict:
            self.z_target_spinbox.setValue(settings_dict["z_target"])
        if "required_ids" in settings_dict:
            ids_text = ",".join(map(str, settings_dict["required_ids"]))
            self.required_ids_edit.setText(ids_text)