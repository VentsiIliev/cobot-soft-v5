from typing import Tuple
from ..models import PlacementTarget


def calculate_target_drop_position(plane, width: float, height: float) -> PlacementTarget:
    """
    Calculate target placement position on the plane.
    
    Args:
        plane: Plane object with placement boundaries
        width: Workpiece width
        height: Workpiece height
    
    Returns:
        PlacementTarget with calculated coordinates
    """
    target_point_x = plane.xOffset + plane.xMin + (width / 2)
    target_point_y = plane.yMax - plane.yOffset - (height / 2)
    
    return PlacementTarget(x=target_point_x, y=target_point_y)


def calculate_pickup_heights(robot_service, gripper, grippers_config, match_height: float, 
                           descent_height_offset: float) -> Tuple[float, float, float]:
    """
    Calculate z_min, descent_height, and pickup_height.
    
    Args:
        robot_service: Robot service for accessing config
        gripper: Gripper type
        grippers_config: Gripper configuration
        match_height: Height of the workpiece
        descent_height_offset: Offset for descent height
    
    Returns:
        Tuple of (z_min, descent_height, pickup_height)
    """
    from modules.shared.tools.enums.Gripper import Gripper
    
    z_min = robot_service.robot_config.safety_limits.z_min
    descent_height = z_min + descent_height_offset  # Safe descent height above minimum
    
    if gripper == Gripper.DOUBLE:
        pickup_height = z_min + grippers_config.double_gripper_z_offset + match_height
    elif gripper == Gripper.SINGLE:
        pickup_height = z_min + grippers_config.single_gripper_z_offset + match_height
    else:
        raise ValueError(f"Unknown gripper type: {gripper}")

    return z_min, descent_height, pickup_height


def determine_gripper_orientation(gripper, base_rz_orientation: float) -> float:
    """
    Determine RZ orientation based on gripper type.
    
    Args:
        gripper: Gripper type
        base_rz_orientation: Base RZ orientation
    
    Returns:
        Calculated RZ orientation
    """
    from modules.shared.tools.enums.Gripper import Gripper
    
    if gripper == Gripper.DOUBLE:
        return base_rz_orientation - 90
    else:
        return base_rz_orientation


def determine_drop_off_orientation(gripper) -> float:
    """
    Calculate RZ rotation for drop-off based on gripper type.
    
    Args:
        gripper: Gripper type
    
    Returns:
        Drop-off RZ rotation
    """
    from modules.shared.tools.enums.Gripper import Gripper
    
    if gripper == Gripper.DOUBLE:
        return -90
    else:
        return 0