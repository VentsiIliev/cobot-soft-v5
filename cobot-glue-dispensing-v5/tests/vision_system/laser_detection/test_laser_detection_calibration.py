import pytest
import numpy as np
from unittest.mock import Mock, patch

from modules.VisionSystem.laser_detection import LaserDetectionCalibration
from modules.VisionSystem.laser_detection.config import LaserCalibrationConfig
from modules.VisionSystem.laser_detection.storage import LaserCalibrationStorage
from modules.VisionSystem.laser_detection.laser_detection_service import LaserDetectionService
from core.services.robot_service.impl.base_robot_service import RobotService

@pytest.fixture
def mock_robot_service():
    mock = Mock(spec=RobotService)
    # Robot config stub
    mock.robot_config.robot_tool = "tool"
    mock.robot_config.robot_user = "user"
    mock.robot_config.robot_calibration_settings.min_safety_z_mm = 5

    # Add a robot mock with move_liner
    mock.robot = Mock()
    mock.robot.move_liner = Mock()
    return mock

@pytest.fixture
def mock_laser_service():
    return Mock(spec=LaserDetectionService)

@pytest.fixture
def calibration(mock_laser_service, mock_robot_service):
    config = LaserCalibrationConfig()
    storage = Mock(spec=LaserCalibrationStorage)
    return LaserDetectionCalibration(
        laser_service=mock_laser_service,
        robot_service=mock_robot_service,
        config=config,
        storage=storage
    )

# -----------------------------
# Initialization test
# -----------------------------
def test_initialization(calibration):
    assert calibration.laser_service is not None
    assert calibration.robot_service is not None
    assert calibration.config is not None
    assert calibration.storage is not None
    assert calibration.calibration_data == []

# -----------------------------
# Move to initial position
# -----------------------------
def test_move_to_initial_position(calibration, mock_robot_service):
    pos = [0, 0, 10]
    result = calibration.move_to_initial_position(pos)
    assert result is True
    mock_robot_service.robot.move_liner.assert_called_once()
    mock_robot_service._waitForRobotToReachPosition.assert_called_once()

# -----------------------------
# Safety check
# -----------------------------
def test_check_min_safety_limit_pass(calibration, mock_robot_service):
    mock_robot_service.get_current_position.return_value = [0, 0, 10]
    assert calibration.check_min_safety_limit() is True

def test_check_min_safety_limit_fail_none(calibration, mock_robot_service):
    mock_robot_service.get_current_position.return_value = None
    assert calibration.check_min_safety_limit() is False

def test_check_min_safety_limit_fail_too_low(calibration, mock_robot_service):
    mock_robot_service.get_current_position.return_value = [0, 0, 2]
    assert calibration.check_min_safety_limit() is False

# -----------------------------
# Move down by mm
# -----------------------------
def test_move_down_by_mm(calibration, mock_robot_service):
    mock_robot_service.get_current_position.return_value = [0, 0, 10]
    result = calibration.move_down_by_mm(2)
    assert result is True
    mock_robot_service.move_to_position.assert_called_once()
    mock_robot_service._waitForRobotToReachPosition.assert_called_once()

# -----------------------------
# Calibrate method (happy path)
# -----------------------------
@patch("time.sleep", return_value=None)
def test_calibrate_success(mock_sleep, calibration, mock_laser_service, mock_robot_service):
    initial_pos = [0, 0, 10]

    # Robot move and detection mocks
    calibration.move_to_initial_position = Mock(return_value=True)
    calibration.move_down_by_mm = Mock(return_value=True)
    calibration.laser_service.detect = Mock(side_effect=[
        (np.ones((10, 10), np.uint8), (5, 5), (5, 5)),  # zero reference
        (np.ones((10, 10), np.uint8), (6, 5), (6, 5)),  # first step
        (np.ones((10, 10), np.uint8), (7, 5), (7, 5)),  # second step
        (np.ones((10, 10), np.uint8), (8, 5), (8, 5)),  # extra for safety
        (np.ones((10, 10), np.uint8), (9, 5), (9, 5)),  # extra
    ])

    calibration.config.num_iterations = 4  # match number of side_effect frames
    calibration.config.step_size_mm = 1

    # Reduce CV splits for small dataset
    with patch("sklearn.model_selection.cross_val_score") as mock_cv:
        mock_cv.return_value = np.array([-0.1, -0.1, -0.1])  # dummy negative MSE
        result = calibration.calibrate(initial_pos)

    assert result is True
    assert len(calibration.calibration_data) >= 2  # zero + steps
    assert calibration.zero_reference_coords == (5, 5)


# -----------------------------
# Calibrate fails on initial detection
# -----------------------------
@patch("time.sleep", return_value=None)
def test_calibrate_fail_initial_detection(mock_sleep, calibration):
    calibration.move_to_initial_position = Mock(return_value=True)
    calibration.laser_service.detect = Mock(return_value=(None, None, None))
    result = calibration.calibrate([0, 0, 10])
    assert result is False

# -----------------------------
# Polynomial fit
# -----------------------------
def test_pick_best_polynomial_fit(calibration):
    # Setup enough calibration data to satisfy CV
    calibration.calibration_data = [(0, 0), (1, 1), (2, 4), (3, 9), (4, 16), (5, 25)]
    with patch("sklearn.model_selection.cross_val_score") as mock_cv:
        mock_cv.return_value = np.array([-0.01, -0.01, -0.01, -0.01, -0.01])
        calibration.pick_best_polynomial_fit(max_degree=2, save_filename=None)

    assert calibration.poly_model is not None
    assert calibration.poly_degree <= 2
    assert calibration.poly_transform is not None


# -----------------------------
# Save calibration
# -----------------------------
def test_save_calibration(calibration):
    calibration.zero_reference_coords = (1, 2)
    calibration.robot_initial_position = [0, 0, 10]
    calibration.calibration_data = [(0, 0), (1, 1)]
    calibration.poly_model = Mock()
    calibration.poly_model.coef_ = np.array([0.5])
    calibration.poly_model.intercept_ = 0.0
    calibration.poly_degree = 1
    calibration.poly_mse = 0.01
    calibration.storage.save_calibration.return_value = True

    result = calibration.save_calibration("file.json")
    assert result is True
    calibration.storage.save_calibration.assert_called_once()
