# Signals
from PyQt6.QtCore import pyqtSignal, QObject


class RobotConfigSignals(QObject):
    """Signal definitions for robot configuration UI"""
    # Robot info signals
    robot_ip_changed = pyqtSignal(str)
    robot_tool_changed = pyqtSignal(int)
    robot_user_changed = pyqtSignal(int)
    tcp_x_offset_changed = pyqtSignal(float)
    tcp_y_offset_changed = pyqtSignal(float)

    # Movement signals
    velocity_changed = pyqtSignal(str, int)  # group_name, value
    acceleration_changed = pyqtSignal(str, int)  # group_name, value

    # Position management signals
    add_point_requested = pyqtSignal(str)  # group_name
    remove_point_requested = pyqtSignal(str)  # group_name
    edit_point_requested = pyqtSignal(str)  # group_name
    move_to_point_requested = pyqtSignal(str)  # group_name

    # Single position signals
    edit_single_position_requested = pyqtSignal(str)  # group_name
    set_current_position_requested = pyqtSignal(str)  # group_name
    move_to_single_position_requested = pyqtSignal(str)  # group_name

    # File operations
    save_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    # Undo/Redo operations
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()

    # Safety limit signals
    safety_limit_changed = pyqtSignal(str, int)  # limit_name, value

    # Global motion settings signals
    global_velocity_changed = pyqtSignal(int)  # value
    global_acceleration_changed = pyqtSignal(int)  # value
    emergency_decel_changed = pyqtSignal(int)  # value
    max_jog_step_changed = pyqtSignal(int)  # value

    # Jog operations
    jog_requested = pyqtSignal(str, str, str, float)  # command, axis, direction, value
    jog_started = pyqtSignal(str)  # direction
    jog_stopped = pyqtSignal(str)  # direction
    save_current_position_as_point = pyqtSignal(str)  # group_name

    # Trajectory execution
    execute_trajectory_requested = pyqtSignal(str)  # group_name

    # Nozzle clean iterations
    nozzle_clean_iterations_changed = pyqtSignal(int)  # iterations_value