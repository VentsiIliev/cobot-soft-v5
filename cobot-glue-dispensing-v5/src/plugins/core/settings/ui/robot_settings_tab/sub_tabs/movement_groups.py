from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QDialog, QDialogButtonBox
)

from frontend.virtualKeyboard.VirtualKeyboard import FocusSpinBox, FocusLineEdit


class MovementGroupType(Enum):
    """Types of movement groups"""
    SINGLE_POSITION = "single_position"  # HOME_POS, LOGIN_POS, CALIBRATION_POS
    MULTI_POSITION = "multi_position"    # NOZZLE CLEAN, SLOT operations
    VELOCITY_ONLY = "velocity_only"      # JOG


@dataclass
class MovementGroupConfig:
    """Configuration for a movement group"""
    name: str
    group_type: MovementGroupType
    has_velocity: bool = True
    has_acceleration: bool = True
    has_iterations: bool = False
    has_trajectory_execution: bool = False
    default_velocity: int = 50
    default_acceleration: int = 30
    default_iterations: int = 1
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary"""
        return {
            "name": self.name,
            "group_type": self.group_type.value,
            "has_velocity": self.has_velocity,
            "has_acceleration": self.has_acceleration,
            "has_iterations": self.has_iterations,
            "has_trajectory_execution": self.has_trajectory_execution,
            "default_velocity": self.default_velocity,
            "default_acceleration": self.default_acceleration,
            "default_iterations": self.default_iterations
        }


class MovementGroupWidget(QGroupBox):
    """Widget for a single movement group"""
    
    # Signals
    velocity_changed = pyqtSignal(str, int)  # group_name, value
    acceleration_changed = pyqtSignal(str, int)  # group_name, value
    iterations_changed = pyqtSignal(str, int)  # group_name, value
    
    # Position signals
    edit_position_requested = pyqtSignal(str)  # group_name
    set_current_position_requested = pyqtSignal(str)  # group_name
    move_to_position_requested = pyqtSignal(str)  # group_name
    
    # Point signals
    add_point_requested = pyqtSignal(str)  # group_name
    remove_point_requested = pyqtSignal(str)  # group_name
    edit_point_requested = pyqtSignal(str)  # group_name
    move_to_point_requested = pyqtSignal(str)  # group_name
    save_current_as_point_requested = pyqtSignal(str)  # group_name
    
    # Trajectory signals
    execute_trajectory_requested = pyqtSignal(str)  # group_name
    
    def __init__(self, config: MovementGroupConfig, parent=None):
        super().__init__(config.name, parent)
        self.config = config
        self.name = config.name
        
        # Widget references
        self.velocity_spinbox: Optional[FocusSpinBox] = None
        self.acceleration_spinbox: Optional[FocusSpinBox] = None
        self.iterations_spinbox: Optional[FocusSpinBox] = None
        self.position_display: Optional[FocusLineEdit] = None
        self.position_list: Optional[QListWidget] = None
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the UI for this movement group"""
        layout = QVBoxLayout()
        
        # Add velocity/acceleration controls
        if self.config.has_velocity or self.config.has_acceleration:
            self.add_velocity_acceleration_controls(layout)
        
        # Add iterations control for specific groups
        if self.config.has_iterations:
            self.add_iterations_control(layout)
        
        # Add position controls based on type
        if self.config.group_type == MovementGroupType.SINGLE_POSITION:
            self.add_single_position_controls(layout)
        elif self.config.group_type == MovementGroupType.MULTI_POSITION:
            self.add_multi_position_controls(layout)
        
        self.setLayout(layout)
    
    def add_velocity_acceleration_controls(self, layout: QVBoxLayout):
        """Add velocity and acceleration controls"""
        vel_acc_layout = QHBoxLayout()
        
        if self.config.has_velocity:
            vel_label = QLabel("Velocity:")
            self.velocity_spinbox = FocusSpinBox()
            self.velocity_spinbox.setRange(0, 1000)
            self.velocity_spinbox.setValue(self.config.default_velocity)
            self.velocity_spinbox.setSuffix(" %")
            
            vel_acc_layout.addWidget(vel_label)
            vel_acc_layout.addWidget(self.velocity_spinbox)
        
        if self.config.has_acceleration:
            acc_label = QLabel("Acceleration:")
            self.acceleration_spinbox = FocusSpinBox()
            self.acceleration_spinbox.setRange(0, 1000)
            self.acceleration_spinbox.setValue(self.config.default_acceleration)
            self.acceleration_spinbox.setSuffix(" %")
            
            vel_acc_layout.addWidget(acc_label)
            vel_acc_layout.addWidget(self.acceleration_spinbox)
        
        vel_acc_layout.addStretch()
        layout.addLayout(vel_acc_layout)
    
    def add_iterations_control(self, layout: QVBoxLayout):
        """Add iterations control"""
        iterations_layout = QHBoxLayout()
        iterations_label = QLabel("Iterations:")
        self.iterations_spinbox = FocusSpinBox()
        self.iterations_spinbox.setRange(1, 100)
        self.iterations_spinbox.setValue(self.config.default_iterations)
        
        iterations_layout.addWidget(iterations_label)
        iterations_layout.addWidget(self.iterations_spinbox)
        iterations_layout.addStretch()
        layout.addLayout(iterations_layout)
    
    def add_single_position_controls(self, layout: QVBoxLayout):
        """Add controls for single position groups"""
        position_label = QLabel(f"{self.name} Position:")
        layout.addWidget(position_label)
        
        position_layout = QHBoxLayout()
        self.position_display = FocusLineEdit()
        self.position_display.setReadOnly(True)
        self.position_display.setPlaceholderText("No position set")
        
        edit_btn = QPushButton("Edit")
        set_current_btn = QPushButton("Set Current")
        move_to_btn = QPushButton("Move To")
        
        # Style buttons
        self.style_button(edit_btn, "#007bff")
        self.style_button(set_current_btn, "#28a745") 
        self.style_button(move_to_btn, "#fd7e14")
        
        position_layout.addWidget(self.position_display)
        position_layout.addWidget(edit_btn)
        position_layout.addWidget(set_current_btn)
        position_layout.addWidget(move_to_btn)
        
        layout.addLayout(position_layout)
        
        # Connect button signals
        edit_btn.clicked.connect(lambda: self.edit_position_requested.emit(self.name))
        set_current_btn.clicked.connect(lambda: self.on_set_current_position_clicked())
        move_to_btn.clicked.connect(lambda: self.move_to_position_requested.emit(self.name))

    def on_set_current_position_clicked(self):
        """Handle set current position button click"""
        print(f"movement_group_widget: on_set_current_position_clicked for {self.name}")
        self.set_current_position_requested.emit(self.name)

    def add_multi_position_controls(self, layout: QVBoxLayout):
        """Add controls for multi-position groups"""
        position_label = QLabel(f"{self.name} Points:")
        layout.addWidget(position_label)
        
        self.position_list = QListWidget()
        self.position_list.setMaximumHeight(120)
        layout.addWidget(self.position_list)
        
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove")
        edit_btn = QPushButton("Edit")
        move_btn = QPushButton("Move To")
        save_current_btn = QPushButton("Save Current")
        
        # Style buttons
        self.style_button(add_btn, "#28a745")
        self.style_button(remove_btn, "#dc3545")
        self.style_button(edit_btn, "#007bff")
        self.style_button(move_btn, "#fd7e14")
        self.style_button(save_current_btn, "#6c757d")
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(move_btn)
        button_layout.addWidget(save_current_btn)
        
        # Add Execute Trajectory button if needed
        if self.config.has_trajectory_execution:
            execute_btn = QPushButton("Execute Trajectory")
            self.style_button(execute_btn, "#17a2b8", bold=True)
            button_layout.addWidget(execute_btn)
            execute_btn.clicked.connect(lambda: self.execute_trajectory_requested.emit(self.name))
            save_current_btn.setVisible(False)
        
        layout.addLayout(button_layout)
        
        # Connect button signals
        add_btn.clicked.connect(lambda: self.add_point_requested.emit(self.name))
        remove_btn.clicked.connect(lambda: self.remove_point_requested.emit(self.name))
        edit_btn.clicked.connect(lambda: self.edit_point_requested.emit(self.name))
        move_btn.clicked.connect(lambda: self.move_to_point_requested.emit(self.name))
        save_current_btn.clicked.connect(lambda: self.on_set_current_position_clicked())
    
    def style_button(self, button: QPushButton, color: str, bold: bool = False):
        """Apply consistent styling to buttons"""
        font_weight = "bold" if bold else "normal"
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: {font_weight};
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}bb;
            }}
        """)
    
    def connect_signals(self):
        """Connect internal widget signals to external signals"""
        if self.velocity_spinbox:
            self.velocity_spinbox.valueChanged.connect(
                lambda value: self.velocity_changed.emit(self.name, value)
            )
        
        if self.acceleration_spinbox:
            self.acceleration_spinbox.valueChanged.connect(
                lambda value: self.acceleration_changed.emit(self.name, value)
            )
        
        if self.iterations_spinbox:
            self.iterations_spinbox.valueChanged.connect(
                lambda value: self.iterations_changed.emit(self.name, value)
            )
    
    def set_velocity(self, value: int):
        """Set velocity value"""
        if self.velocity_spinbox:
            self.velocity_spinbox.setValue(value)
    
    def set_acceleration(self, value: int):
        """Set acceleration value"""
        if self.acceleration_spinbox:
            self.acceleration_spinbox.setValue(value)
    
    def set_iterations(self, value: int):
        """Set iterations value"""
        if self.iterations_spinbox:
            self.iterations_spinbox.setValue(value)
    
    def set_position(self, position: str):
        """Set position for single position groups"""
        if self.position_display:
            self.position_display.setText(position)
    
    def set_points(self, points: List[str]):
        """Set points for multi-position groups"""
        if self.position_list is not None:
            self.position_list.clear()
            for point in points:
                item = QListWidgetItem(point)
                self.position_list.addItem(item)
        else:
            # Auto-fix: Create the position list if it's missing for multi-position groups
            if self.config.group_type == MovementGroupType.MULTI_POSITION:
                self.position_list = QListWidget()
                self.position_list.setMaximumHeight(120)
                # Add to layout if possible
                if hasattr(self, 'layout') and self.layout():
                    self.layout().addWidget(self.position_list)
                # Populate with points
                if self.position_list:
                    self.position_list.clear()
                    for point in points:
                        item = QListWidgetItem(point)
                        self.position_list.addItem(item)
    
    def get_velocity(self) -> int:
        """Get velocity value"""
        return self.velocity_spinbox.value() if self.velocity_spinbox else 0
    
    def get_acceleration(self) -> int:
        """Get acceleration value"""
        return self.acceleration_spinbox.value() if self.acceleration_spinbox else 0
    
    def get_iterations(self) -> int:
        """Get iterations value"""
        return self.iterations_spinbox.value() if self.iterations_spinbox else 1
    
    def get_position(self) -> str:
        """Get position for single position groups"""
        return self.position_display.text() if self.position_display else ""
    
    def get_points(self) -> List[str]:
        """Get points for multi-position groups"""
        if not self.position_list:
            return []
        
        points = []
        for i in range(self.position_list.count()):
            item = self.position_list.item(i)
            if item:
                points.append(item.text())
        return points
    
    def get_selected_point_index(self) -> Optional[int]:
        """Get index of currently selected point"""
        if not self.position_list:
            return None
        return self.position_list.currentRow() if self.position_list.currentItem() else None


class MovementGroupsTab(QWidget):
    """Main tab widget for movement groups"""
    
    # Signals for external communication
    movement_setting_changed = pyqtSignal(str, str, object)  # group_name, setting_name, value
    move_to_point_requested = pyqtSignal(str, str)  # group_name, point_name
    move_to_position_requested = pyqtSignal(str)  # group_name
    def __init__(self, controller_service,parent=None):
        super().__init__(parent)
        self.controller_service = controller_service
        self.movement_groups: Dict[str, MovementGroupWidget] = {}
        self.setup_ui()
        self.create_movement_groups()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
    
    def create_movement_groups(self):
        """Create all movement group widgets"""
        # Define movement group configurations
        configs = [
            MovementGroupConfig(
                name="LOGIN_POS",
                group_type=MovementGroupType.SINGLE_POSITION,
                default_velocity=50,
                default_acceleration=30
            ),
            MovementGroupConfig(
                name="HOME_POS", 
                group_type=MovementGroupType.SINGLE_POSITION,
                default_velocity=60,
                default_acceleration=30
            ),
            MovementGroupConfig(
                name="CALIBRATION_POS",
                group_type=MovementGroupType.SINGLE_POSITION,
                default_velocity=60,
                default_acceleration=30
            ),
            MovementGroupConfig(
                name="JOG",
                group_type=MovementGroupType.VELOCITY_ONLY,
                default_velocity=100,
                default_acceleration=50
            ),
            MovementGroupConfig(
                name="NOZZLE CLEAN",
                group_type=MovementGroupType.MULTI_POSITION,
                has_iterations=True,
                has_trajectory_execution=True,
                default_velocity=80,
                default_acceleration=50,
                default_iterations=4
            ),
            MovementGroupConfig(
                name="TOOL CHANGER",
                group_type=MovementGroupType.MULTI_POSITION,
                has_trajectory_execution=True,
                default_velocity=50,
                default_acceleration=30
            ),
            MovementGroupConfig(
                name="SLOT 0 PICKUP",
                group_type=MovementGroupType.MULTI_POSITION,
                has_trajectory_execution=True,
                default_velocity=30,
                default_acceleration=30
            ),
            MovementGroupConfig(
                name="SLOT 0 DROPOFF",
                group_type=MovementGroupType.MULTI_POSITION,
                has_trajectory_execution=True,
                default_velocity=30,
                default_acceleration=10
            ),
            MovementGroupConfig(
                name="SLOT 1 PICKUP",
                group_type=MovementGroupType.MULTI_POSITION,
                has_trajectory_execution=True,
                default_velocity=30,
                default_acceleration=10
            ),
            MovementGroupConfig(
                name="SLOT 1 DROPOFF",
                group_type=MovementGroupType.MULTI_POSITION,
                has_trajectory_execution=True,
                default_velocity=30,
                default_acceleration=10
            ),
            MovementGroupConfig(
                name="SLOT 4 PICKUP",
                group_type=MovementGroupType.MULTI_POSITION,
                has_trajectory_execution=True,
                default_velocity=30,
                default_acceleration=10
            ),
            MovementGroupConfig(
                name="SLOT 4 DROPOFF",
                group_type=MovementGroupType.MULTI_POSITION,
                has_trajectory_execution=True,
                default_velocity=30,
                default_acceleration=10
            ),
        ]
        
        # Create widgets for each configuration
        for config in configs:
            widget = MovementGroupWidget(config)
            self.movement_groups[config.name] = widget
            self.layout.addWidget(widget)
            
            # Connect signals
            self.connect_movement_group_signals(widget)
    
    def connect_movement_group_signals(self, widget: MovementGroupWidget):
        """Connect signals from a movement group widget"""
        widget.velocity_changed.connect(
            lambda group_name, value: self.movement_setting_changed.emit(group_name, "velocity", value)
        )
        widget.acceleration_changed.connect(
            lambda group_name, value: self.movement_setting_changed.emit(group_name, "acceleration", value)
        )
        widget.iterations_changed.connect(
            lambda group_name, value: self.movement_setting_changed.emit(group_name, "iterations", value)
        )
        
        # Position signals - these will be connected to robot controller in main UI
        widget.edit_position_requested.connect(self.handle_edit_position)
        widget.set_current_position_requested.connect(self.handle_set_current_position)
        widget.move_to_position_requested.connect(self.handle_move_to_position)
        
        widget.add_point_requested.connect(self.handle_add_point)
        widget.remove_point_requested.connect(self.handle_remove_point)
        widget.edit_point_requested.connect(self.handle_edit_point)
        widget.move_to_point_requested.connect(self.handle_move_to_point)
        widget.save_current_as_point_requested.connect(self.handle_save_current_as_point)
        
        widget.execute_trajectory_requested.connect(self.handle_execute_trajectory)
    
    def handle_edit_position(self, group_name: str):
        """Handle edit position request for single-position groups"""
        widget = self.movement_groups.get(group_name)
        if not widget or not widget.position_display:
            QMessageBox.warning(self, "Error", f"Movement group '{group_name}' not found")
            return

        # Get current position
        current_position = widget.get_position()

        # Create edit dialog
        from PyQt6.QtWidgets import QGridLayout, QDoubleSpinBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit {group_name} Position")
        dialog.setModal(True)
        layout = QVBoxLayout()

        # Parse current position if it exists
        position_values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if current_position:
            try:
                # Remove brackets and split
                pos_str = current_position.strip("[]")
                position_values = [float(x.strip()) for x in pos_str.split(",")]
            except (ValueError, AttributeError) as e:
                print(f"Error parsing position: {e}")

        # Create spinboxes for each coordinate
        labels = ["X (mm):", "Y (mm):", "Z (mm):", "RX (deg):", "RY (deg):", "RZ (deg):"]
        spinboxes = []

        grid_layout = QGridLayout()
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-9999.999, 9999.999)
            spinbox.setDecimals(3)
            spinbox.setValue(position_values[i] if i < len(position_values) else 0.0)
            spinbox.setSuffix(" " + ("mm" if i < 3 else "°"))
            spinbox.setMinimumWidth(150)

            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(spinbox, i, 1)
            spinboxes.append(spinbox)

        layout.addLayout(grid_layout)

        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        # Show dialog and update if accepted
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get values from spinboxes
            new_values = [spinbox.value() for spinbox in spinboxes]
            # Format as string
            new_position = f"[{', '.join(str(round(v, 3)) for v in new_values)}]"

            # Update widget
            widget.set_position(new_position)

            # Emit change signal
            self.movement_setting_changed.emit(group_name, "position", new_position)

            QMessageBox.information(self, "Success", f"Updated {group_name} position")

    def handle_set_current_position(self, group_name: str):
        """Handle set current position request for single-position groups"""
        widget = self.movement_groups.get(group_name)
        print(f"handle_set_current_position {group_name}")
        print(f"DEBUG: comparing >{group_name}< to keys:")

        if widget is None:
            raise ValueError(f"No widget found for group '{group_name}'")

        if widget.name is None:
            raise ValueError(f"Widget for group '{group_name}' has no position display -> {widget.position_display}")

        if not self.controller_service:
            QMessageBox.warning(self, "Error", "Robot controller service not available")
            return

        try:
            # Get current robot position
            result = self.controller_service.robot.get_current_position()

            # Check if the operation was successful
            if not result.success:
                QMessageBox.warning(self, "Error", f"Failed to get current robot position: {result.message}")
                return

            # Extract the actual position data from the result
            current_pos = result.data

            if current_pos is None:
                QMessageBox.warning(self, "Error", "Failed to get current robot position: No position data available")
                return

            # Format position as string: "[x, y, z, rx, ry, rz]"
            # Check if current_pos is already a string or a list
            if isinstance(current_pos, str):
                # Already formatted as string, use as-is
                position_str = current_pos
            elif isinstance(current_pos, (list, tuple)):
                # Format list/tuple of numbers into string
                position_str = f"[{', '.join(str(round(float(p), 3)) for p in current_pos)}]"
            else:
                QMessageBox.warning(self, "Error", f"Unexpected position data type: {type(current_pos)}")
                return

            # Update widget
            widget.set_position(position_str)

            # Emit change signal
            self.movement_setting_changed.emit(group_name, "position", position_str)

            QMessageBox.information(
                self,
                "Success",
                f"Set current position for {group_name}:\n{position_str}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to set current position: {str(e)}"
            )
            print(f"Error in handle_set_current_position: {e}")
            import traceback
            traceback.print_exc()

    def handle_move_to_position(self, group_name: str):
        """Handle move to position request"""
        # TODO: Move robot to position

        print(f"[movement_groups] Move to position for group: {group_name}")
        result = None
        if group_name == "HOME_POS":
            result = self.controller_service.robot.move_to_home()
        elif group_name == "LOGIN_POS":
            result = self.controller_service.robot.move_to_login_position()
        elif group_name == "CALIBRATION_POS":
            result = self.controller_service.robot.move_to_calibration_position()
        else:
            QMessageBox.warning(self, "Error", f"Move to position not supported for group '{group_name}'")
            return

        if not result.success:
            print(f"Move to position failed: {result}")
            QMessageBox.warning(self, "Error", f"Failed to move to {group_name}: {result.message}")
            return

    def handle_add_point(self, group_name: str):
        """Handle add point request for multi-position groups"""
        widget = self.movement_groups.get(group_name)

        if widget is None:
            raise ValueError(f"No widget found for group '{group_name}'")

        if widget.position_list is None:
            raise ValueError(f"Widget for group '{group_name}' has no position list -> {widget.position_list}")

        # Create add point dialog
        from PyQt6.QtWidgets import QGridLayout, QDoubleSpinBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Add Point to {group_name}")
        dialog.setModal(True)
        layout = QVBoxLayout()

        # Add info label
        current_count = widget.position_list.count()
        info_label = QLabel(f"Adding new point {current_count} to {group_name}")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Default position values: fetch from current robot position if possible
        position_values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if self.controller_service:
            try:
                result = self.controller_service.robot.get_current_position()
                if result.success and result.data:
                    current_pos = result.data
                    if isinstance(current_pos, (list, tuple)):
                        position_values = [float(p) for p in current_pos]
                    elif isinstance(current_pos, str):
                        pos_str = current_pos.strip("[]")
                        position_values = [float(x.strip()) for x in pos_str.split(",")]
            except Exception as e:
                print(f"Failed to fetch current robot position for pre-fill: {e}")

        # Fallback: if previous points exist, use last point for easier sequential teaching
        if current_count > 0:
            last_point = widget.position_list.item(current_count - 1).text()
            try:
                pos_str = last_point.strip("[]")
                last_values = [float(x.strip()) for x in pos_str.split(",")]
                # Only use last point values if current robot position failed
                if position_values == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]:
                    position_values = last_values
            except Exception as e:
                print(f"Error parsing last point: {e}")

        # Create spinboxes for each coordinate
        labels = ["X (mm):", "Y (mm):", "Z (mm):", "RX (deg):", "RY (deg):", "RZ (deg):"]
        spinboxes = []

        grid_layout = QGridLayout()
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-9999.999, 9999.999)
            spinbox.setDecimals(3)
            spinbox.setValue(position_values[i] if i < len(position_values) else 0.0)
            spinbox.setSuffix(" " + ("mm" if i < 3 else "°"))
            spinbox.setMinimumWidth(150)

            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(spinbox, i, 1)
            spinboxes.append(spinbox)

        layout.addLayout(grid_layout)

        # Add helpful note
        note_label = QLabel("Tip: Use 'Save Current' button to capture the robot's current position")
        note_label.setStyleSheet("color: #666; font-style: italic; margin-top: 5px;")
        layout.addWidget(note_label)

        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        # Show dialog and add if accepted
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get values from spinboxes
            new_values = [spinbox.value() for spinbox in spinboxes]
            # Format as string
            new_point = f"[{', '.join(str(round(v, 3)) for v in new_values)}]"

            # Add to the list
            item = QListWidgetItem(new_point)
            widget.position_list.addItem(item)

            # Select the newly added point
            widget.position_list.setCurrentItem(item)

            # Get all points and emit change signal
            points = widget.get_points()
            self.movement_setting_changed.emit(group_name, "points", points)

            QMessageBox.information(self, "Success", f"Added point {current_count} to {group_name}")

    def handle_remove_point(self, group_name: str):
        """Handle remove point request"""
        widget = self.movement_groups.get(group_name)
        if widget and widget.position_list:
            current_row = widget.position_list.currentRow()
            if current_row >= 0:
                widget.position_list.takeItem(current_row)
                # Emit change signal
                points = widget.get_points()
                self.movement_setting_changed.emit(group_name, "points", points)
            else:
                QMessageBox.warning(self, "No Selection", "Please select a point to remove.")
    
    def handle_edit_point(self, group_name: str):
        """Handle edit point request for multi-position groups"""
        widget = self.movement_groups.get(group_name)
        if not widget or not widget.position_list:
            QMessageBox.warning(self, "Error", f"Movement group '{group_name}' not found")
            return

        # Get selected point
        current_row = widget.position_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a point to edit.")
            return

        # Get current point value
        current_point = widget.position_list.item(current_row).text()

        # Create edit dialog
        from PyQt6.QtWidgets import QGridLayout, QDoubleSpinBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Point {current_row} in {group_name}")
        dialog.setModal(True)
        layout = QVBoxLayout()

        # Add info label
        info_label = QLabel(f"Editing point {current_row} of {widget.position_list.count()}")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Parse current point position
        position_values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if current_point:
            try:
                # Remove brackets and split
                pos_str = current_point.strip("[]")
                position_values = [float(x.strip()) for x in pos_str.split(",")]
            except (ValueError, AttributeError) as e:
                print(f"Error parsing point: {e}")

        # Create spinboxes for each coordinate
        labels = ["X (mm):", "Y (mm):", "Z (mm):", "RX (deg):", "RY (deg):", "RZ (deg):"]
        spinboxes = []

        grid_layout = QGridLayout()
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            spinbox = QDoubleSpinBox()
            spinbox.setRange(-9999.999, 9999.999)
            spinbox.setDecimals(3)
            spinbox.setValue(position_values[i] if i < len(position_values) else 0.0)
            spinbox.setSuffix(" " + ("mm" if i < 3 else "°"))
            spinbox.setMinimumWidth(150)

            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(spinbox, i, 1)
            spinboxes.append(spinbox)

        layout.addLayout(grid_layout)

        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        # Show dialog and update if accepted
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get values from spinboxes
            new_values = [spinbox.value() for spinbox in spinboxes]
            # Format as string
            new_point = f"[{', '.join(str(round(v, 3)) for v in new_values)}]"

            # Update the list item
            widget.position_list.item(current_row).setText(new_point)

            # Get all points and emit change signal
            points = widget.get_points()
            self.movement_setting_changed.emit(group_name, "points", points)

            QMessageBox.information(self, "Success", f"Updated point {current_row} in {group_name}")

    def handle_move_to_point(self, group_name: str):
        """Handle move to point request"""
        widget = self.movement_groups.get(group_name)
        if not widget or not widget.position_list:
            QMessageBox.warning(self, "Error", f"Movement group '{group_name}' not found")
            return

        # Get selected point
        current_row = widget.position_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a point to edit.")
            return

        # Get current point value
        current_point = widget.position_list.item(current_row).text()
        velocity = widget.get_velocity()
        acceleration = widget.get_acceleration()
        print(f"Requesting move to point {current_row} in {group_name}: {current_point}")
        result = self.controller_service.robot.move_to_position(current_point,velocity,acceleration)
        if not result.success:
            QMessageBox.warning(self, "Error", f"Failed to move to point: {result.message}")
        else:
            print(f"Successfully moved to point {current_row} in {group_name}")

    def handle_save_current_as_point(self, group_name: str):
        """Handle save current as point request for multi-position groups"""
        widget = self.movement_groups.get(group_name)
        if not widget or not widget.position_list:
            QMessageBox.warning(self, "Error", f"Movement group '{group_name}' not found")
            return

        if not self.controller_service:
            QMessageBox.warning(self, "Error", "Robot controller service not available")
            return

        try:
            # Get current robot position
            result = self.controller_service.robot.get_current_position()

            # Check if the operation was successful
            if not result.success:
                QMessageBox.warning(self, "Error", f"Failed to get current robot position: {result.message}")
                return

            # Extract the actual position data from the result
            current_pos = result.data

            if current_pos is None:
                QMessageBox.warning(self, "Error", "Failed to get current robot position: No position data available")
                return

            # Format position as string: "[x, y, z, rx, ry, rz]"
            # Check if current_pos is already a string or a list
            if isinstance(current_pos, str):
                # Already formatted as string, use as-is
                position_str = current_pos
            elif isinstance(current_pos, (list, tuple)):
                # Format list/tuple of numbers into string
                position_str = f"[{', '.join(str(round(float(p), 3)) for p in current_pos)}]"
            else:
                QMessageBox.warning(self, "Error", f"Unexpected position data type: {type(current_pos)}")
                return

            # Add to the list
            item = QListWidgetItem(position_str)
            widget.position_list.addItem(item)

            # Select the newly added point
            widget.position_list.setCurrentItem(item)

            # Get all points and emit change signal
            points = widget.get_points()
            self.movement_setting_changed.emit(group_name, "points", points)

            current_count = widget.position_list.count()
            QMessageBox.information(
                self,
                "Success",
                f"Added current position to {group_name} as point {current_count - 1}:\n{position_str}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save current position: {str(e)}"
            )
            print(f"Error in handle_save_current_as_point: {e}")
            import traceback
            traceback.print_exc()

    def handle_execute_trajectory(self, group_name: str):
        """Handle execute trajectory request"""
        # TODO: Execute trajectory for group
        print(f"[movement_groups] Execute trajectory for group: {group_name}")
        if group_name == "NOZZLE CLEAN":
            result = self.controller_service.robot.clean_nozzle()
            if not result.success:
                QMessageBox.warning(self, "Error", f"Failed to execute nozzle clean trajectory: {result.message}")
                return
        elif group_name == "TOOL CHANGER":
            print(f"Executing tool changer trajectory for group: {group_name}")
        elif group_name in ["SLOT 0 PICKUP", "SLOT 0 DROPOFF",
                            "SLOT 1 PICKUP", "SLOT 1 DROPOFF",
                            "SLOT 4 PICKUP", "SLOT 4 DROPOFF"]:
            # split the group name by space to get slot number and action
            parts = group_name.split(" ")
            if len(parts) != 3:
                raise ValueError(f"Invalid slot trajectory group name: {group_name}")

            slot_number = int(parts[1])
            action = parts[2]  # PICKUP or DROPOFF
            if action == "PICKUP":
                result = self.controller_service.robot.pickup_gripper(slot_number)
            elif action == "DROPOFF":
                result = self.controller_service.robot.drop_gripper(slot_number)
            else:
                raise ValueError(f"Invalid slot action: {action}")
        else:
            QMessageBox.warning(self, "Error", f"Execute trajectory not supported for group '{group_name}'")
            return

    def update_values(self, robot_settings):
        """Update all movement group values from robot settings"""
        for group_name, group_data in robot_settings.movement_groups.items():
            if group_name in self.movement_groups:
                widget = self.movement_groups[group_name]
                
                # Update velocity and acceleration
                if hasattr(group_data, 'velocity'):
                    widget.set_velocity(group_data.velocity)
                if hasattr(group_data, 'acceleration'):
                    widget.set_acceleration(group_data.acceleration)
                if hasattr(group_data, 'iterations'):
                    widget.set_iterations(group_data.iterations)
                
                # Update position or points
                if hasattr(group_data, 'position') and group_data.position:
                    widget.set_position(group_data.position)
                elif hasattr(group_data, 'points') and group_data.points:
                    widget.set_points(group_data.points)
    
    def get_movement_group_widget(self, group_name: str) -> Optional[MovementGroupWidget]:
        """Get a specific movement group widget"""
        return self.movement_groups.get(group_name)
    
    def get_all_group_names(self) -> List[str]:
        """Get all movement group names"""
        return list(self.movement_groups.keys())


# Legacy function for backward compatibility
def get_movement_groups_sub_tab(robot_config_ui):
    """Legacy function - creates new class-based MovementGroupsTab and adds to robot_config_ui"""
    movement_groups_tab = MovementGroupsTab(controller_service=robot_config_ui.controller_service)

    # Add to the robot config UI layout
    robot_config_ui.movement_group_tab_layout.addWidget(movement_groups_tab)
    
    # Store reference for access
    robot_config_ui.movement_groups_tab = movement_groups_tab
    
    # Connect signals to robot_config_ui signals
    movement_groups_tab.movement_setting_changed.connect(
        lambda group_name, setting, value: robot_config_ui.value_changed_signal.emit(
            f"movement_groups.{group_name}.{setting}", value, robot_config_ui.className
        )
    )
    
    # Store references for backward compatibility
    robot_config_ui.velocity_acceleration_widgets = {}
    robot_config_ui.position_lists = {}
    
    for group_name, widget in movement_groups_tab.movement_groups.items():
        # Store velocity/acceleration widgets
        if widget.velocity_spinbox or widget.acceleration_spinbox:
            robot_config_ui.velocity_acceleration_widgets[group_name] = {
                "velocity": widget.velocity_spinbox,
                "acceleration": widget.acceleration_spinbox
            }
        
        # Store position widgets
        if widget.position_display:
            robot_config_ui.position_lists[group_name] = widget.position_display
        elif widget.position_list:
            robot_config_ui.position_lists[group_name] = widget.position_list
    
    return movement_groups_tab
