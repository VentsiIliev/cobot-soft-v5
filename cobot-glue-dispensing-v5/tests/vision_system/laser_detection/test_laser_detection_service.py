import pytest
import numpy as np
from unittest.mock import Mock, patch

from modules.VisionSystem.laser_detection.laser_detection_service import LaserDetectionService
from modules.VisionSystem.laser_detection.laser_detector import LaserDetector
from modules.VisionSystem.laser_detection.config import LaserDetectionConfig
from modules.shared.tools.Laser import Laser


@pytest.fixture
def mock_detector():
    return Mock(spec=LaserDetector)


@pytest.fixture
def mock_laser():
    return Mock(spec=Laser)


@pytest.fixture
def mock_vision_service():
    return Mock()


@pytest.fixture
def detection_service(mock_detector, mock_laser, mock_vision_service):
    config = LaserDetectionConfig()
    return LaserDetectionService(detector=mock_detector,
                                 laser=mock_laser,
                                 vision_service=mock_vision_service,
                                 config=config)


@pytest.fixture
def dummy_frame():
    # 10x10 RGB image
    return np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)


# -----------------------------
# Laser toggle tests
# -----------------------------
def test_toggle_laser_on_off(detection_service, mock_laser):
    # Initially off
    detection_service.laser_status = 0
    detection_service.toggle_laser()
    mock_laser.turnOn.assert_called_once()
    assert detection_service.laser_status == 1

    # Toggle again -> off
    detection_service.toggle_laser()
    mock_laser.turnOff.assert_called_once()
    assert detection_service.laser_status == 0


# -----------------------------
# Frame update tests
# -----------------------------
def test_update_frame_on_off(detection_service, dummy_frame):
    # Laser ON
    detection_service.laser_status = 1
    detection_service.update_frame(dummy_frame)
    np.testing.assert_array_equal(detection_service.last_on_frame, dummy_frame)

    # Laser OFF
    detection_service.laser_status = 0
    detection_service.update_frame(dummy_frame)
    np.testing.assert_array_equal(detection_service.last_off_frame, dummy_frame)


# -----------------------------
# Detection tests
# -----------------------------
@patch("time.sleep", return_value=None)  # avoid delays
def test_detect_success(mock_sleep, detection_service, dummy_frame, mock_detector, mock_vision_service):
    samples = detection_service.config.detection_samples

    # Prepare vision service to return frames
    frames = [dummy_frame for _ in range(samples)]
    mock_vision_service.latest_frame = dummy_frame

    # Mock detector to return a valid point
    mock_detector.detect_laser_line.return_value = (np.ones((10, 10), np.uint8), (5, 5), (5, 5))

    mask, bright, closest = detection_service.detect()

    # Should call detector once
    mock_detector.detect_laser_line.assert_called_once()
    assert mask is not None
    assert bright == (5, 5)
    assert closest == (5, 5)
    np.testing.assert_array_equal(detection_service.last_on_frame, dummy_frame)
    np.testing.assert_array_equal(detection_service.last_off_frame, dummy_frame)


@patch("time.sleep", return_value=None)
def test_detect_failure_retries(mock_sleep, detection_service, dummy_frame, mock_detector, mock_vision_service):
    samples = detection_service.config.detection_samples

    # Vision service always returns frames
    mock_vision_service.latest_frame = dummy_frame

    # Detector fails to detect (closest is None)
    mock_detector.detect_laser_line.return_value = (np.ones((10, 10), np.uint8), (5, 5), None)

    mask, bright, closest = detection_service.detect()

    # Should return None after max retries
    assert mask is None
    assert bright is None
    assert closest is None


@patch("time.sleep", return_value=None)
def test_detect_insufficient_frames(mock_sleep, detection_service, dummy_frame, mock_detector, mock_vision_service):
    # Vision service returns None for frames -> insufficient frames
    mock_vision_service.latest_frame = None

    mask, bright, closest = detection_service.detect()

    # Detection should fail after retries
    assert mask is None
    assert bright is None
    assert closest is None


# -----------------------------
# Config override test
# -----------------------------
def test_custom_config_passed(mock_detector, mock_laser, mock_vision_service):
    custom_config = LaserDetectionConfig()
    custom_config.default_axis = 'y'
    service = LaserDetectionService(mock_detector, mock_laser, mock_vision_service, config=custom_config)
    assert service.config.default_axis == 'y'
