"""
Chessboard Found State Handler

Handles the state when a chessboard has been successfully detected.
This is a transition state that prepares for ArUco marker detection.
"""

from modules.utils.custom_logging import log_debug_message
from modules.robot_calibration.states.robot_calibration_states import RobotCalibrationStates


def handle_chessboard_found_state(context) -> RobotCalibrationStates:
    """
    Handle the CHESSBOARD_FOUND state.
    
    This is a simple transition state that confirms chessboard detection
    and prepares the system to look for ArUco markers.
    
    Args:
        context: RobotCalibrationContext containing all calibration state
        
    Returns:
        Next state to transition to
    """
    log_debug_message(
        context.logger_context, 
        f"CHESSBOARD FOUND at {context.chessboard_center_px}, aligning to center..."
    )
    
    # Transition directly to looking for ArUco markers
    # The chessboard detection has already stored the necessary reference points
    return RobotCalibrationStates.LOOKING_FOR_ARUCO_MARKERS