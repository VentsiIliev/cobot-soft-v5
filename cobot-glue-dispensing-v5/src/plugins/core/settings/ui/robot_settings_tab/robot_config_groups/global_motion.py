from dataclasses import dataclass

from PyQt6.QtWidgets import QGroupBox, QGridLayout, QLabel, QSizePolicy
from PyQt6.QtWidgets import QGridLayout
from frontend.virtualKeyboard.VirtualKeyboard import FocusSpinBox
from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.base import SettingGroupBox

@dataclass
class GlobalMotionSettings:
    velocity: int
    acceleration: int
    emergency_decel: int
    max_jog_step: int

    def to_dict(self):
        return {
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "emergency_decel": self.emergency_decel,
            "max_jog_step": self.max_jog_step
        }

class GlobalMotionSettingsGroup(SettingGroupBox):
    def __init__(self):
        super().__init__("Global Motion Settings")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layout = self.build_layout()
        self.build_ui()
        self.setMaximumHeight(self.sizeHint().height())

    def build_layout(self):

        layout = QGridLayout()
        return layout

    def build_ui(self):
        # Global Velocity and Acceleration Settings
        global_layout = QGridLayout()

        # Global velocity
        self.global_velocity_label = QLabel("Global Velocity:")
        global_layout.addWidget(self.global_velocity_label, 0, 0)
        self.global_velocity = FocusSpinBox()
        self.global_velocity.setRange(1, 1000)
        self.global_velocity.setValue(100)
        self.global_velocity.setSuffix(" mm/s")
        global_layout.addWidget(self.global_velocity, 0, 1)

        # Global acceleration
        self.global_acceleration_label = QLabel("Global Acceleration:")
        global_layout.addWidget(self.global_acceleration_label, 1, 0)
        self.global_acceleration = FocusSpinBox()
        self.global_acceleration.setRange(1, 1000)
        self.global_acceleration.setValue(100)
        self.global_acceleration.setSuffix(" mm/s²")
        global_layout.addWidget(self.global_acceleration, 1, 1)

        # Emergency deceleration
        self.emergency_decel_label = QLabel("Emergency Deceleration:")
        global_layout.addWidget(self.emergency_decel_label, 2, 0)
        self.emergency_decel = FocusSpinBox()
        self.emergency_decel.setRange(1, 1000)
        self.emergency_decel.setValue(500)
        self.emergency_decel.setSuffix(" mm/s²")
        global_layout.addWidget(self.emergency_decel, 2, 1)

        # Max jog step
        self.max_jog_step_label = QLabel("Max Jog Step:")
        global_layout.addWidget(self.max_jog_step_label, 3, 0)
        self.max_jog_step = FocusSpinBox()
        self.max_jog_step.setRange(1, 100)
        self.max_jog_step.setValue(50)
        self.max_jog_step.setSuffix(" mm")
        global_layout.addWidget(self.max_jog_step, 3, 1)

        self.setLayout(global_layout)
        
        # Add the group to the main layout
        self.layout.addWidget(self)
        self.setLayout(self.layout)

    def get_settings(self)->GlobalMotionSettings:
        return GlobalMotionSettings(
            velocity=self.global_velocity.value(),
            acceleration=self.global_acceleration.value(),
            emergency_decel=self.emergency_decel.value(),
            max_jog_step=self.max_jog_step.value()
        )

    def update_values(self, settings:GlobalMotionSettings):
        self.global_velocity.setValue(settings.velocity)
        self.global_acceleration.setValue(settings.acceleration)
        self.emergency_decel.setValue(settings.emergency_decel)
        self.max_jog_step.setValue(settings.max_jog_step)
