"""
Settings update strategies.

This package provides the strategy pattern implementation for updating
different types of settings.
"""

from .base_strategy import SettingsUpdateStrategy
from .camera_strategy import CameraSettingsUpdateStrategy
from .robot_config_strategy import RobotConfigUpdateStrategy
from .robot_calibration_strategy import RobotCalibrationSettingsUpdateStrategy
from .default_strategy import DefaultSettingsUpdateStrategy

__all__ = [
    'SettingsUpdateStrategy',
    'CameraSettingsUpdateStrategy',
    'RobotConfigUpdateStrategy',
    'RobotCalibrationSettingsUpdateStrategy',
    'DefaultSettingsUpdateStrategy',
]
