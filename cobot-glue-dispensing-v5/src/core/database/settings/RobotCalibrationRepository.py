from typing import Dict, Any

from core.database.settings.BaseJsonSettingsRepository import BaseJsonSettingsRepository
from core.model.settings.robot_calibration_settings import RobotCalibrationSettings
from core.services.settings.interfaces.ISettingsRepository import T


class RobotCalibrationSettingsRepository(BaseJsonSettingsRepository[RobotCalibrationSettings]):
    def get_default(self) -> T:
        return RobotCalibrationSettings()

    def to_dict(self, settings: T) -> Dict[str, Any]:
        return settings.to_dict()

    def from_dict(self, data: Dict[str, Any]) -> T:
        return RobotCalibrationSettings.from_dict(data)

    def get_settings_type(self) -> str:
        return "robot_calibration"