import pytest
from unittest.mock import Mock, patch
import numpy as np

from modules.VisionSystem.laser_detection import HeightMeasuringService
from modules.VisionSystem.laser_detection.config import HeightMeasuringConfig
from modules.VisionSystem.laser_detection.storage import LaserCalibrationStorage


@pytest.fixture
def mock_robot_service():
    robot = Mock()
    # Required config
    robot.robot_config.robot_tool = "tool"
    robot.robot_config.robot_user = "user"
    robot.get_current_position = Mock(return_value=[100, 200, 10, 180, 0, 0])
    robot.move_to_position = Mock()
    robot._waitForRobotToReachPosition = Mock()
    return robot


@pytest.fixture
def mock_laser_service():
    laser = Mock()
    # Return dummy detection: mask, bright, closest point
    laser.detect = Mock(return_value=(np.ones((10, 10), np.uint8), (5, 5), (5, 5)))
    return laser


@pytest.fixture
def mock_storage():
    storage = Mock(spec=LaserCalibrationStorage)
    # Provide dummy calibration data with polynomial
    storage.load_calibration = Mock(return_value={
        "polynomial": {
            "coefficients": [0.0, 0.5],  # intercept + coefficient for x
            "intercept": 0.0,
            "degree": 1,
            "mse": 0.01
        },
        "zero_reference_coords": [100, 50],
        "robot_initial_position": [100, 200, 10, 180, 0, 0]
    })

    return storage


def test_initialization_loads_calibration(mock_robot_service, mock_laser_service, mock_storage):
    service = HeightMeasuringService(
        laser_detection_service=mock_laser_service,
        robot_service=mock_robot_service,
        storage=mock_storage
    )
    # Calibration data loaded
    assert service.poly_model is not None
    assert service.poly_transform is not None
    assert service.poly_degree == 1
    assert service.mse == 0.01
    assert service.zero_reference_z == 10
    assert service.reference_xy == [100, 200]
    assert service.zero_reference_coords == [100, 50]


def test_pixel_to_mm_conversion(mock_robot_service, mock_laser_service, mock_storage):
    service = HeightMeasuringService(
        laser_detection_service=mock_laser_service,
        robot_service=mock_robot_service,
        storage=mock_storage
    )
    # pixel_delta = 10 -> check conversion using linear model: y = 0.5*x + 0
    mm = service.pixel_to_mm(10)
    expected_mm = 0.5 * 10 + 0.0
    assert np.isclose(mm, expected_mm)


def test_move_to_with_xy(mock_robot_service, mock_laser_service, mock_storage):
    service = HeightMeasuringService(
        laser_detection_service=mock_laser_service,
        robot_service=mock_robot_service,
        storage=mock_storage
    )
    # Move to explicit coordinates
    service.move_to(x=150, y=250)
    mock_robot_service.move_to_position.assert_called_once()
    args, kwargs = mock_robot_service.move_to_position.call_args
    pos_arg = kwargs.get("position") or args[0]
    assert pos_arg[:3] == [150, 250, 10]  # Z = zero_reference_z
    mock_robot_service._waitForRobotToReachPosition.assert_called_once()


def test_move_to_without_xy_uses_reference(mock_robot_service, mock_laser_service, mock_storage):
    service = HeightMeasuringService(
        laser_detection_service=mock_laser_service,
        robot_service=mock_robot_service,
        storage=mock_storage
    )
    # Move without specifying x/y -> should use reference_xy
    service.move_to()
    args, kwargs = mock_robot_service.move_to_position.call_args
    pos_arg = kwargs.get("position") or args[0]
    assert pos_arg[:2] == service.reference_xy


@patch("time.sleep", return_value=None)
def test_measure_at_returns_height_and_delta(mock_sleep, mock_robot_service, mock_laser_service, mock_storage):
    service = HeightMeasuringService(
        laser_detection_service=mock_laser_service,
        robot_service=mock_robot_service,
        storage=mock_storage
    )
    service.zero_reference_coords = [110, 50]  # zero pixel x = 110
    # Laser detect returns x = 100 -> delta = 10
    mock_laser_service.detect.return_value = (np.ones((10, 10), np.uint8), (5, 5), (100, 5))

    height_mm, delta = service.measure_at()

