from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Position:
    """Represents a 6-DOF robot position [x, y, z, rx, ry, rz]."""
    x: float
    y: float
    z: float
    rx: float
    ry: float
    rz: float

    def to_list(self) -> List[float]:
        """Convert position to list format for robot commands."""
        return [self.x, self.y, self.z, self.rx, self.ry, self.rz]


@dataclass
class PickupPositions:
    """Container for the three-stage pickup sequence."""
    descent: Position
    pickup: Position
    lift: Position

    def to_list(self) -> List[List[float]]:
        """Convert all positions to list format."""
        return [
            self.descent.to_list(),
            self.pickup.to_list(),
            self.lift.to_list()
        ]


@dataclass
class DropOffPositions:
    """Container for drop-off positions."""
    position1: Position  # Higher drop position
    position2: Position  # Lower drop position

    def to_tuple(self) -> Tuple[List[float], List[float]]:
        """Convert to tuple of lists for backward compatibility."""
        return self.position1.to_list(), self.position2.to_list()


@dataclass
class HeightMeasurePosition:
    """Position for height measurement operations."""
    position: Position