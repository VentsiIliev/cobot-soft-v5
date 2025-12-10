from typing import Dict, Any
from .BaseJsonSettingsRepository import BaseJsonSettingsRepository
from core.model.settings.modbusConfig.modbusConfigModel import ModbusConfig, get_default_modbus_config
class ModbusSettingsRepository(BaseJsonSettingsRepository[ModbusConfig]):
    def get_default(self) -> ModbusConfig:
        try:
            return get_default_modbus_config()
        except Exception:
            return ModbusConfig()
    def to_dict(self, settings: ModbusConfig) -> Dict[str, Any]:
        return settings.to_dict()
    def from_dict(self, data: Dict[str, Any]) -> ModbusConfig:
        return ModbusConfig.from_dict(data)
    def get_settings_type(self) -> str:
        return "modbus_config"
    def update_field(self, field: str, value: Any) -> None:
        config = self.load()
        config.update_field(field, value)
        self.save(config)
