from PyQt6.QtCore import pyqtSignal

from frontend.virtualKeyboard.VirtualKeyboard import FocusSpinBox
from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.base import SettingGroupBox
from PyQt6.QtWidgets import QGridLayout, QLabel
from core.model.settings.robotConfig.SafetyLimits import SafetyLimits
from PyQt6.QtCore import pyqtSignal
class SafetyLimitsGroup(SettingGroupBox):
    safety_limits_changed_signal = pyqtSignal(str,object)
    def __init__(self):
        super().__init__("Safety Limits")
        self.layout = self.build_layout()
        self.build_ui()

    def build_layout(self):
        layout = QGridLayout()
        return layout

    def build_ui(self):
        # Initialize safety limit spinboxes
        self.safety_limits = {}

        # Position limits (X, Y, Z in mm)
        position_limits = [
            ("X_MIN", "X Min (mm):", -1000, 1000, -500),
            ("X_MAX", "X Max (mm):", -1000, 1000, 500),
            ("Y_MIN", "Y Min (mm):", -1000, 1000, -500),
            ("Y_MAX", "Y Max (mm):", -1000, 1000, 500),
            ("Z_MIN", "Z Min (mm):", 0, 1000, 100),
            ("Z_MAX", "Z Max (mm):", 0, 1000, 800)
        ]

        # Orientation limits (RX, RY, RZ in degrees)
        orientation_limits = [
            ("RX_MIN", "RX Min (°):", -180, 180, 170),
            ("RX_MAX", "RX Max (°):", -180, 180, 190),
            ("RY_MIN", "RY Min (°):", -180, 180, -10),
            ("RY_MAX", "RY Max (°):", -180, 180, 10),
            ("RZ_MIN", "RZ Min (°):", -180, 180, -180),
            ("RZ_MAX", "RZ Max (°):", -180, 180, 180)
        ]

        # Create position limit controls (left column)
        row = 0
        for key, label, min_val, max_val, default_val in position_limits:
            self.layout.addWidget(QLabel(label), row, 0)
            spinbox = FocusSpinBox()
            spinbox.setRange(min_val, max_val)
            spinbox.setValue(default_val)
            spinbox.setSuffix(" mm" if "mm" in label else " °")
            spinbox.valueChanged.connect(lambda val, k=key: self.safety_limits_changed_signal.emit(k, val))
            self.safety_limits[key] = spinbox
            self.layout.addWidget(spinbox, row, 1)
            row += 1

        # Create orientation limit controls (right column)
        row = 0
        for key, label, min_val, max_val, default_val in orientation_limits:
            self.layout.addWidget(QLabel(label), row, 2)
            spinbox = FocusSpinBox()
            spinbox.setRange(min_val, max_val)
            spinbox.setValue(default_val)
            spinbox.setSuffix(" °")
            spinbox.valueChanged.connect(lambda val, k=key: self.safety_limits_changed_signal.emit(k, val))
            self.safety_limits[key] = spinbox
            self.layout.addWidget(spinbox, row, 3)
            row += 1

        self.setLayout(self.layout)

    def get_safety_limits(self):
        """Retrieve current safety limit values as a dictionary."""
        safety_limits_dict = {key: spinbox.value() for key, spinbox in self.safety_limits.items()}
        safety_limits = SafetyLimits.from_dict(safety_limits_dict)
        print(safety_limits.to_dict())
        return safety_limits

    def update_values(self, safety_limits:SafetyLimits):
        limits_dict = safety_limits.to_dict()
        for key, spinbox in self.safety_limits.items():
            if key in limits_dict:
                spinbox.setValue(limits_dict[key])