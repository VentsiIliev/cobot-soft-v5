import math
from typing import Tuple
from ..models import GrippersConfig
from ..operations import rotate_offsets
from modules.shared.tools.enums.Gripper import Gripper


class GripperService:
    """Service for gripper-related operations and configurations."""
    
    def __init__(self, grippers_config: GrippersConfig):
        self.grippers_config = grippers_config
    
    def apply_gripper_offsets_to_positions(self, gripper, drop_off_position1: list, 
                                         drop_off_position2: list) -> None:
        """
        Apply gripper offsets to drop-off positions based on gripper type.
        
        Args:
            gripper: Gripper type
            drop_off_position1: First drop-off position (modified in place)
            drop_off_position2: Second drop-off position (modified in place)
        """
        if gripper == Gripper.DOUBLE:
            # Rotate the offsets by -90 degrees and apply them
            orientation_radians = math.radians(-90)
            rotated_x, rotated_y = rotate_offsets(
                self.grippers_config.gripper_x_offset, 
                self.grippers_config.gripper_y_offset, 
                orientation_radians
            )
            
            # Apply to both positions
            drop_off_position1[0] += rotated_x
            drop_off_position1[1] += rotated_y
            drop_off_position2[0] += rotated_x
            drop_off_position2[1] += rotated_y
        else:
            # Apply standard gripper offsets
            drop_off_position1[0] += self.grippers_config.gripper_x_offset
            drop_off_position1[1] += self.grippers_config.gripper_y_offset
            drop_off_position2[0] += self.grippers_config.gripper_x_offset
            drop_off_position2[1] += self.grippers_config.gripper_y_offset
    
    def get_gripper_z_offset(self, gripper) -> float:
        """
        Get Z offset for the specified gripper type.
        
        Args:
            gripper: Gripper type
            
        Returns:
            Z offset in mm
        """
        if gripper == Gripper.DOUBLE:
            return self.grippers_config.double_gripper_z_offset
        elif gripper == Gripper.SINGLE:
            return self.grippers_config.single_gripper_z_offset
        else:
            raise ValueError(f"Unknown gripper type: {gripper}")
    
    def get_gripper_xy_offsets(self) -> Tuple[float, float]:
        """
        Get X and Y offsets for grippers.
        
        Returns:
            Tuple of (x_offset, y_offset)
        """
        return self.grippers_config.gripper_x_offset, self.grippers_config.gripper_y_offset
    
    def validate_gripper_type(self, gripper) -> bool:
        """
        Validate that the gripper type is supported.
        
        Args:
            gripper: Gripper type to validate
            
        Returns:
            True if valid, False otherwise
        """
        return gripper in [Gripper.SINGLE, Gripper.DOUBLE]