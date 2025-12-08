from modules.VisionSystem.laser_detection.height_measuring import HeightMeasuringService
from modules.robot_calibration.RobotCalibrationContext import RobotCalibrationContext
from modules.robot_calibration.states.robot_calibration_states import RobotCalibrationStates


def handle_height_sample_state(context:RobotCalibrationContext):
    print("Handling HEIGHT_SAMPLE state...")
    hms = context.height_measuring_service
    rs = context.calibration_robot_controller.robot_service
    current_position = rs.get_current_position()
    height_mm,pixel_data = hms.measure_at(current_position[0], current_position[1])
    print(f"Measured height at position {current_position}: {height_mm} mm")
    # Placeholder logic for handling height sampling
    return RobotCalibrationStates.DONE