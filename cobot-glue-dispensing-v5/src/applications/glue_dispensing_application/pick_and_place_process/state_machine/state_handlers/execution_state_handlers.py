"""
State handlers for execution-related operations in the pick and place process.
"""

from typing import Optional
from modules.utils.custom_logging import log_info_message
from modules.shared.core.ContourStandartized import Contour

from ..PickAndPlaceState import PickAndPlaceState
from ..PickAndPlaceContext import PickAndPlaceContext


def processing_workpiece_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle processing a single workpiece.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.PROCESSING_WORKPIECE)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Get next workpiece to process
        workpiece = context.get_next_workpiece()
        
        if workpiece is None:
            log_info_message(context.logger_context, "No more workpieces in current batch")
            return PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES
        
        context.current_match = workpiece
        
        log_info_message(
            context.logger_context, 
            f"Processing workpiece {context.current_match_index + 1}/{len(context.current_matches)}"
        )
        return PickAndPlaceState.CALCULATING_PICKUP_POSITION
        
    except Exception as e:
        context.record_error(f"Error processing workpiece: {str(e)}")
        return PickAndPlaceState.ERROR


def calculating_pickup_position_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle calculating pickup positions for the current workpiece.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.CALCULATING_PICKUP_POSITION)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        match = context.current_match
        orientation = context.current_orientations[context.current_match_index]
        
        # Create contour object for pickup point determination
        contour = match.get_main_contour()
        cnt_obj = Contour(contour)
        
        # Determine pickup point
        centroid = context.placement_workflow.determine_pickup_point(match, cnt_obj)
        
        # Apply homography transformation
        centroid_for_height_measure, flat_centroid = context.placement_workflow.transform_centroids(
            context.vision_service, centroid
        )
        
        # Calculate pickup positions
        pickup_positions, height_measure_position, pickup_height = context.pickup_service.calculate_pickup_positions(
            flat_centroid, 3.0, context.robot_service, orientation, 
            match.gripperID, context.RZ_ORIENTATION
        )
        
        # Store in context for later use
        context.centroid_for_height_measure = centroid_for_height_measure
        context.pickup_positions = pickup_positions
        context.height_measure_position = height_measure_position
        context.pickup_height = pickup_height
        context.current_centroid = centroid
        context.current_orientation = orientation
        
        log_info_message(context.logger_context, "Pickup position calculated successfully")
        return PickAndPlaceState.CALCULATING_PLACEMENT_POSITION
        
    except Exception as e:
        context.record_error(f"Error calculating pickup position: {str(e)}")
        return PickAndPlaceState.ERROR


def calculating_placement_position_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle calculating placement positions for the current workpiece.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.CALCULATING_PLACEMENT_POSITION)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Calculate placement positions
        placement_result = context.placement_service.calculate_placement_positions(
            context.current_match, 
            context.current_centroid, 
            context.current_orientation, 
            context.pickup_height, 
            context.current_match.gripperID
        )
        
        if not placement_result.success:
            if placement_result.plane_full:
                log_info_message(context.logger_context, "⚠️  PLANE FULL: Cannot place more workpieces")
                return PickAndPlaceState.COMPLETED
            else:
                context.record_error(f"Placement calculation failed: {placement_result.message}")
                # Skip this workpiece and try next one
                context.advance_to_next_workpiece()
                return PickAndPlaceState.PROCESSING_WORKPIECE
        
        # Store placement in context
        context.current_placement = placement_result.placement
        context.current_placement.pickup_positions = context.pickup_positions
        
        log_info_message(context.logger_context, "Placement position calculated successfully")
        return PickAndPlaceState.CHANGING_GRIPPER
        
    except Exception as e:
        context.record_error(f"Error calculating placement position: {str(e)}")
        return PickAndPlaceState.ERROR


def executing_pick_and_place_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle executing the pick and place sequence.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.EXECUTING_PICK_AND_PLACE)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Execute the complete placement
        success = context.placement_workflow.execute_workpiece_placement(
            context.current_placement,
            context.robot_service,
            context.laser,
            context.current_match.gripperID,
            context.centroid_for_height_measure
        )
        
        if not success:
            context.record_error("Failed during pick and place sequence")
            return PickAndPlaceState.ERROR
        
        log_info_message(
            context.logger_context, 
            f"Successfully placed workpiece {context.current_match_index + 1}"
        )
        return PickAndPlaceState.UPDATING_DEBUG_INFO
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        context.record_error(f"Error executing pick and place: {str(e)}")
        return PickAndPlaceState.ERROR


def updating_debug_info_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle updating debug information and tracking.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.UPDATING_DEBUG_INFO)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Update tracking
        context.count += 1
        
        # Add placed contour to tracking list for debug plotting
        # Check if current_placement exists
        if context.current_placement and hasattr(context.current_placement, 'contour'):
            context.placed_contours.append({
                'contour': context.current_placement.contour,
                'drop_position': context.current_placement.drop_off_positions.position1.to_list(),
                'dimensions': (context.current_placement.dimensions.width, 
                              context.current_placement.dimensions.height),
                'match_index': context.current_match_index + 1
            })
        else:
            # Fallback: create a simple entry without the placement details
            log_info_message(context.logger_context, "Warning: current_placement is None, using fallback debug info")
            context.placed_contours.append({
                'contour': None,
                'drop_position': [0, 0, 0, 0, 0, 0],  # Placeholder
                'dimensions': (0, 0),  # Placeholder
                'match_index': context.current_match_index + 1
            })
        
        # Save debug plot
        from ...debug import save_nesting_debug_plot
        save_nesting_debug_plot(context.plane, context.placed_contours, context.current_match_index + 1)
        
        log_info_message(
            context.logger_context, 
            f"Debug info updated, total workpieces placed: {context.count}"
        )
        
        # Advance to next workpiece
        context.advance_to_next_workpiece()
        
        # Check if there are more workpieces in the current batch
        if context.has_more_workpieces_in_batch():
            return PickAndPlaceState.PROCESSING_WORKPIECE
        else:
            # No more workpieces in current batch, check for more
            return PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES
        
    except Exception as e:
        context.record_error(f"Error updating debug info: {str(e)}")
        return PickAndPlaceState.ERROR


def checking_for_more_workpieces_handler(context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
    """
    Handle checking if there are more workpieces to process.
    
    Args:
        context: Pick and place context
        
    Returns:
        Next state or None if staying in current state
    """
    try:
        # Check for pause/stop requests
        if context.pause_requested:
            context.request_pause(PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES)
            return PickAndPlaceState.PAUSED
        
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Check if we should continue the operation
        if not context.should_continue_operation():
            # Check the specific reason for stopping
            if context.consecutive_empty_detections >= context.max_empty_detections:
                log_info_message(
                    context.logger_context,
                    f"No workpieces detected after {context.consecutive_empty_detections} consecutive attempts, completing nesting"
                )
            else:
                log_info_message(context.logger_context, "Operation should not continue")
            return PickAndPlaceState.COMPLETED
        
        # Check if plane is full
        if context.is_plane_full():
            log_info_message(context.logger_context, "Plane is full, operation complete")
            return PickAndPlaceState.COMPLETED
        
        # Reset for new cycle and continue
        context.reset_for_new_cycle()
        
        log_info_message(context.logger_context, "Checking for more workpieces...")
        return PickAndPlaceState.MOVING_TO_CAPTURE_POSITION
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        context.record_error(f"Error checking for more workpieces: {str(e)}")
        return PickAndPlaceState.ERROR