from typing import Tuple, Optional
from ..models import WorkpiecePlacement, PlacementResult, DropOffPositions, Position, WorkpieceDimensions
from ..operations import (
    process_workpiece_contour,
    calculate_workpiece_dimensions,
    calculate_target_drop_position,
    translate_contour_to_target,
    determine_drop_off_orientation
)
from .plane_management_service import PlaneManagementService


class PlacementService:
    """Service for calculating workpiece placement positions."""
    
    def __init__(self, plane_service: PlaneManagementService):
        self.plane_service = plane_service
    
    def calculate_placement_positions(self, match, centroid: Tuple[float, float], 
                                    orientation: float, pickup_height: float, 
                                    gripper) -> PlacementResult:
        """
        Calculate complete placement positions for a workpiece.
        
        Args:
            match: Matched workpiece object
            centroid: Original centroid coordinates
            orientation: Object orientation in degrees
            pickup_height: Height at which the workpiece was picked up
            gripper: Gripper type for determining orientation
            
        Returns:
            PlacementResult with placement information or failure details
        """
        try:
            # Process workpiece contour
            cnt_object, cnt = process_workpiece_contour(match, centroid, orientation)
            
            # Calculate workpiece dimensions
            dimensions = calculate_workpiece_dimensions(cnt_object)
            
            # Update plane height tracking
            self.plane_service.update_height_tracking(dimensions.height)
            
            # Calculate initial target position
            target_position = calculate_target_drop_position(
                self.plane_service.plane, dimensions.width, dimensions.height
            )
            
            # Handle row overflow if needed
            overflow_result = self.plane_service.handle_row_overflow(
                dimensions.width, dimensions.height, target_position.x, target_position.y
            )
            
            if overflow_result.plane_full:
                return PlacementResult(
                    success=False,
                    placement=None,
                    plane_full=True,
                    message="Plane is full - cannot fit more workpieces"
                )
            
            # Update target position if overflow occurred
            if overflow_result.overflow_occurred:
                target_position.x = overflow_result.new_target_x
                target_position.y = overflow_result.new_target_y
            
            # Translate contour to target position
            new_centroid, translation_x, translation_y = translate_contour_to_target(
                cnt_object, dimensions.bbox_center, target_position.x, target_position.y
            )
            
            # Determine drop-off orientation based on gripper
            drop_off_rz = determine_drop_off_orientation(gripper)
            
            # Create drop-off positions
            drop_off_positions = self._create_drop_off_positions(
                new_centroid, pickup_height, drop_off_rz
            )
            
            # Update plane for next placement
            self.plane_service.update_for_next_placement(dimensions.width)
            
            # Create placement object
            placement = WorkpiecePlacement(
                dimensions=dimensions,
                target_position=target_position,
                pickup_positions=None,  # Will be set by caller
                drop_off_positions=drop_off_positions,
                pickup_height=pickup_height,
                contour=cnt_object.get(),
                translation=(translation_x, translation_y)
            )
            
            return PlacementResult(
                success=True,
                placement=placement,
                plane_full=False,
                message="Placement calculated successfully"
            )
            
        except Exception as e:
            return PlacementResult(
                success=False,
                placement=None,
                plane_full=False,
                message=f"Error calculating placement: {str(e)}"
            )
    
    def _create_drop_off_positions(self, centroid: Tuple[float, float], 
                                 pickup_height: float, drop_off_rz: float) -> DropOffPositions:
        """
        Create drop-off position objects.
        
        Args:
            centroid: New centroid after translation
            pickup_height: Height at which workpiece was picked up
            drop_off_rz: RZ rotation for drop-off
            
        Returns:
            DropOffPositions object
        """
        position1 = Position(
            x=centroid[0], 
            y=centroid[1], 
            z=pickup_height + 50, 
            rx=180, 
            ry=0, 
            rz=drop_off_rz
        )
        
        position2 = Position(
            x=centroid[0], 
            y=centroid[1], 
            z=pickup_height + 20, 
            rx=180, 
            ry=0, 
            rz=drop_off_rz
        )
        
        return DropOffPositions(position1=position1, position2=position2)