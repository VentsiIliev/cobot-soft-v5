from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QLabel, QMessageBox,
    QVBoxLayout, QHBoxLayout, QScrollArea,
    QListWidget, QComboBox, QDialog, QDialogButtonBox, QTabWidget, QListWidgetItem
)

from core.model.settings.robotConfig.SafetyLimits import SafetyLimits
from core.model.settings.robotConfig.robotConfigModel import RobotConfig
from frontend.core.utils.localization import get_app_translator
from frontend.virtualKeyboard.VirtualKeyboard import FocusLineEdit
from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout
from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.global_motion import GlobalMotionSettings
from plugins.core.settings.ui.robot_settings_tab.robot_config_groups.robot_info import RobotInfo
from plugins.core.settings.ui.robot_settings_tab.translate import translate
from plugins.core.settings.ui.robot_settings_tab.signals import RobotConfigSignals
from plugins.core.settings.ui.robot_settings_tab.sub_tabs.general_settings import GeneralRobotSettingsTab, \
    GeneralSettings
from plugins.core.settings.ui.robot_settings_tab.sub_tabs.movement_groups import get_movement_groups_sub_tab, \
    MovementGroupType
from plugins.core.settings.ui.robot_settings_tab.sub_tabs.safety import SafetySettingsTab
from plugins.core.settings.ui.robot_settings_tab.sub_tabs.robot_calibration import RobotCalibrationTabLayout

# Main UI Class
class RobotConfigUI(BaseSettingsTabLayout, QWidget):
    value_changed_signal = pyqtSignal(str, object, str)
    def __init__(self, parent_widget=None, controller_service=None):
        # super().__init__()
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QWidget.__init__(self)
        self.setWindowTitle("Robot Config UI")
        self.resize(1200, 800)
        self.position_lists = {}
        self.velocity_acceleration_widgets = {}
        self.signals = RobotConfigSignals()
        # Initialize translation mapping for UI elements
        self._button_translation_map = {}
        self._group_box_translation_map = {}
        self._label_translation_map = {}

        # Store controller_service for robot operations
        self.controller_service = controller_service

        self.init_ui()
        self.connect_ui_signals()
        self.connect_service_handlers()

        self.translator = get_app_translator()
        self.translator.language_changed.connect(lambda: translate(self))
        translate(self)

    def init_ui(self):
        # Main layout - just the scrollable configuration panel (full width)
        main_layout = QHBoxLayout()

        # Scrollable Configuration panel (full width)
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create main scroll content widget and layout
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        self.tab_widget = QTabWidget()

        self.general_settings_tab = GeneralRobotSettingsTab()
        self.general_settings_tab.general_settings_changed_signal.connect(self.on_settings_changed)
        self.tab_widget.addTab(self.general_settings_tab,"General")

        self.safety_settings_tab = SafetySettingsTab()
        # self.safety_settings_tab.safety_settings_changed_signal.connect(lambda k,v:self.value_changed_signal(k,v,self.className))
        self.tab_widget.addTab(self.safety_settings_tab,"Safety")

        self.movement_group_tab_layout = QVBoxLayout()
        get_movement_groups_sub_tab(self)
        self.tab_widget.addTab(QWidget(), "Movement Groups")
        self.tab_widget.widget(2).setLayout(self.movement_group_tab_layout)
        
        # Create calibration tab with proper layout
        self.calibration_tab_widget = QWidget()
        self.calibration_tab_layout = RobotCalibrationTabLayout(self.calibration_tab_widget)
        self.calibration_tab_layout.value_changed_signal.connect(
            lambda k, v, c: self.value_changed_signal.emit(k, v, c))
        self.calibration_tab_widget.setLayout(self.calibration_tab_layout)
        self.tab_widget.addTab(self.calibration_tab_widget, "Calibration")

        scroll_layout.addWidget(self.tab_widget)

        # Set the scroll content and add to main scroll area
        scroll_content.setLayout(scroll_layout)
        config_scroll.setWidget(scroll_content)
        main_layout.addWidget(config_scroll, 1)  # Full width

        self.setLayout(main_layout)


    def on_settings_changed(self, k, v):
        """Emit value_changed_signal when settings change"""
        self.value_changed_signal.emit(k, v, self.className)

    def connect_service_handlers(self):
        """Connect signals to controller_service methods for robot operations"""
        if not self.controller_service:
            print("Warning: controller_service not available in RobotConfigUI")
            return

        # Connect jog operations
        self.signals.jog_requested.connect(self._handle_jog)

        # Connect position operations
        self.signals.save_current_position_as_point.connect(self._handle_save_current_position)

        # Connect trajectory execution
        self.signals.execute_trajectory_requested.connect(self._handle_execute_trajectory)

    def _handle_jog(self, command, axis, direction, step):
        """Handle jog request through controller_service"""
        if self.controller_service:
            result = self.controller_service.robot.jog_robot(axis, direction, step)
            if not result.success:
                QMessageBox.warning(self, "Jog Error", result.message)

    def _handle_move_to_point(self, group_name):
        """Handle move to point request"""
        # This will be implemented based on movement group logic
        print(f"Move to point in group: {group_name}")

    def _handle_move_to_position(self, group_name):
        """Handle move to single position request"""
        # This will be implemented based on position logic
        print(f"[ROBOT_CONFIG_UI] Move to position: {group_name}")

    def _handle_save_current_position(self, group_name):
        """Handle save current position request"""
        if not self.controller_service:
            QMessageBox.warning(self, "Error", "Controller service not available")
            return

        try:
            # Get current robot position
            result = self.controller_service.robot.get_current_position()
            if not result.success or result.data is None:
                QMessageBox.warning(self, "Error", f"Failed to get current robot position: {result.message}")
                return

            current_pos = result.data

            # Format position as string
            if isinstance(current_pos, str):
                position_str = current_pos
            elif isinstance(current_pos, (list, tuple)):
                position_str = f"[{', '.join(str(round(float(p), 3)) for p in current_pos)}]"
            else:
                QMessageBox.warning(self, "Error", f"Unexpected position data type: {type(current_pos)}")
                return

            # Find the movement group widget
            if not hasattr(self, 'movement_groups_tab') or not self.movement_groups_tab:
                QMessageBox.warning(self, "Error", "Movement groups not initialized")
                return

            widget = self.movement_groups_tab.movement_groups.get(group_name)
            if not widget:
                QMessageBox.warning(self, "Error", f"Movement group '{group_name}' not found")
                return

            # Single-position group: override existing position
            if widget.config.group_type == MovementGroupType.SINGLE_POSITION:
                widget.set_position(position_str)
                self.value_changed_signal.emit(
                    f"movement_groups.{group_name}.position",
                    position_str,
                    self.className
                )
                QMessageBox.information(
                    self,
                    "Success",
                    f"Updated position for {group_name}:\n{position_str}"
                )

            # Multi-position group: append new point
            elif widget.config.group_type == MovementGroupType.MULTI_POSITION:
                # Get existing points
                existing_points = widget.get_points()
                # Append new position
                existing_points.append(position_str)
                # Clear and repopulate the list
                widget.position_list.clear()
                for point in existing_points:
                    widget.position_list.addItem(point)
                # Select the newly added point
                widget.position_list.setCurrentRow(len(existing_points) - 1)
                widget.position_list.scrollToItem(widget.position_list.currentItem(),
                                                  hint=QListWidget.PositionAtCenter)
                # Emit value changed signal
                self.value_changed_signal.emit(
                    f"movement_groups.{group_name}.points",
                    existing_points,
                    self.className
                )
                QMessageBox.information(
                    self,
                    "Success",
                    f"Added current position to {group_name} as point {len(existing_points) - 1}:\n{position_str}"
                )


        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save position: {str(e)}"
            )
            import traceback
            traceback.print_exc()

    def _handle_execute_trajectory(self, group_name):
        """Handle trajectory execution request"""
        # This will be implemented based on trajectory logic
        print(f"Execute trajectory: {group_name}")

    def connect_ui_signals(self):
        """Connect UI element signals to custom signals"""
        # Connect general settings to value_changed_signal
        # This follows the same pattern as camera and glue settings
        self.general_settings_tab.general_settings_changed_signal.connect(
            lambda k, v: self.value_changed_signal.emit(k, v, self.className)
        )

        # Robot info signals (also emit to value_changed_signal)
        self.general_settings_tab.robot_info_group.ip_edit.textChanged.connect(
            lambda value: (self.signals.robot_ip_changed.emit(value),
                          self.value_changed_signal.emit("robot_ip", value, self.className))
        )
        self.general_settings_tab.robot_info_group.tool_edit.valueChanged.connect(
            lambda value: (self.signals.robot_tool_changed.emit(value),
                          self.value_changed_signal.emit("robot_tool", value, self.className))
        )
        self.general_settings_tab.robot_info_group.user_edit.valueChanged.connect(
            lambda value: (self.signals.robot_user_changed.emit(value),
                          self.value_changed_signal.emit("robot_user", value, self.className))
        )
        self.general_settings_tab.robot_info_group.tcp_x_offset_edit.valueChanged.connect(
            lambda value: (self.signals.tcp_x_offset_changed.emit(value),
                          self.value_changed_signal.emit("tcp_x_offset", value, self.className))
        )
        self.general_settings_tab.robot_info_group.tcp_y_offset_edit.valueChanged.connect(
            lambda value: (self.signals.tcp_y_offset_changed.emit(value),
                          self.value_changed_signal.emit("tcp_y_offset", value, self.className))
        )

        # Velocity/acceleration signals (also emit to value_changed_signal)
        for group_name, widgets in self.velocity_acceleration_widgets.items():
            widgets["velocity"].valueChanged.connect(
                lambda value, gn=group_name: (
                    self.signals.velocity_changed.emit(gn, value),
                    self.value_changed_signal.emit(f"movement_groups.{gn}.velocity", value, self.className)
                )
            )
            widgets["acceleration"].valueChanged.connect(
                lambda value, gn=group_name: (
                    self.signals.acceleration_changed.emit(gn, value),
                    self.value_changed_signal.emit(f"movement_groups.{gn}.acceleration", value, self.className)
                )
            )

        # Safety limit signals (also emit to value_changed_signal)
        for limit_name, spinbox in self.safety_settings_tab.safety_group.safety_limits.items():
            spinbox.valueChanged.connect(
                lambda value, ln=limit_name: (
                    self.signals.safety_limit_changed.emit(ln, value),
                    self.value_changed_signal.emit(f"safety_limits.{ln.lower()}", value, self.className)
                )
            )

        # Global motion settings signals (also emit to value_changed_signal)
        self.general_settings_tab.global_group.global_velocity.valueChanged.connect(
            lambda value: (
                self.signals.global_velocity_changed.emit(value),
                self.value_changed_signal.emit("global_motion_settings.global_velocity", value, self.className)
            )
        )
        self.general_settings_tab.global_group.global_acceleration.valueChanged.connect(
            lambda value: (
                self.signals.global_acceleration_changed.emit(value),
                self.value_changed_signal.emit("global_motion_settings.global_acceleration", value, self.className)
            )
        )
        self.general_settings_tab.global_group.emergency_decel.valueChanged.connect(
            lambda value: (
                self.signals.emergency_decel_changed.emit(value),
                self.value_changed_signal.emit("global_motion_settings.emergency_decel", value, self.className)
            )
        )
        self.general_settings_tab.global_group.max_jog_step.valueChanged.connect(
            lambda value: (
                self.signals.max_jog_step_changed.emit(value),
                self.value_changed_signal.emit("global_motion_settings.max_jog_step", value, self.className)
            )
        )


        # Connect nozzle clean iterations signal
        if hasattr(self, 'nozzle_clean_iterations'):
            self.nozzle_clean_iterations.valueChanged.connect(self.signals.nozzle_clean_iterations_changed.emit)

    def on_jog_save_point(self):
        """Handle save point request from jog widget"""
        # Create dialog to select target group
        dialog = QDialog(self)
        dialog.setWindowTitle("Save Current Position")
        dialog.setModal(True)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select target group to save current position:")) # TODO TRANSLATE

        combo = QComboBox()

        # Use the new movement_groups_tab if available
        if hasattr(self, 'movement_groups_tab') and self.movement_groups_tab:
            # Add all movement groups that can accept positions
            for group_name, widget in self.movement_groups_tab.movement_groups.items():
                # Include both single-position and multi-position groups
                # Exclude only velocity-only groups (like JOG)
                if widget.position_display is not None or widget.position_list is not None:
                    combo.addItem(group_name)
        else:
            # Fallback to legacy position_lists dictionary
            for group_name in self.position_lists.keys():
                widget = self.position_lists[group_name]
                if isinstance(widget, QListWidget):  # Multi-position groups
                    combo.addItem(group_name)
                elif isinstance(widget, FocusLineEdit):  # Single-position groups (LOGIN_POS, HOME_POS, CALIBRATION_POS)
                    combo.addItem(group_name)

        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted and combo.currentText():
            selected_group = combo.currentText()
            self.signals.save_current_position_as_point.emit(selected_group)

    def updateValues(self,robot_settings:RobotConfig):
        self.update_general_settings_tab(robot_settings)
        self.update_safety_settings_tab(robot_settings)
        self.update_movement_groups_tab(robot_settings)
        print(f"[RobotConfigUI] UI values updated from RobotConfig model")

    def update_general_settings_tab(self,robot_settings:RobotConfig):
        robot_info = RobotInfo(
            robot_ip=robot_settings.robot_ip,
            robot_tool=robot_settings.robot_tool,
            robot_user=robot_settings.robot_user,
            tcp_x_offset=robot_settings.tcp_x_offset,
            tcp_y_offset = robot_settings.tcp_y_offset)

        global_motion_settings = GlobalMotionSettings(
            velocity=robot_settings.global_motion_settings.global_velocity,
            acceleration=robot_settings.global_motion_settings.global_acceleration,
            emergency_decel=robot_settings.global_motion_settings.emergency_decel,
            max_jog_step=robot_settings.global_motion_settings.max_jog_step
        )

        general_values = GeneralSettings(
            robot_info=robot_info,
            global_motion= global_motion_settings
        )

        self.general_settings_tab.update_values(general_values)

    def update_safety_settings_tab(self,robot_settings:RobotConfig):
        safety_limits = SafetyLimits(
            x_min=robot_settings.safety_limits.x_min,
            x_max=robot_settings.safety_limits.x_max,
            y_min=robot_settings.safety_limits.y_min,
            y_max=robot_settings.safety_limits.y_max,
            z_min=robot_settings.safety_limits.z_min,
            z_max=robot_settings.safety_limits.z_max,
            rx_min=robot_settings.safety_limits.rx_min,
            rx_max=robot_settings.safety_limits.rx_max,
            ry_min=robot_settings.safety_limits.ry_min,
            ry_max=robot_settings.safety_limits.ry_max,
            rz_min=robot_settings.safety_limits.rz_min,
            rz_max=robot_settings.safety_limits.rz_max
        )

        self.safety_settings_tab.update_values(safety_limits)

    def update_movement_groups_tab(self,robot_settings:RobotConfig):
        # Use the new MovementGroupsTab update method if available
        if hasattr(self, 'movement_groups_tab'):
            self.movement_groups_tab.update_values(robot_settings)
        
        # Legacy support for old approach
        for group_name, group_data in robot_settings.movement_groups.items():
            if group_name in self.position_lists:
                widget = self.position_lists[group_name]

                if isinstance(widget, FocusLineEdit):
                    widget.setText(group_data.position or "")
                elif isinstance(widget, QListWidget):
                    widget.clear()
                    for point in group_data.points:
                        item = QListWidgetItem(point)
                        widget.addItem(item)
