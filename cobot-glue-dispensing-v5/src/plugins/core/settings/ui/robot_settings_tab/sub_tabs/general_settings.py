# python
from dataclasses import dataclass

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.global_motion import GlobalMotionSettingsGroup, \
    GlobalMotionSettings
from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.robot_info import RobotInformationGroup, RobotInfo
from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.safety_limits import SafetyLimitsGroup

@dataclass
class GeneralSettings:
    robot_info: RobotInfo
    global_motion: GlobalMotionSettings

    def to_dict(self):
        return {
            "robot_info": self.robot_info.to_dict(),
            "global_motion": self.global_motion.to_dict()
        }

class GeneralRobotSettingsTab(QWidget):
    general_settings_changed_signal = pyqtSignal(str, object)
    def __init__(self,parent=None):
        super().__init__(parent)
        # create and assign layout to the widget so child widgets exist in the UI
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        # build UI elements (creates robot_info_group, safety_group, global_group)
        self.build_ui()
        self.setMaximumHeight(self.sizeHint().height())

    def build_layout(self):
        layout = QVBoxLayout()
        return layout

    def build_ui(self):
        # instantiate groups and add them to the widget layout
        self.robot_info_group = RobotInformationGroup()
        self.robot_info_group.robot_info_changed_signal.connect(
            lambda key, value: self.general_settings_changed_signal.emit(f"robot_info.{key}", value)
        )
        self.layout.addWidget(self.robot_info_group)

        self.global_group = GlobalMotionSettingsGroup()
        self.layout.addWidget(self.global_group)

    def get_settings(self)-> GeneralSettings:
        return GeneralSettings(
            robot_info=self.robot_info_group.get_settings(),
            global_motion=self.global_group.get_settings()
        )

    def update_values(self, settings: GeneralSettings):
        self.robot_info_group.update_values(settings.robot_info)
        self.global_group.update_values(settings.global_motion)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = GeneralRobotSettingsTab()
    window.show()
    sys.exit(app.exec())