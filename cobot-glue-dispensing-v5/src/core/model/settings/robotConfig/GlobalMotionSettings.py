from dataclasses import dataclass
from typing import Dict


@dataclass
class GlobalMotionSettings:
    """Data class representing global motion settings"""
    global_velocity: int = 100
    global_acceleration: int = 100
    emergency_decel: int = 500
    max_jog_step: int = 50

    @classmethod
    def from_dict(cls, data: Dict) -> 'GlobalMotionSettings':
        """Create GlobalMotionSettings from dictionary data"""
        return cls(
            global_velocity=data.get("global_velocity", 100),
            global_acceleration=data.get("global_acceleration", 100),
            emergency_decel=data.get("emergency_decel", 500),
            max_jog_step=data.get("max_jog_step", 50)
        )

    def to_dict(self) -> Dict:
        """Convert GlobalMotionSettings to dictionary"""
        return {
            "global_velocity": self.global_velocity,
            "global_acceleration": self.global_acceleration,
            "emergency_decel": self.emergency_decel,
            "max_jog_step": self.max_jog_step
        }