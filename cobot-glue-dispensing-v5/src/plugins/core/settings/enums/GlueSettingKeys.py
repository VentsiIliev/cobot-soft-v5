"""
GlueSettingKeys - Enumeration of all glue dispensing setting keys.

Defines all valid setting keys for glue dispensing configuration including:
- Spray settings (width, height, fan speed)
- Motor control settings (speed, direction, ramping)
- General settings (angle, timeouts)
- Device control settings

Used for type safety and preventing invalid setting key usage.
"""

from enum import Enum


class GlueSettingKeys(str, Enum):
    """
    Enumeration of all valid glue dispensing setting keys.
    
    Inherits from str to allow direct string comparison while providing
    type safety and IDE autocompletion support.
    """
    
    # ========== SPRAY SETTINGS ==========
    
    SPRAY_WIDTH = "spray_width"
    """Width of spray pattern in mm"""
    
    SPRAYING_HEIGHT = "spraying_height"
    """Height for spraying operation in mm"""
    
    FAN_SPEED = "fan_speed"
    """Fan speed percentage (0-100%)"""
    
    GENERATOR_TO_GLUE_DELAY = "generator_to_glue_delay"
    """Time delay between generator activation and glue dispensing in seconds"""
    
    TIME_BEFORE_MOTION = "time_before_motion"
    """Timeout before motion starts in seconds"""
    
    REACH_START_THRESHOLD = "reach_start_threshold"
    """Position threshold to start operation in mm"""
    
    # ========== MOTOR CONTROL SETTINGS ==========
    
    # Forward Motion
    MOTOR_SPEED = "motor_speed"
    """Primary motor speed in Hz"""
    
    FORWARD_RAMP_STEPS = "forward_ramp_steps"
    """Number of ramping steps for forward motion"""
    
    INITIAL_RAMP_SPEED = "initial_ramp_speed"
    """Initial speed for ramping in Hz"""
    
    INITIAL_RAMP_SPEED_DURATION = "initial_ramp_speed_duration"
    """Duration for initial ramp speed in seconds"""
    
    # Reverse Motion
    REVERSE_SPEED = "reverse_speed"
    """Motor reverse speed in Hz"""
    
    REVERSE_DURATION = "reverse_duration"
    """Duration of reverse motion in seconds"""
    
    REVERSE_RAMP_STEPS = "reverse_ramp_steps"
    """Number of ramping steps for reverse motion"""
    
    # ========== GENERAL SETTINGS ==========
    
    RZ_ANGLE = "rz_angle"
    """Rotation angle around Z-axis in degrees"""
    
    GENERATOR_TIMEOUT = "generator_timeout"
    """Timeout for generator operation in seconds"""
    
    GLUE_TYPE = "glue_type"
    """Type of glue being used (affects dispensing parameters)"""
    
    # ========== DEVICE CONTROL SETTINGS ==========
    
    SPRAY_ON = "spray_on"
    """Enable/disable spray functionality"""
    
    GENERATOR_ENABLED = "generator_enabled"
    """Enable/disable generator functionality"""
    
    FAN_ENABLED = "fan_enabled"
    """Enable/disable fan functionality"""
    
    # Motor individual controls (if needed for multi-motor systems)
    MOTOR_1_ENABLED = "motor_1_enabled"
    """Enable/disable motor 1"""
    
    MOTOR_2_ENABLED = "motor_2_enabled"
    """Enable/disable motor 2"""
    
    MOTOR_3_ENABLED = "motor_3_enabled"
    """Enable/disable motor 3"""
    
    MOTOR_4_ENABLED = "motor_4_enabled"
    """Enable/disable motor 4"""
    
    # ========== ADVANCED SETTINGS ==========
    
    PRESSURE_THRESHOLD = "pressure_threshold"
    """Pressure threshold for safety checks"""
    
    TEMPERATURE_THRESHOLD = "temperature_threshold"
    """Temperature threshold for operation limits"""
    
    VISCOSITY_COMPENSATION = "viscosity_compensation"
    """Viscosity compensation factor for different glue types"""
    
    FLOW_RATE_CALIBRATION = "flow_rate_calibration"
    """Flow rate calibration factor"""
    
    # ========== SAFETY SETTINGS ==========
    
    EMERGENCY_STOP_ENABLED = "emergency_stop_enabled"
    """Enable emergency stop functionality"""
    
    MAX_OPERATION_TIME = "max_operation_time"
    """Maximum continuous operation time in seconds"""
    
    COOL_DOWN_TIME = "cool_down_time"
    """Required cool down time between operations in seconds"""
    
    # ========== UTILITY METHODS ==========
    
    @classmethod
    def get_spray_settings(cls) -> list['GlueSettingKeys']:
        """Get list of spray-related setting keys."""
        return [
            cls.SPRAY_WIDTH, cls.SPRAYING_HEIGHT, cls.FAN_SPEED,
            cls.GENERATOR_TO_GLUE_DELAY, cls.TIME_BEFORE_MOTION,
            cls.REACH_START_THRESHOLD
        ]
    
    @classmethod
    def get_motor_settings(cls) -> list['GlueSettingKeys']:
        """Get list of motor control setting keys."""
        return [
            cls.MOTOR_SPEED, cls.FORWARD_RAMP_STEPS, cls.INITIAL_RAMP_SPEED,
            cls.INITIAL_RAMP_SPEED_DURATION, cls.REVERSE_SPEED, 
            cls.REVERSE_DURATION, cls.REVERSE_RAMP_STEPS
        ]
    
    @classmethod
    def get_general_settings(cls) -> list['GlueSettingKeys']:
        """Get list of general setting keys."""
        return [
            cls.RZ_ANGLE, cls.GENERATOR_TIMEOUT, cls.GLUE_TYPE
        ]
    
    @classmethod
    def get_device_control_settings(cls) -> list['GlueSettingKeys']:
        """Get list of device control setting keys."""
        return [
            cls.SPRAY_ON, cls.GENERATOR_ENABLED, cls.FAN_ENABLED,
            cls.MOTOR_1_ENABLED, cls.MOTOR_2_ENABLED, 
            cls.MOTOR_3_ENABLED, cls.MOTOR_4_ENABLED
        ]
    
    @classmethod
    def get_advanced_settings(cls) -> list['GlueSettingKeys']:
        """Get list of advanced setting keys."""
        return [
            cls.PRESSURE_THRESHOLD, cls.TEMPERATURE_THRESHOLD,
            cls.VISCOSITY_COMPENSATION, cls.FLOW_RATE_CALIBRATION
        ]
    
    @classmethod
    def get_safety_settings(cls) -> list['GlueSettingKeys']:
        """Get list of safety setting keys."""
        return [
            cls.EMERGENCY_STOP_ENABLED, cls.MAX_OPERATION_TIME,
            cls.COOL_DOWN_TIME
        ]
    
    @classmethod
    def get_all_keys(cls) -> list['GlueSettingKeys']:
        """Get list of all glue setting keys."""
        return [key for key in cls]