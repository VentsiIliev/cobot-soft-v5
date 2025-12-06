"""
Remaining State Handlers for Robot Calibration

This module contains the remaining state handlers that were extracted from
the main calibration pipeline. For brevity, they are combined here but
should be separated into individual files in a full refactoring.
"""

import time
import numpy as np
import cv2

from modules.utils.custom_logging import log_debug_message, log_error_message
from modules.robot_calibration.states.robot_calibration_states import RobotCalibrationStates
from modules.robot_calibration.logging import (
    construct_align_robot_log_message,
    construct_iterative_alignment_log_message
)
from modules.robot_calibration.states.looking_for_aruco_markers_handler import show_live_feed


def handle_align_robot_state(context) -> RobotCalibrationStates:
    """
    Handle the ALIGN_ROBOT state.
    
    This state moves the robot to align with the current marker being calibrated.
    """
    required_ids_list = sorted(list(context.required_ids))
    marker_id = required_ids_list[context.current_marker_id]
    context.iteration_count = 0

    # Get marker offset and apply image-to-robot mapping
    calib_to_marker = context.markers_offsets_mm.get(marker_id, (0, 0))
    calib_to_marker_mapped = context.image_to_robot_mapping.map(
        calib_to_marker[0],
        calib_to_marker[1]
    )
    calib_to_marker = calib_to_marker_mapped

    print(f"calib_to_marker for ID {marker_id}: {calib_to_marker}")
    current_pose = context.calibration_robot_controller.get_current_position()
    calib_pose = context.calibration_robot_controller.get_calibration_position()
    retry_attempted = False

    # Compute new target position
    x, y, z, rx, ry, rz = current_pose
    cx, cy, cz, crx, cry, crz = calib_pose

    calib_to_current = (x - cx, y - cy)
    current_to_marker = (
        calib_to_marker[0] - calib_to_current[0],
        calib_to_marker[1] - calib_to_current[1]
    )

    x_new = x + current_to_marker[0]
    y_new = y + current_to_marker[1]
    z_new = context.Z_target
    new_position = [x_new, y_new, z_new, rx, ry, rz]

    # Move to position
    result = context.calibration_robot_controller.move_to_position(new_position, blocking=True)

    # Retry if failed
    if result != 0:
        retry_attempted = True
        if len(context.robot_positions_for_calibration) != 0:
            context.calibration_robot_controller.move_to_position(
                context.robot_positions_for_calibration[0], blocking=False
            )
        result = context.calibration_robot_controller.move_to_position(new_position, blocking=True)
        
        if result != 0:
            # Robot movement failed after retry
            log_error_message(
                context.logger_context,
                f"Robot movement failed for marker {marker_id} after retry attempt. "
                f"Target position: {new_position}. Movement result: {result}"
            )
            # Store specific error details for UI notification
            context.calibration_error_message = (
                f"Robot movement failed for marker {marker_id}. "
                f"Could not reach target position after retry. "
                f"Check robot safety limits and workspace boundaries."
            )
            return RobotCalibrationStates.ERROR

    # Log the alignment operation
    message = construct_align_robot_log_message(
        marker_id=marker_id,
        calib_to_marker=calib_to_marker,
        current_pose=current_pose,
        calib_pose=calib_pose,
        z_target=context.Z_target,
        result=result,
        retry_attempted=retry_attempted,
    )
    log_debug_message(context.logger_context, message)

    if result == 0:
        time.sleep(1)
        return RobotCalibrationStates.ITERATE_ALIGNMENT
    else:
        return RobotCalibrationStates.ERROR


def handle_iterate_alignment_state(context) -> RobotCalibrationStates:
    """
    Handle the ITERATE_ALIGNMENT state.
    
    This state iteratively refines the robot position until the marker
    is aligned with the image center within the specified threshold.
    """
    required_ids_list = sorted(list(context.required_ids))
    marker_id = required_ids_list[context.current_marker_id]
    context.iteration_count += 1

    if context.iteration_count > context.max_iterations:
        # Maximum iterations exceeded - this is a calibration failure
        log_error_message(
            context.logger_context,
            f"Maximum iterations ({context.max_iterations}) exceeded for marker {marker_id}. "
            f"Robot failed to align with marker within threshold ({context.alignment_threshold_mm}mm). "
            f"Stopping calibration process."
        )
        # Store error details for UI notification
        context.calibration_error_message = (
            f"Calibration failed: Could not align with marker {marker_id} "
            f"after {context.max_iterations} iterations. "
            f"Required precision: {context.alignment_threshold_mm}mm"
        )
        return RobotCalibrationStates.ERROR

    # Capture frame
    capture_start = time.time()
    iteration_image = None
    while iteration_image is None:
        iteration_image = context.system.getLatestFrame()
    capture_time = time.time() - capture_start

    # Detect marker
    detection_start = time.time()
    result = context.calibration_vision.detect_specific_marker(iteration_image, marker_id)
    marker_found = result.found
    arucoCorners = result.aruco_corners
    arucoIds = result.aruco_ids
    detection_time = time.time() - detection_start

    if not marker_found:
        log_debug_message(
            context.logger_context,
            f"Marker {marker_id} not found during iteration {context.iteration_count}!"
        )
        return RobotCalibrationStates.ITERATE_ALIGNMENT  # Stay in state

    # Process and compute error
    processing_start = time.time()
    context.calibration_vision.update_marker_top_left_corners(marker_id, arucoCorners, arucoIds)
    
    image_center_px = (
        context.system.camera_settings.get_camera_width() // 2,
        context.system.camera_settings.get_camera_height() // 2
    )

    marker_top_left_px = context.calibration_vision.marker_top_left_corners[marker_id]
    offset_x_px = marker_top_left_px[0] - image_center_px[0]
    offset_y_px = marker_top_left_px[1] - image_center_px[1]
    current_error_px = np.sqrt(offset_x_px ** 2 + offset_y_px ** 2)
    
    newPpm = context.calibration_vision.PPM * context.ppm_scale
    current_error_mm = current_error_px / newPpm
    offset_x_mm = offset_x_px / newPpm
    offset_y_mm = offset_y_px / newPpm
    processing_time = time.time() - processing_start

    alignment_success = current_error_mm <= context.alignment_threshold_mm
    movement_time = stability_time = None
    result = None

    if alignment_success:
        # Store pose and complete this marker
        start_time = time.time()
        while time.time() - start_time < 1.0:
            current_pose = context.calibration_robot_controller.get_current_position()
            time.sleep(0.05)

        context.robot_positions_for_calibration[marker_id] = current_pose
        context.debug_draw.draw_image_center(iteration_image)
        show_live_feed(context, iteration_image, current_error_mm, broadcast_image=context.broadcast_events)
        
        # return RobotCalibrationStates.DONE
        return RobotCalibrationStates.SAMPLE_HEIGHT
    else:
        # Compute next move
        mapped_x_mm, mapped_y_mm = context.image_to_robot_mapping.map(offset_x_mm, offset_y_mm)
        log_debug_message(
            context.logger_context,
            f"Marker {marker_id} offsets: image_mm=({offset_x_mm:.2f},{offset_y_mm:.2f}) -> "
            f"mapped_robot_mm=({mapped_x_mm:.2f},{mapped_y_mm:.2f})"
        )
        
        iterative_position = context.calibration_robot_controller.get_iterative_align_position(
            current_error_mm, mapped_x_mm, mapped_y_mm, context.alignment_threshold_mm
        )
        
        movement_start = time.time()
        result = context.calibration_robot_controller.move_to_position(iterative_position, blocking=True)
        movement_time = time.time() - movement_start
        
        # Check if iterative movement failed
        if result != 0:
            log_error_message(
                context.logger_context,
                f"Iterative robot movement failed for marker {marker_id} during iteration {context.iteration_count}. "
                f"Movement result: {result}"
            )
            # Store specific error details for UI notification
            context.calibration_error_message = (
                f"Robot movement failed during fine alignment of marker {marker_id}. "
                f"Iteration {context.iteration_count}/{context.max_iterations}. "
                f"Check robot connectivity and safety systems."
            )
            return RobotCalibrationStates.ERROR

        # Stability wait
        stability_start = time.time()
        time.sleep(context.fast_iteration_wait)
        stability_time = time.time() - stability_start
        
        context.debug_draw.draw_image_center(iteration_image)
        show_live_feed(context, iteration_image, current_error_mm, broadcast_image=context.broadcast_events)

    # Log iteration results
    message = construct_iterative_alignment_log_message(
        marker_id=marker_id,
        iteration=context.iteration_count,
        max_iterations=context.max_iterations,
        capture_time=capture_time,
        detection_time=detection_time,
        processing_time=processing_time,
        movement_time=movement_time,
        stability_time=stability_time,
        current_error_mm=current_error_mm,
        current_error_px=current_error_px,
        offset_mm=(offset_x_mm, offset_y_mm),
        threshold_mm=context.alignment_threshold_mm,
        alignment_success=alignment_success,
        result=result
    )
    log_debug_message(context.logger_context, message)

    return RobotCalibrationStates.ITERATE_ALIGNMENT


def handle_done_state(context) -> RobotCalibrationStates:
    """
    Handle the DONE state.
    
    This state manages the transition between markers and final completion.
    """
    if context.current_marker_id < len(context.required_ids) - 1:
        # Move to next marker
        context.current_marker_id += 1
        return RobotCalibrationStates.ALIGN_ROBOT
    else:
        # All markers processed - complete calibration
        log_debug_message(
            context.logger_context,
            "All markers processed, proceeding to homography computation..."
        )
        return RobotCalibrationStates.DONE  # Final completion


def handle_error_state(context) -> RobotCalibrationStates:
    """
    Handle the ERROR state.
    
    This state logs the error, sends UI notification, and stops the calibration process.
    """
    # Get specific error message or use default
    error_message = getattr(context, 'calibration_error_message', None) or "An unknown error occurred during calibration"
    
    # Log detailed error information
    log_error_message(
        context.logger_context,
        f"CALIBRATION FAILED: {error_message}"
    )
    
    # Log additional context for debugging
    log_error_message(
        context.logger_context,
        f"Calibration context: "
        f"Current marker: {context.current_marker_id}/{len(context.required_ids) if context.required_ids else 0}, "
        f"Iteration: {context.iteration_count}/{context.max_iterations}, "
        f"Markers successfully calibrated: {len(context.robot_positions_for_calibration)}"
    )
    
    # Send UI notification via message broker if available
    if context.broadcast_events and context.broker and hasattr(context, 'CALIBRATION_STOP_TOPIC'):
        try:
            # Create structured error notification
            error_notification = {
                "status": "error",
                "message": error_message,
                "details": {
                    "current_marker": context.current_marker_id,
                    "total_markers": len(context.required_ids) if context.required_ids else 0,
                    "successful_markers": len(context.robot_positions_for_calibration),
                    "iteration_count": context.iteration_count,
                    "max_iterations": context.max_iterations
                }
            }
            
            # Broadcast error notification to UI
            context.broker.publish(context.CALIBRATION_STOP_TOPIC, error_notification)
            
            log_debug_message(
                context.logger_context,
                f"Error notification sent to UI via topic: {context.CALIBRATION_STOP_TOPIC}"
            )
            
        except Exception as e:
            log_error_message(
                context.logger_context,
                f"Failed to send error notification to UI: {e}"
            )
    
    return RobotCalibrationStates.ERROR  # Stay in error state