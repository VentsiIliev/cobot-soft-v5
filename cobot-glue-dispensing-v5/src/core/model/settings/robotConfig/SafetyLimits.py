from dataclasses import dataclass
from typing import Dict


@dataclass
class SafetyLimits:
    """Data class representing robot safety limits"""
    x_min: int = -500
    x_max: int = 500
    y_min: int = -500
    y_max: int = 500
    z_min: int = 100
    z_max: int = 800
    rx_min: int = 170
    rx_max: int = 190
    ry_min: int = -10
    ry_max: int = 10
    rz_min: int = -180
    rz_max: int = 180

    @classmethod
    def from_dict(cls, data: Dict) -> 'SafetyLimits':
        """Create SafetyLimits from dictionary data"""
        return cls(
            x_min=data.get("x_min", -500),
            x_max=data.get("x_max", 500),
            y_min=data.get("y_min", -500),
            y_max=data.get("y_max", 500),
            z_min=data.get("z_min", 100),
            z_max=data.get("z_max", 800),
            rx_min=data.get("rx_min", 170),
            rx_max=data.get("rx_max", 190),
            ry_min=data.get("ry_min", -10),
            ry_max=data.get("ry_max", 10),
            rz_min=data.get("rz_min", -180),
            rz_max=data.get("rz_max", 180)
        )

    def to_dict(self) -> Dict:
        """Convert SafetyLimits to dictionary"""
        return {
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "z_min": self.z_min,
            "z_max": self.z_max,
            "rx_min": self.rx_min,
            "rx_max": self.rx_max,
            "ry_min": self.ry_min,
            "ry_max": self.ry_max,
            "rz_min": self.rz_min,
            "rz_max": self.rz_max
        }