"""
CameraSettingKeys - Enumeration of all camera setting keys.

Defines all valid setting keys for camera configuration including:
- Core camera properties (width, height, index)
- Contour detection settings  
- Preprocessing parameters
- Calibration settings
- Brightness control
- ArUco detection settings

Used for type safety and preventing invalid setting key usage.
"""

from enum import Enum


class CameraSettingKeys(str, Enum):
    """
    Enumeration of all valid camera setting keys.
    
    Inherits from str to allow direct string comparison while providing
    type safety and IDE autocompletion support.
    """
    
    # ========== CORE CAMERA SETTINGS ==========
    
    CAMERA_INDEX = "camera_index"
    """Camera device index (0, 1, 2, etc.)"""
    
    WIDTH = "camera_width" 
    """Camera capture width in pixels"""
    
    HEIGHT = "camera_height"
    """Camera capture height in pixels"""
    
    SKIP_FRAMES = "skip_frames"
    """Number of frames to skip between captures"""
    
    CAPTURE_POS_OFFSET = "capture_pos_offset"
    """Position offset for capture in mm"""
    
    # ========== CONTOUR DETECTION SETTINGS ==========
    
    CONTOUR_DETECTION = "contour_detection_enabled"
    """Enable/disable contour detection"""
    
    DRAW_CONTOURS = "draw_contours"
    """Enable/disable contour visualization"""
    
    THRESHOLD = "threshold"
    """Primary threshold value for contour detection (0-255)"""
    
    THRESHOLD_PICKUP_AREA = "threshold_pickup_area"
    """Secondary threshold for pickup area detection (0-255)"""
    
    EPSILON = "epsilon"
    """Epsilon value for contour approximation (0.0-1.0)"""
    
    MIN_CONTOUR_AREA = "min_contour_area"
    """Minimum contour area to consider (pixels)"""
    
    MAX_CONTOUR_AREA = "max_contour_area"
    """Maximum contour area to consider (pixels)"""
    
    # ========== PREPROCESSING SETTINGS ==========
    
    GAUSSIAN_BLUR = "gaussian_blur_enabled"
    """Enable/disable Gaussian blur preprocessing"""
    
    BLUR_KERNEL_SIZE = "blur_kernel_size"
    """Kernel size for Gaussian blur (odd numbers 1-31)"""
    
    THRESHOLD_TYPE = "threshold_type"
    """Type of thresholding (binary, binary_inv, trunc, tozero, tozero_inv)"""
    
    DILATE_ENABLED = "dilate_enabled"
    """Enable/disable dilation morphological operation"""
    
    DILATE_KERNEL_SIZE = "dilate_kernel_size"
    """Kernel size for dilation (1-31)"""
    
    DILATE_ITERATIONS = "dilate_iterations"
    """Number of dilation iterations (0-20)"""
    
    ERODE_ENABLED = "erode_enabled"
    """Enable/disable erosion morphological operation"""
    
    ERODE_KERNEL_SIZE = "erode_kernel_size"
    """Kernel size for erosion (1-31)"""
    
    ERODE_ITERATIONS = "erode_iterations"
    """Number of erosion iterations (0-20)"""
    
    # ========== CALIBRATION SETTINGS ==========
    
    CHESSBOARD_WIDTH = "chessboard_width"
    """Number of internal corners in chessboard width"""
    
    CHESSBOARD_HEIGHT = "chessboard_height"
    """Number of internal corners in chessboard height"""
    
    SQUARE_SIZE_MM = "square_size_mm"
    """Size of chessboard squares in millimeters"""
    
    CALIBRATION_SKIP_FRAMES = "calibration_skip_frames"
    """Number of frames to skip during calibration capture"""
    
    # ========== BRIGHTNESS CONTROL SETTINGS ==========
    
    BRIGHTNESS_AUTO = "brightness_auto_enabled"
    """Enable/disable automatic brightness control"""
    
    BRIGHTNESS_KP = "brightness_kp"
    """Proportional gain for brightness PID control"""
    
    BRIGHTNESS_KI = "brightness_ki"
    """Integral gain for brightness PID control"""
    
    BRIGHTNESS_KD = "brightness_kd"
    """Derivative gain for brightness PID control"""
    
    TARGET_BRIGHTNESS = "target_brightness"
    """Target brightness value for auto control (0-255)"""
    
    # ========== ARUCO DETECTION SETTINGS ==========
    
    ARUCO_ENABLED = "aruco_detection_enabled"
    """Enable/disable ArUco marker detection"""
    
    ARUCO_DICTIONARY = "aruco_dictionary"
    """ArUco dictionary type (DICT_4X4_50, DICT_5X5_100, etc.)"""
    
    ARUCO_FLIP_IMAGE = "aruco_flip_image"
    """Enable/disable image flipping for ArUco detection"""
    
    # ========== UTILITY METHODS ==========
    
    @classmethod
    def get_core_settings(cls) -> list['CameraSettingKeys']:
        """Get list of core camera setting keys."""
        return [
            cls.CAMERA_INDEX, cls.WIDTH, cls.HEIGHT, 
            cls.SKIP_FRAMES, cls.CAPTURE_POS_OFFSET
        ]
    
    @classmethod
    def get_contour_settings(cls) -> list['CameraSettingKeys']:
        """Get list of contour detection setting keys."""
        return [
            cls.CONTOUR_DETECTION, cls.DRAW_CONTOURS, cls.THRESHOLD,
            cls.THRESHOLD_PICKUP_AREA, cls.EPSILON, cls.MIN_CONTOUR_AREA, 
            cls.MAX_CONTOUR_AREA
        ]
    
    @classmethod
    def get_preprocessing_settings(cls) -> list['CameraSettingKeys']:
        """Get list of preprocessing setting keys."""
        return [
            cls.GAUSSIAN_BLUR, cls.BLUR_KERNEL_SIZE, cls.THRESHOLD_TYPE,
            cls.DILATE_ENABLED, cls.DILATE_KERNEL_SIZE, cls.DILATE_ITERATIONS,
            cls.ERODE_ENABLED, cls.ERODE_KERNEL_SIZE, cls.ERODE_ITERATIONS
        ]
    
    @classmethod
    def get_calibration_settings(cls) -> list['CameraSettingKeys']:
        """Get list of calibration setting keys.""" 
        return [
            cls.CHESSBOARD_WIDTH, cls.CHESSBOARD_HEIGHT,
            cls.SQUARE_SIZE_MM, cls.CALIBRATION_SKIP_FRAMES
        ]
    
    @classmethod
    def get_brightness_settings(cls) -> list['CameraSettingKeys']:
        """Get list of brightness control setting keys."""
        return [
            cls.BRIGHTNESS_AUTO, cls.BRIGHTNESS_KP, cls.BRIGHTNESS_KI,
            cls.BRIGHTNESS_KD, cls.TARGET_BRIGHTNESS
        ]
    
    @classmethod
    def get_aruco_settings(cls) -> list['CameraSettingKeys']:
        """Get list of ArUco detection setting keys."""
        return [
            cls.ARUCO_ENABLED, cls.ARUCO_DICTIONARY, cls.ARUCO_FLIP_IMAGE
        ]
    
    @classmethod
    def get_all_keys(cls) -> list['CameraSettingKeys']:
        """Get list of all camera setting keys."""
        return [key for key in cls]