"""
State handlers for vision-related operations in the pick and place process.
"""

from typing import Optional
from modules.utils.custom_logging import log_info_message

from ..PickAndPlaceState import PickAndPlaceState
from ..PickAndPlaceContext import PickAndPlaceContext


def moving_to_capture_position_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle moving the robot to the capture position.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.MOVING_TO_CAPTURE_POSITION)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Move to capture position
        success = context.robot_workflow.move_to_capture_position(context.application, context.laser)
        
        if not success:
            context.record_error("Failed to move to capture position")
            return PickAndPlaceState.ERROR
        
        log_info_message(context.logger_context, "Moved to capture position successfully")
        return PickAndPlaceState.SETTING_UP_VISION
        
    except Exception as e:
        context.record_error(f"Error moving to capture position: {str(e)}")
        return PickAndPlaceState.ERROR


def setting_up_vision_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle setting up the vision system.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.SETTING_UP_VISION)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Setup vision capture
        context.vision_workflow.setup_vision_capture()
        
        log_info_message(context.logger_context, "Vision system setup completed")
        return PickAndPlaceState.DETECTING_CONTOURS
        
    except Exception as e:
        context.record_error(f"Error setting up vision: {str(e)}")
        return PickAndPlaceState.ERROR


def detecting_contours_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle detecting contours from the vision system.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.DETECTING_CONTOURS)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Get contours with retries
        success, contours = context.vision_workflow.get_contours_with_retries(
            context.max_retries, context.retry_delay
        )
        
        if not success:
            log_info_message(context.logger_context, "No contours found, operation complete")
            return PickAndPlaceState.COMPLETED
        
        # Store contours in context
        context.current_contours = contours
        
        log_info_message(context.logger_context, f"Detected {len(contours)} contours")
        return PickAndPlaceState.FILTERING_CONTOURS
        
    except Exception as e:
        context.record_error(f"Error detecting contours: {str(e)}")
        return PickAndPlaceState.ERROR


def filtering_contours_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle filtering contours by pickup area.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.FILTERING_CONTOURS)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Process and filter contours
        processed_contours = context.vision_workflow.process_detected_contours(context.current_contours)
        filtered_contours = context.vision_workflow.filter_contours_by_pickup_area(processed_contours)
        
        if filtered_contours is None:
            filtered_contours = processed_contours
        
        # Update context with filtered contours
        context.current_contours = filtered_contours
        
        log_info_message(context.logger_context, f"Filtered to {len(filtered_contours)} contours")
        return PickAndPlaceState.MATCHING_WORKPIECES
        
    except Exception as e:
        context.record_error(f"Error filtering contours: {str(e)}")
        return PickAndPlaceState.ERROR


def matching_workpieces_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle matching contours to workpiece templates.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.MATCHING_WORKPIECES)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Match workpieces
        matches_data, no_matches = context.vision_workflow.match_contours_to_workpieces(
            context.preselected_workpieces, context.current_contours
        )
        
        if matches_data is None:
            context.record_error("Error during contour matching")
            return PickAndPlaceState.ERROR
        
        # Extract matches and orientations
        context.current_orientations = matches_data["orientations"]
        context.current_matches = matches_data["workpieces"]
        
        if not context.current_matches or len(context.current_matches) == 0:
            # Increment consecutive empty detection counter
            context.consecutive_empty_detections += 1
            log_info_message(
                context.logger_context,
                f"No workpieces matched (consecutive empty: {context.consecutive_empty_detections}/{context.max_empty_detections}), checking for more"
            )
            return PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES
        
        # Mark that workpieces were found and reset counters
        context.workpiece_found = True
        context.current_match_index = 0
        context.consecutive_empty_detections = 0  # Reset empty detection counter

        log_info_message(context.logger_context, f"Found {len(context.current_matches)} matching workpieces")
        return PickAndPlaceState.PROCESSING_WORKPIECE
        
    except Exception as e:
        context.record_error(f"Error matching workpieces: {str(e)}")
        return PickAndPlaceState.ERROR