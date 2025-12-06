import math
from typing import Tuple
from ..models import Position


def apply_90_degree_rotation(x: float, y: float) -> Tuple[float, float]:
    """Apply 90° coordinate transformation."""
    pickup_x_rotated = -y  # 90° rotation: x' = -y
    pickup_y_rotated = x   # 90° rotation: y' = x
    return pickup_x_rotated, pickup_y_rotated


def rotate_offsets(x_offset: float, y_offset: float, orientation_radians: float) -> Tuple[float, float]:
    """Rotate gripper offsets by given orientation."""
    cos_angle = math.cos(orientation_radians)
    sin_angle = math.sin(orientation_radians)
    
    rotated_x = x_offset * cos_angle - y_offset * sin_angle
    rotated_y = x_offset * sin_angle + y_offset * cos_angle
    
    return rotated_x, rotated_y


def apply_final_pickup_coordinates(rotated_position: Tuple[float, float], 
                                   rotated_offsets: Tuple[float, float]) -> Tuple[float, float]:
    """Apply rotated offsets to rotated position."""
    pickup_x_rotated, pickup_y_rotated = rotated_position
    gripper_x_offset_rotated, gripper_y_offset_rotated = rotated_offsets
    
    final_pickup_x = pickup_x_rotated + gripper_x_offset_rotated
    final_pickup_y = pickup_y_rotated + gripper_y_offset_rotated
    
    return final_pickup_x, final_pickup_y


def create_position_from_coordinates(x: float, y: float, z: float, 
                                     rx: float = 180, ry: float = 0, rz: float = 0) -> Position:
    """Create a Position object from coordinates."""
    return Position(x=x, y=y, z=z, rx=rx, ry=ry, rz=rz)