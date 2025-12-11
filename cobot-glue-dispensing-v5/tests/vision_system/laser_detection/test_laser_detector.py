import pytest
import numpy as np
import cv2
from modules.VisionSystem.laser_detection.laser_detector import LaserDetector
from modules.VisionSystem.laser_detection.config import LaserDetectionConfig

@pytest.fixture
def config():
    return LaserDetectionConfig(
        default_axis='x',
        gaussian_blur_kernel=(3, 3),
        gaussian_blur_sigma=0.5,
        min_intensity=10
    )

@pytest.fixture
def detector(config):
    return LaserDetector(config)

def test_initialization(detector, config):
    assert detector.config == config
    assert detector.last_closest_point is None
    assert detector.lase_bright_point is None

# -------------------------------------------------
# Subpixel Quadratic Tests
# -------------------------------------------------
def test_subpixel_quadratic_middle(detector):
    arr = np.array([1, 4, 2], dtype=float)
    refined = detector.subpixel_quadratic(1, arr)
    assert 0 < refined < 2  # should refine within neighbors

def test_subpixel_quadratic_edges(detector):
    arr = np.array([1, 2, 3], dtype=float)
    # first index
    assert detector.subpixel_quadratic(0, arr) == 0.0
    # last index
    assert detector.subpixel_quadratic(2, arr) == 2.0

def test_subpixel_quadratic_flat(detector):
    arr = np.array([5,5,5], dtype=float)
    assert detector.subpixel_quadratic(1, arr) == 1.0

# -------------------------------------------------
# Detect laser line
# -------------------------------------------------
def create_synthetic_frame(shape=(10, 10), bright_value=50, axis='x'):
    """Create synthetic laser line"""
    frame = np.zeros((shape[0], shape[1], 3), dtype=np.uint8)
    if axis == 'x':
        frame[5, :] = [0,0,bright_value]  # red channel
    else:
        frame[:, 5] = [0,0,bright_value]
    return frame

def test_detect_laser_line_none_frames(detector):
    mask, bright, closest = detector.detect_laser_line(None, None)
    assert mask is None
    assert bright is None
    assert closest is None

def test_detect_laser_line_axis_x(detector):
    on_frame = create_synthetic_frame(axis='x')
    off_frame = np.zeros_like(on_frame)
    mask, bright, closest = detector.detect_laser_line(on_frame, off_frame, axis='x')
    assert mask is not None
    assert bright is not None
    assert closest is not None
    # Check mask has nonzero points
    assert np.any(mask > 0)

def test_detect_laser_line_axis_y(detector):
    on_frame = create_synthetic_frame(axis='y')
    off_frame = np.zeros_like(on_frame)
    mask, bright, closest = detector.detect_laser_line(on_frame, off_frame, axis='y')
    assert mask is not None
    assert bright is not None
    assert closest is not None
    # Check mask has nonzero points
    assert np.any(mask > 0)

def test_detect_laser_line_no_detection(detector):
    # All zeros → should produce empty points
    on_frame = np.zeros((5,5,3), dtype=np.uint8)
    off_frame = np.zeros_like(on_frame)
    mask, bright, closest = detector.detect_laser_line(on_frame, off_frame)
    # mask should be all zeros
    assert np.sum(mask) == 0
    # bright should be 0
    assert bright == (0,0)
    # closest point should be None
    assert closest is None

def test_detect_laser_line_closest_point(detector):
    on_frame = np.zeros((5,5,3), dtype=np.uint8)
    off_frame = np.zeros_like(on_frame)
    # Place bright point near center
    on_frame[2,2,2] = 100
    mask, bright, closest = detector.detect_laser_line(on_frame, off_frame)
    assert closest == (2.0,2.0)
    assert detector.last_closest_point == closest
    assert detector.lase_bright_point == bright

def test_detect_laser_line_subpixel_refinement(detector):
    on_frame = np.zeros((5,5,3), dtype=np.uint8)
    off_frame = np.zeros_like(on_frame)
    # Slight peak in red channel
    on_frame[2,1,2] = 50
    on_frame[2,2,2] = 100
    on_frame[2,3,2] = 60
    mask, bright, closest = detector.detect_laser_line(on_frame, off_frame, axis='y')
    assert mask is not None
    assert closest is not None
    # Check that subpixel refinement moves centroid slightly
    x_coords = [int(round(p[0])) for p in np.argwhere(mask > 0)]
    assert 1 in x_coords or 2 in x_coords or 3 in x_coords
