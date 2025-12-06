from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class MovementGroup:
    """Data class representing a movement group configuration"""
    velocity: int = 0
    acceleration: int = 0
    position: Optional[str] = None
    points: List[str] = field(default_factory=list)
    iterations: int = 1

    @classmethod
    def from_dict(cls, data: Dict) -> 'MovementGroup':
        """Create MovementGroup from dictionary data"""
        return cls(
            velocity=data.get("velocity", 0),
            acceleration=data.get("acceleration", 0),
            position=data.get("position"),
            points=data.get("points", []),
            iterations=data.get("iterations", 1)
        )

    def to_dict(self) -> Dict:
        """Convert MovementGroup to dictionary"""
        result = {
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "iterations": self.iterations
        }
        if self.position:
            result["position"] = self.position
        if self.points:
            result["points"] = self.points
        return result

    def parse_position(self) -> Optional[List[float]]:
        """Parse position string into list of floats"""
        if not self.position:
            return None

        try:
            # Remove brackets and split by comma
            position_str = self.position.strip("[]")
            values = [float(x.strip()) for x in position_str.split(",")]
            return values
        except (ValueError, AttributeError):
            return None

    def parse_points(self) -> List[List[float]]:
        """Parse all trajectory points into lists of floats"""
        parsed_points = []
        for point in self.points:
            try:
                # Remove brackets and split by comma
                point_str = point.strip("[]")
                values = [float(x.strip()) for x in point_str.split(",")]
                parsed_points.append(values)
            except (ValueError, AttributeError):
                continue
        return parsed_points