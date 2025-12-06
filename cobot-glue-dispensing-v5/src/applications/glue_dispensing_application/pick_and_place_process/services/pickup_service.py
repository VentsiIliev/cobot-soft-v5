import math
from typing import Tuple
from ..models import PickupPositions, Position, GrippersConfig
from ..operations import (
    apply_90_degree_rotation,
    rotate_offsets,
    apply_final_pickup_coordinates,
    calculate_pickup_heights,
    determine_gripper_orientation,
    create_position_from_coordinates
)


class PickupService:
    """Service for calculating pickup positions and sequences."""
    
    def __init__(self, grippers_config: GrippersConfig, descent_height_offset: float):
        self.grippers_config = grippers_config
        self.descent_height_offset = descent_height_offset
    
    def calculate_pickup_positions(self, flat_centroid: Tuple[float, float], 
                                 match_height: float, robot_service, 
                                 orientation: float, gripper, 
                                 rz_orientation: float) -> Tuple[PickupPositions, Position, float]:
        """
        Calculate pickup positions with coordinate transformation and gripper offsets.
        
        Args:
            flat_centroid: Transformed centroid coordinates from homography
            match_height: Height of the workpiece to pick up
            robot_service: Robot service for accessing config
            orientation: Workpiece orientation in degrees
            gripper: Gripper type
            rz_orientation: Base RZ orientation
            
        Returns:
            Tuple of (pickup_positions, height_measure_position, pickup_height)
        """
        # Apply 90° coordinate transformation
        pickup_x_rotated, pickup_y_rotated = apply_90_degree_rotation(flat_centroid[0], flat_centroid[1])
        
        # Determine gripper-specific orientation
        rz = determine_gripper_orientation(gripper, rz_orientation)
        
        # Calculate rotated gripper offsets
        orientation_radians = math.radians(rz - orientation)
        gripper_x_offset_rotated, gripper_y_offset_rotated = rotate_offsets(
            self.grippers_config.gripper_x_offset,
            self.grippers_config.gripper_y_offset,
            orientation_radians
        )
        
        # Apply rotated offsets to rotated position
        final_pickup_x, final_pickup_y = apply_final_pickup_coordinates(
            (pickup_x_rotated, pickup_y_rotated),
            (gripper_x_offset_rotated, gripper_y_offset_rotated)
        )
        
        # Calculate heights
        z_min, descent_height, pickup_height = calculate_pickup_heights(
            robot_service, gripper, self.grippers_config, match_height, self.descent_height_offset
        )
        
        # Create position objects
        final_orientation = rz - orientation
        
        descent_pos = create_position_from_coordinates(final_pickup_x, final_pickup_y, descent_height, 
                                                     180, 0, final_orientation)
        pickup_pos = create_position_from_coordinates(final_pickup_x, final_pickup_y, pickup_height,
                                                    180, 0, final_orientation)
        lift_pos = create_position_from_coordinates(final_pickup_x, final_pickup_y, descent_height,
                                                  180, 0, final_orientation)
        
        pickup_positions = PickupPositions(descent=descent_pos, pickup=pickup_pos, lift=lift_pos)
        
        # Height measurement position (without gripper offsets)
        height_measure_position = create_position_from_coordinates(
            pickup_x_rotated, pickup_y_rotated, descent_height, 180, 0, final_orientation
        )
        
        return pickup_positions, height_measure_position, pickup_height