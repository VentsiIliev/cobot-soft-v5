from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

from applications.glue_dispensing_application.settings.enums import GlueSettingKey
from core.model.settings.RobotConfigKey import RobotSettingKey

from frontend.contour_editor.widgets.SegmentSettingsWidget import SegmentSettingsWidget, update_default_settings
from applications.glue_dispensing_application.services.glue.glue_type_migration import get_all_glue_type_names


class GlobalSettingsDialog(QDialog):
    def __init__(self, point_manager_widget, parent=None):
        super().__init__(parent)
        self.point_manager_widget = point_manager_widget
        self.contour_editor = point_manager_widget.contour_editor
        self.setWindowTitle("Global Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(700)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Add title label
        title_label = QLabel("Global Settings - Apply to All Segments")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Prepare input keys for the settings widget
        inputKeys = [key.value for key in GlueSettingKey]
        if GlueSettingKey.GLUE_TYPE.value in inputKeys:
            inputKeys.remove(GlueSettingKey.GLUE_TYPE.value)
        
        inputKeys.append(RobotSettingKey.VELOCITY.value)
        inputKeys.append(RobotSettingKey.ACCELERATION.value)
        
        # Get dynamic glue types from API instead of using enum
        try:
            glue_type_names = get_all_glue_type_names()
        except Exception as e:
            print(f"Failed to load glue types from API: {e}, using defaults")
            glue_type_names = ["Type A", "Type B", "Type C", "Type D"]

        # Pass glue type names as a list instead of enum class
        comboEnums = [[GlueSettingKey.GLUE_TYPE.value, glue_type_names]]

        # Create the global settings widget
        self.segment_settings_widget = SegmentSettingsWidget(
            inputKeys + [GlueSettingKey.GLUE_TYPE.value], 
            comboEnums, 
            parent=self, 
            segment=None, 
            global_settings=True, 
            pointManagerWidget=self.point_manager_widget
        )
        
        layout.addWidget(self.segment_settings_widget)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        apply_button = QPushButton("Apply to All Segments")
        apply_button.clicked.connect(self.apply_settings_to_all_segments)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def apply_settings_to_all_segments(self):
        settings_dict = self.segment_settings_widget.get_global_values()
        
        # Update the default settings for future segments

        update_default_settings(settings_dict)
        
        # Apply to all segments through the point manager
        if self.point_manager_widget:
            self.point_manager_widget.update_all_segments_settings(settings_dict)
        
        self.accept()