from dataclasses import dataclass

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QLabel, QSizePolicy

from frontend.virtualKeyboard.VirtualKeyboard import FocusLineEdit, FocusDoubleSpinBox, FocusSpinBox
from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.base import SettingGroupBox

@dataclass
class RobotInfo:
    robot_ip: str
    robot_tool: int
    robot_user: int
    tcp_x_offset: float
    tcp_y_offset: float

    def to_dict(self):
        return {
            "robot_ip": self.robot_ip,
            "robot_tool": self.robot_tool,
            "robot_user": self.robot_user,
            "tcp_x_offset": self.tcp_x_offset,
            "tcp_y_offset": self.tcp_y_offset
        }

class RobotInformationGroup(SettingGroupBox):
    robot_info_changed_signal = pyqtSignal(str,object)
    def __init__(self):
        super().__init__("Robot Info")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layout = self.build_layout()
        self.build_ui()
        self.setMaximumHeight(self.sizeHint().height())

    def build_layout(self):
        layout = QGridLayout()
        return layout

    def build_ui(self):
        self.ip_label = QLabel("IP:")
        self.ip_edit = FocusLineEdit("192.168.58.2")
        self.ip_edit.textChanged.connect(lambda text: self.robot_info_changed_signal.emit("robot_ip", text))
        self.add_setting(self.ip_label, self.ip_edit, 0, 0)

        self.robot_tool_label = QLabel("ROBOT_TOOL:")
        self.tool_edit = FocusSpinBox()
        self.tool_edit.setRange(0, 10)
        self.tool_edit.setValue(0)
        self.tool_edit.valueChanged.connect(lambda value: self.robot_info_changed_signal.emit("robot_tool", value))
        self.add_setting(self.robot_tool_label, self.tool_edit, 1, 0)

        self.robot_user_label = QLabel("ROBOT_USER:")
        self.user_edit = self.get_focus_spin_box(min=0, max=10, current_value=0, decimals=0, suffix="")
        self.user_edit.valueChanged.connect(lambda value: self.robot_info_changed_signal.emit("robot_user", value))
        self.add_setting(self.robot_user_label, self.user_edit, 2, 0)


        self.tcp_x_offset_label = QLabel("TCP X OFFSET:")
        self.tcp_x_offset_edit = self.get_focus_spin_box(min=-1000, max=1000, current_value=0.0, decimals=3, suffix=" mm")
        self.tcp_x_offset_edit.valueChanged.connect(lambda value: self.robot_info_changed_signal.emit("tcp_x_offset", value))
        self.add_setting(self.tcp_x_offset_label, self.tcp_x_offset_edit, 3, 0)

        self.tcp_y_offset_label = QLabel("TCP Y OFFSET:")
        self.tcp_y_offset_edit = self.get_focus_spin_box(min=-1000, max=1000, current_value=0.0, decimals=3, suffix=" mm")
        self.tcp_y_offset_edit.valueChanged.connect(lambda value: self.robot_info_changed_signal.emit("tcp_y_offset", value))
        self.add_setting(self.tcp_y_offset_label, self.tcp_y_offset_edit, 4, 0)

        self.setLayout(self.layout)

    def add_setting(self,label:QLabel,widget,row,col):
        self.layout.addWidget(label,row,col)
        self.layout.addWidget(widget,row,col+1)

    def get_focus_spin_box(self,min,max,current_value,decimals=0,suffix=""):
        spin_box = FocusSpinBox() if decimals == 0 else FocusDoubleSpinBox()
        spin_box.setRange(min, max)
        spin_box.setValue(current_value)
        if decimals > 0:
            spin_box.setDecimals(decimals)
        spin_box.setSuffix(suffix)
        return spin_box

    def get_settings(self)->RobotInfo:
        return RobotInfo(
            robot_ip=self.ip_edit.text(),
            robot_tool=self.tool_edit.value(),
            robot_user=self.user_edit.value(),
            tcp_x_offset=self.tcp_x_offset_edit.value(),
            tcp_y_offset=self.tcp_y_offset_edit.value()
        )

    def update_values(self, robot_info:RobotInfo):
        self.ip_edit.setText(robot_info.robot_ip)
        self.tool_edit.setValue(robot_info.robot_tool)
        self.user_edit.setValue(robot_info.robot_user)
        self.tcp_x_offset_edit.setValue(robot_info.tcp_x_offset)
        self.tcp_y_offset_edit.setValue(robot_info.tcp_y_offset)

