from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QSizePolicy

from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.safety_limits import SafetyLimitsGroup

class SafetySettingsTab(QWidget):
    safety_settings_changed_signal = pyqtSignal(str,object)  # Placeholder for signal
    def __init__(self,parent= None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layout = self.build_layout()
        self.build_ui()
        self.setMaximumHeight(self.sizeHint().height())

    def build_layout(self):
        from PyQt6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout()
        return layout

    def build_ui(self):
        self.safety_group = SafetyLimitsGroup()
        self.safety_group.safety_limits_changed_signal.connect(self.on_value_changed)
        self.layout.addWidget(self.safety_group)
        self.setLayout(self.layout)

    def on_value_changed(self, key, value):
        # Emit the signal when a safety setting is changed
        self.safety_settings_changed_signal.emit(key, value)

    def get_settings(self):
        return self.safety_group.get_safety_limits()

    def update_values(self, safety_limits):
        self.safety_group.update_values(safety_limits)