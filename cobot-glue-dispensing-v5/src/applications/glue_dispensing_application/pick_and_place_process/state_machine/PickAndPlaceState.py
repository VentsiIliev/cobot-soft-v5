"""
Pick and Place Process States

This module defines the states specific to the pick and place (nesting) application.
These states represent the complete workflow for automated workpiece placement operations.
"""

from enum import Enum, auto
from typing import Dict, Set


class PickAndPlaceState(Enum):
    """
    States specific to the pick and place nesting process.
    
    These states represent the complete workflow for nesting operations,
    from initialization through completion with full pause/resume/stop control.
    """
    
    # Initialization and Setup
    INITIALIZING = auto()
    IDLE = auto()
    
    # Vision and Detection
    MOVING_TO_CAPTURE_POSITION = auto()
    SETTING_UP_VISION = auto()
    DETECTING_CONTOURS = auto()
    FILTERING_CONTOURS = auto()
    MATCHING_WORKPIECES = auto()
    
    # Workpiece Processing
    PROCESSING_WORKPIECE = auto()
    CALCULATING_PICKUP_POSITION = auto()
    CALCULATING_PLACEMENT_POSITION = auto()
    
    # Gripper Management
    CHANGING_GRIPPER = auto()
    VERIFYING_GRIPPER = auto()
    
    # Height Measurement
    MEASURING_HEIGHT = auto()
    
    # Execution
    EXECUTING_PICK_AND_PLACE = auto()
    
    # Loop Control
    CHECKING_FOR_MORE_WORKPIECES = auto()
    UPDATING_DEBUG_INFO = auto()
    
    # Completion and Control States
    COMPLETED = auto()
    ERROR = auto()
    STOPPED = auto()
    PAUSED = auto()
    
    # Cleanup
    CLEANING_UP = auto()
    DROPPING_GRIPPER = auto()


class PickAndPlaceTransitionRules:
    """
    Transition rules specific to the pick and place process.
    
    These rules define the valid state transitions for nesting operations
    with proper pause/resume/stop control at each step.
    """
    
    @staticmethod
    def get_pick_and_place_transition_rules() -> Dict[PickAndPlaceState, Set[PickAndPlaceState]]:
        """
        Get the complete transition rules for pick and place operations.
        
        Returns:
            Dict mapping pick and place states to their valid transition targets
        """
        return {
            PickAndPlaceState.INITIALIZING: {
                PickAndPlaceState.IDLE,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.IDLE: {
                PickAndPlaceState.MOVING_TO_CAPTURE_POSITION,
                PickAndPlaceState.ERROR,
                PickAndPlaceState.STOPPED
            },
            
            PickAndPlaceState.MOVING_TO_CAPTURE_POSITION: {
                PickAndPlaceState.SETTING_UP_VISION,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.SETTING_UP_VISION: {
                PickAndPlaceState.DETECTING_CONTOURS,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.DETECTING_CONTOURS: {
                PickAndPlaceState.FILTERING_CONTOURS,
                PickAndPlaceState.COMPLETED,  # No contours found - end operation
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.FILTERING_CONTOURS: {
                PickAndPlaceState.MATCHING_WORKPIECES,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.MATCHING_WORKPIECES: {
                PickAndPlaceState.PROCESSING_WORKPIECE,
                PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES,  # No matches - check for more
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.PROCESSING_WORKPIECE: {
                PickAndPlaceState.CALCULATING_PICKUP_POSITION,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.CALCULATING_PICKUP_POSITION: {
                PickAndPlaceState.CALCULATING_PLACEMENT_POSITION,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.CALCULATING_PLACEMENT_POSITION: {
                PickAndPlaceState.CHANGING_GRIPPER,
                PickAndPlaceState.COMPLETED,  # Plane full
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.CHANGING_GRIPPER: {
                PickAndPlaceState.VERIFYING_GRIPPER,
                PickAndPlaceState.MEASURING_HEIGHT,  # Skip if same gripper
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.VERIFYING_GRIPPER: {
                PickAndPlaceState.MEASURING_HEIGHT,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.MEASURING_HEIGHT: {
                PickAndPlaceState.EXECUTING_PICK_AND_PLACE,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.EXECUTING_PICK_AND_PLACE: {
                PickAndPlaceState.UPDATING_DEBUG_INFO,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.UPDATING_DEBUG_INFO: {
                PickAndPlaceState.PROCESSING_WORKPIECE,  # Continue with next workpiece in batch
                PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES,
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES: {
                PickAndPlaceState.MOVING_TO_CAPTURE_POSITION,  # Continue with more workpieces
                PickAndPlaceState.COMPLETED,  # No more workpieces
                PickAndPlaceState.PAUSED,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.ERROR
            },
            
            # Control States
            PickAndPlaceState.PAUSED: {
                PickAndPlaceState.PAUSED,  # Stay paused
                PickAndPlaceState.MOVING_TO_CAPTURE_POSITION,  # Resume from any paused state
                PickAndPlaceState.SETTING_UP_VISION,
                PickAndPlaceState.DETECTING_CONTOURS,
                PickAndPlaceState.FILTERING_CONTOURS,
                PickAndPlaceState.MATCHING_WORKPIECES,
                PickAndPlaceState.PROCESSING_WORKPIECE,
                PickAndPlaceState.CALCULATING_PICKUP_POSITION,
                PickAndPlaceState.CALCULATING_PLACEMENT_POSITION,
                PickAndPlaceState.CHANGING_GRIPPER,
                PickAndPlaceState.VERIFYING_GRIPPER,
                PickAndPlaceState.MEASURING_HEIGHT,
                PickAndPlaceState.EXECUTING_PICK_AND_PLACE,
                PickAndPlaceState.UPDATING_DEBUG_INFO,
                PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES,
                PickAndPlaceState.STOPPED,
                PickAndPlaceState.COMPLETED,
                PickAndPlaceState.IDLE,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.STOPPED: {
                PickAndPlaceState.CLEANING_UP,
                PickAndPlaceState.COMPLETED,
                PickAndPlaceState.IDLE,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.CLEANING_UP: {
                PickAndPlaceState.DROPPING_GRIPPER,
                PickAndPlaceState.COMPLETED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.DROPPING_GRIPPER: {
                PickAndPlaceState.COMPLETED,
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.COMPLETED: {
                PickAndPlaceState.IDLE,  # Ready for next operation
                PickAndPlaceState.ERROR
            },
            
            PickAndPlaceState.ERROR: {
                PickAndPlaceState.ERROR,  # Stay in error
                PickAndPlaceState.IDLE,  # Recovery
                PickAndPlaceState.INITIALIZING  # Full reset
            }
        }