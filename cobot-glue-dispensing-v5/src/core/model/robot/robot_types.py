"""
Robot Types Enum

This module defines the available robot types that can be used in the system.
Each robot type corresponds to a specific robot implementation.
"""

from enum import Enum


class RobotType(Enum):
    """Enum defining available robot types"""
    FAIRINO = "fairino"
    ZERO_ERROR = "zero_error"
    TEST = "test"
    
    def __str__(self):
        return self.value