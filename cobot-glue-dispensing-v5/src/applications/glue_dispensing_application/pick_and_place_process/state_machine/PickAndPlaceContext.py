"""
Pick and Place Context

This module defines the context object that holds all the state data
and services needed for the pick and place state machine operations.
"""

from typing import List, Optional, Any
from dataclasses import dataclass, field

from applications.glue_dispensing_application.glue_process.ExecutionContext import Context
from core.services.robot_service.impl.base_robot_service import RobotService

from ..models import GrippersConfig, WorkpiecePlacement
from ..services import PickupService, PlacementService, PlaneManagementService, GripperService
from ..workflows import VisionWorkflow, RobotWorkflow, MeasurementWorkflow, PlacementWorkflow
from ..Plane import Plane


@dataclass
class PickAndPlaceContext(Context):
    """
    Context object for pick and place state machine operations.
    
    This extends the base Context with all the data and services
    needed for nesting operations.
    """
    
    # Input parameters
    application: Any = None
    vision_service: Any = None
    robot_service: RobotService = None
    preselected_workpieces: List = field(default_factory=list)
    
    # Services and workflows
    pickup_service: Optional[PickupService] = None
    placement_service: Optional[PlacementService] = None
    gripper_service: Optional[GripperService] = None
    plane_service: Optional[PlaneManagementService] = None
    
    vision_workflow: Optional[VisionWorkflow] = None
    robot_workflow: Optional[RobotWorkflow] = None
    measurement_workflow: Optional[MeasurementWorkflow] = None
    placement_workflow: Optional[PlacementWorkflow] = None
    
    # Configuration
    grippers_config: Optional[GrippersConfig] = None
    
    # State data
    plane: Optional[Plane] = None
    laser: Any = None
    logger_context: Any = None
    
    # Current operation data
    current_contours: List = field(default_factory=list)
    current_matches: List = field(default_factory=list)
    current_orientations: List = field(default_factory=list)
    current_match_index: int = 0
    current_match: Any = None
    current_placement: Optional[WorkpiecePlacement] = None
    current_gripper_id: Optional[int] = None
    
    # Tracking and debug data
    count: int = 0
    workpiece_found: bool = False
    placed_contours: List = field(default_factory=list)
    
    # Control flags
    pause_requested: bool = False
    stop_requested: bool = False
    previous_state_before_pause: Optional[Any] = None
    
    # Constants
    RZ_ORIENTATION: float = 90.0
    DESCENT_HEIGHT_OFFSET: float = 150.0
    
    # Retry configuration
    max_retries: int = 10
    retry_delay: int = 1
    
    # Error handling
    last_error: Optional[str] = None
    error_count: int = 0
    max_errors: int = 5
    
    # Empty detection tracking
    consecutive_empty_detections: int = 0
    max_empty_detections: int = 3  # Stop after 3 consecutive empty detections

    def reset_for_new_cycle(self):
        """Reset context for a new nesting cycle."""
        self.current_contours.clear()
        self.current_matches.clear()
        self.current_orientations.clear()
        self.current_match_index = 0
        self.current_match = None
        self.current_placement = None
        self.current_gripper_id = None
    
    def reset_for_new_workpiece(self):
        """Reset context for processing a new workpiece."""
        self.current_match = None
        self.current_placement = None
        self.current_gripper_id = None
    
    def has_more_workpieces_in_batch(self) -> bool:
        """Check if there are more workpieces to process in current batch."""
        return (self.current_matches and 
                self.current_match_index < len(self.current_matches))
    
    def get_next_workpiece(self):
        """Get the next workpiece to process."""
        if self.has_more_workpieces_in_batch():
            self.current_match = self.current_matches[self.current_match_index]
            return self.current_match
        return None
    
    def advance_to_next_workpiece(self):
        """Advance to the next workpiece in the batch."""
        self.current_match_index += 1
        self.reset_for_new_workpiece()
    
    def is_plane_full(self) -> bool:
        """Check if the placement plane is full."""
        return self.plane and hasattr(self.plane, 'isFull') and self.plane.isFull
    
    def should_continue_operation(self) -> bool:
        """Check if the operation should continue."""
        # Check if we've had too many consecutive empty detections
        if self.consecutive_empty_detections >= self.max_empty_detections:
            return False

        return (not self.stop_requested and
                not self.is_plane_full() and 
                self.error_count < self.max_errors)
    
    def record_error(self, error_message: str):
        """Record an error in the context."""
        self.last_error = error_message
        self.error_count += 1
    
    def clear_error(self):
        """Clear the last error."""
        self.last_error = None
        self.error_count = 0
    
    def request_pause(self, current_state=None):
        """Request a pause operation."""
        self.pause_requested = True
        if current_state:
            self.previous_state_before_pause = current_state
    
    def request_stop(self):
        """Request a stop operation."""
        self.stop_requested = True
        self.pause_requested = False
    
    def resume_from_pause(self):
        """Resume from pause state."""
        self.pause_requested = False
        return self.previous_state_before_pause
    
    def get_operation_summary(self) -> dict:
        """Get a summary of the current operation."""
        return {
            'workpieces_placed': self.count,
            'workpiece_found': self.workpiece_found,
            'plane_full': self.is_plane_full(),
            'current_batch_size': len(self.current_matches) if self.current_matches else 0,
            'current_match_index': self.current_match_index,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'paused': self.pause_requested,
            'stop_requested': self.stop_requested
        }