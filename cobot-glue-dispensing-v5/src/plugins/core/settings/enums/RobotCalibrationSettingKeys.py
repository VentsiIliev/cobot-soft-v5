"""
RobotCalibrationSettingKeys - Enumeration of all robot calibration setting keys.

Defines all valid setting keys for robot calibration configuration including:
- Adaptive movement settings 
- Work area corner definitions
- Marker detection settings
- Calibration process parameters

Used for type safety and preventing invalid setting key usage.
Handles complex sub-tab structure with work areas and robot calibration.
"""

from enum import Enum


class RobotCalibrationSettingKeys(str, Enum):
    """
    Enumeration of all valid robot calibration setting keys.
    
    Inherits from str to allow direct string comparison while providing
    type safety and IDE autocompletion support.
    
    Includes keys for both work area definitions and robot calibration parameters.
    """
    
    # ========== ADAPTIVE MOVEMENT SETTINGS ==========
    
    MIN_STEP_MM = "min_step_mm"
    """Minimum movement step size in millimeters (for very small errors)"""
    
    MAX_STEP_MM = "max_step_mm"
    """Maximum movement step size in millimeters (for large misalignments)"""
    
    TARGET_ERROR_MM = "target_error_mm" 
    """Desired target error to reach in millimeters"""
    
    MAX_ERROR_REF = "max_error_ref"
    """Error reference at which maximum step size is used in millimeters"""
    
    RESPONSIVENESS_K = "responsiveness_k"
    """Responsiveness factor K (1.0 = smooth, 2.0 = faster reaction)"""
    
    DERIVATIVE_SCALING = "derivative_scaling"
    """Derivative term scaling factor (how strongly it reduces step size)"""
    
    # ========== GENERAL CALIBRATION SETTINGS ==========
    
    Z_TARGET = "z_target"
    """Target Z height for refined marker search in millimeters"""
    
    REQUIRED_MARKER_IDS = "required_marker_ids"
    """List of required ArUco marker IDs for calibration"""
    
    # ========== WORK AREA CORNER SETTINGS ==========
    # Format: WORK_AREA_{AREA_TYPE}_{CORNER}_{COORDINATE}
    
    # Pickup Area Corners
    WORK_AREA_PICKUP_CORNER1_X = "work_area_pickup_corner1_x"
    """Pickup area corner 1 X coordinate in camera pixels"""
    
    WORK_AREA_PICKUP_CORNER1_Y = "work_area_pickup_corner1_y"
    """Pickup area corner 1 Y coordinate in camera pixels"""
    
    WORK_AREA_PICKUP_CORNER2_X = "work_area_pickup_corner2_x"
    """Pickup area corner 2 X coordinate in camera pixels"""
    
    WORK_AREA_PICKUP_CORNER2_Y = "work_area_pickup_corner2_y"
    """Pickup area corner 2 Y coordinate in camera pixels"""
    
    WORK_AREA_PICKUP_CORNER3_X = "work_area_pickup_corner3_x"
    """Pickup area corner 3 X coordinate in camera pixels"""
    
    WORK_AREA_PICKUP_CORNER3_Y = "work_area_pickup_corner3_y"
    """Pickup area corner 3 Y coordinate in camera pixels"""
    
    WORK_AREA_PICKUP_CORNER4_X = "work_area_pickup_corner4_x"
    """Pickup area corner 4 X coordinate in camera pixels"""
    
    WORK_AREA_PICKUP_CORNER4_Y = "work_area_pickup_corner4_y"
    """Pickup area corner 4 Y coordinate in camera pixels"""
    
    # Spray Area Corners
    WORK_AREA_SPRAY_CORNER1_X = "work_area_spray_corner1_x"
    """Spray area corner 1 X coordinate in camera pixels"""
    
    WORK_AREA_SPRAY_CORNER1_Y = "work_area_spray_corner1_y"
    """Spray area corner 1 Y coordinate in camera pixels"""
    
    WORK_AREA_SPRAY_CORNER2_X = "work_area_spray_corner2_x"
    """Spray area corner 2 X coordinate in camera pixels"""
    
    WORK_AREA_SPRAY_CORNER2_Y = "work_area_spray_corner2_y"
    """Spray area corner 2 Y coordinate in camera pixels"""
    
    WORK_AREA_SPRAY_CORNER3_X = "work_area_spray_corner3_x"
    """Spray area corner 3 X coordinate in camera pixels"""
    
    WORK_AREA_SPRAY_CORNER3_Y = "work_area_spray_corner3_y"
    """Spray area corner 3 Y coordinate in camera pixels"""
    
    WORK_AREA_SPRAY_CORNER4_X = "work_area_spray_corner4_x"
    """Spray area corner 4 X coordinate in camera pixels"""
    
    WORK_AREA_SPRAY_CORNER4_Y = "work_area_spray_corner4_y"
    """Spray area corner 4 Y coordinate in camera pixels"""
    
    # ========== CALIBRATION PROCESS SETTINGS ==========
    
    CALIBRATION_TIMEOUT = "calibration_timeout"
    """Maximum time allowed for calibration process in seconds"""
    
    MARKER_DETECTION_RETRIES = "marker_detection_retries"
    """Number of retries for marker detection before failure"""
    
    POSITION_TOLERANCE = "position_tolerance"
    """Position tolerance for successful calibration in millimeters"""
    
    ROTATION_TOLERANCE = "rotation_tolerance"
    """Rotation tolerance for successful calibration in degrees"""
    
    # ========== ADVANCED SETTINGS ==========
    
    MOVEMENT_SMOOTHING = "movement_smoothing"
    """Enable/disable movement smoothing for calibration"""
    
    VERIFICATION_ENABLED = "verification_enabled"
    """Enable/disable post-calibration verification"""
    
    AUTO_RETRY_ON_FAILURE = "auto_retry_on_failure"
    """Enable/disable automatic retry on calibration failure"""
    
    MAX_CALIBRATION_ATTEMPTS = "max_calibration_attempts"
    """Maximum number of calibration attempts before giving up"""
    
    # ========== UTILITY METHODS ==========
    
    @classmethod
    def get_adaptive_movement_settings(cls) -> list['RobotCalibrationSettingKeys']:
        """Get list of adaptive movement setting keys."""
        return [
            cls.MIN_STEP_MM, cls.MAX_STEP_MM, cls.TARGET_ERROR_MM,
            cls.MAX_ERROR_REF, cls.RESPONSIVENESS_K, cls.DERIVATIVE_SCALING
        ]
    
    @classmethod
    def get_general_settings(cls) -> list['RobotCalibrationSettingKeys']:
        """Get list of general calibration setting keys."""
        return [
            cls.Z_TARGET, cls.REQUIRED_MARKER_IDS
        ]
    
    @classmethod
    def get_pickup_area_corners(cls) -> list['RobotCalibrationSettingKeys']:
        """Get list of pickup area corner setting keys."""
        return [
            cls.WORK_AREA_PICKUP_CORNER1_X, cls.WORK_AREA_PICKUP_CORNER1_Y,
            cls.WORK_AREA_PICKUP_CORNER2_X, cls.WORK_AREA_PICKUP_CORNER2_Y,
            cls.WORK_AREA_PICKUP_CORNER3_X, cls.WORK_AREA_PICKUP_CORNER3_Y,
            cls.WORK_AREA_PICKUP_CORNER4_X, cls.WORK_AREA_PICKUP_CORNER4_Y
        ]
    
    @classmethod
    def get_spray_area_corners(cls) -> list['RobotCalibrationSettingKeys']:
        """Get list of spray area corner setting keys."""
        return [
            cls.WORK_AREA_SPRAY_CORNER1_X, cls.WORK_AREA_SPRAY_CORNER1_Y,
            cls.WORK_AREA_SPRAY_CORNER2_X, cls.WORK_AREA_SPRAY_CORNER2_Y,
            cls.WORK_AREA_SPRAY_CORNER3_X, cls.WORK_AREA_SPRAY_CORNER3_Y,
            cls.WORK_AREA_SPRAY_CORNER4_X, cls.WORK_AREA_SPRAY_CORNER4_Y
        ]
    
    @classmethod
    def get_all_work_area_corners(cls) -> list['RobotCalibrationSettingKeys']:
        """Get list of all work area corner setting keys."""
        return cls.get_pickup_area_corners() + cls.get_spray_area_corners()
    
    @classmethod
    def get_process_settings(cls) -> list['RobotCalibrationSettingKeys']:
        """Get list of calibration process setting keys."""
        return [
            cls.CALIBRATION_TIMEOUT, cls.MARKER_DETECTION_RETRIES,
            cls.POSITION_TOLERANCE, cls.ROTATION_TOLERANCE
        ]
    
    @classmethod
    def get_advanced_settings(cls) -> list['RobotCalibrationSettingKeys']:
        """Get list of advanced setting keys."""
        return [
            cls.MOVEMENT_SMOOTHING, cls.VERIFICATION_ENABLED,
            cls.AUTO_RETRY_ON_FAILURE, cls.MAX_CALIBRATION_ATTEMPTS
        ]
    
    @classmethod
    def get_corner_coordinate_key(cls, area_type: str, corner_num: int, coordinate: str) -> 'RobotCalibrationSettingKeys':
        """
        Get the setting key for a specific work area corner coordinate.
        
        Args:
            area_type: 'pickup' or 'spray'
            corner_num: Corner number (1-4)
            coordinate: 'x' or 'y'
            
        Returns:
            RobotCalibrationSettingKeys: The corresponding setting key
            
        Raises:
            ValueError: If parameters are invalid
        """
        if area_type not in ['pickup', 'spray']:
            raise ValueError(f"Invalid area_type: {area_type}. Must be 'pickup' or 'spray'")
        
        if corner_num not in [1, 2, 3, 4]:
            raise ValueError(f"Invalid corner_num: {corner_num}. Must be 1, 2, 3, or 4")
        
        if coordinate not in ['x', 'y']:
            raise ValueError(f"Invalid coordinate: {coordinate}. Must be 'x' or 'y'")
        
        key_name = f"WORK_AREA_{area_type.upper()}_CORNER{corner_num}_{coordinate.upper()}"
        return cls(getattr(cls, key_name))
    
    @classmethod
    def parse_corner_key(cls, key: 'RobotCalibrationSettingKeys') -> tuple[str, int, str]:
        """
        Parse a corner setting key to extract area type, corner number, and coordinate.
        
        Args:
            key: Corner setting key to parse
            
        Returns:
            tuple[str, int, str]: (area_type, corner_num, coordinate)
            
        Raises:
            ValueError: If key is not a corner setting key
        """
        if not key.value.startswith('work_area_'):
            raise ValueError(f"Key {key} is not a work area corner key")
        
        parts = key.value.split('_')
        if len(parts) != 5 or parts[0] != 'work' or parts[1] != 'area':
            raise ValueError(f"Invalid corner key format: {key}")
        
        area_type = parts[2].lower()
        corner_part = parts[3]
        coordinate = parts[4].lower()
        
        if not corner_part.startswith('corner'):
            raise ValueError(f"Invalid corner part: {corner_part}")
        
        try:
            corner_num = int(corner_part.replace('corner', ''))
        except ValueError:
            raise ValueError(f"Invalid corner number in: {corner_part}")
        
        return area_type, corner_num, coordinate
    
    @classmethod
    def is_corner_key(cls, key: 'RobotCalibrationSettingKeys') -> bool:
        """Check if a setting key represents a work area corner coordinate."""
        return key.value.startswith('work_area_') and ('corner' in key.value)
    
    @classmethod
    def get_all_keys(cls) -> list['RobotCalibrationSettingKeys']:
        """Get list of all robot calibration setting keys."""
        return [key for key in cls]