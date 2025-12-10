from dataclasses import dataclass, asdict
from typing import Dict, Any
@dataclass
class ModbusConfig:
    port: str = 'COM5'
    baudrate: int = 115200
    bytesize: int = 8
    stopbits: int = 1
    parity: str = 'N'
    timeout: float = 0.01
    slave_address: int = 10
    max_retries: int = 30
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModbusConfig':
        return cls(
            port=data.get('port', 'COM5'),
            baudrate=data.get('baudrate', 115200),
            bytesize=data.get('bytesize', 8),
            stopbits=data.get('stopbits', 1),
            parity=data.get('parity', 'N'),
            timeout=data.get('timeout', 0.01),
            slave_address=data.get('slave_address', 10),
            max_retries=data.get('max_retries', 30)
        )
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    def update_field(self, field: str, value: Any) -> None:
        if hasattr(self, field):
            setattr(self, field, value)
        else:
            raise ValueError(f"Invalid field: {field}")
def get_default_modbus_config() -> ModbusConfig:
    return ModbusConfig()
