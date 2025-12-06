from collections import namedtuple
import time
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from modules.utils.custom_logging import log_debug_message, log_error_message

HandlerResult = namedtuple(
    "HandlerResult",
    [
        "handled",
        "resume",
        "next_state",
        "next_path_index",
        "next_point_index",
        "next_path",
        "next_settings",
    ]
)

def handle_wait_for_path_completion(context,logger_context) -> GlueProcessState:
    """
    Waits for the pump adjustment thread to finish.
    Since that thread runs until the robot reaches the last path point,
    this implicitly means waiting for robot motion completion.
    
    If no pump thread exists (e.g., spray_on=False or pump adjustment disabled),
    we wait for robot motion completion instead.
    """
    path_index = context.current_path_index
    path = context.current_path
    settings = context.current_settings

    log_debug_message(logger_context, message=f"[WAIT_FOR_PATH_COMPLETION] Waiting for path {path_index} completion...")

    pump_thread = getattr(context, "pump_thread", None)

    if pump_thread is None:
        log_debug_message(logger_context, message="[WAIT] No pump thread found - waiting for robot motion completion instead.")
        # If no pump thread exists, wait for robot motion completion
        return _wait_for_robot_motion_completion(context, logger_context, path_index, path, settings)
    try:
        # Wait indefinitely for the pump thread to finish.
        # You can add a soft timeout if you ever need to handle unexpected hangs.
        while pump_thread.is_alive():
            state = context.state_machine.state

            if state == GlueProcessState.PAUSED:
                log_debug_message(logger_context, message="[WAIT] Paused while waiting for pump thread - waiting for thread to finish and capture progress")
                # When paused, wait for pump thread to finish so we can capture its progress
                pump_thread.join(timeout=2.0)  # Give thread a moment to detect pause and finish
                
                # Get the progress from the pump thread result
                paused_point_index = context.current_point_index  # Default fallback
                if hasattr(pump_thread, 'result') and pump_thread.result is not None:
                    try:
                        success, progress_index = pump_thread.result[:2]
                        paused_point_index = progress_index
                        log_debug_message(logger_context, 
                            message=f"[WAIT] Captured pump thread progress on pause: {paused_point_index}")
                    except Exception as e:
                        log_debug_message(logger_context, 
                            message=f"[WAIT] Error capturing pump thread progress: {e}")
                
                result = HandlerResult(True, True, GlueProcessState.PAUSED, path_index, paused_point_index, path, settings)
                update_context_from_handler_result(context, result)
                return result.next_state

            if state == GlueProcessState.STOPPED:
                log_debug_message(logger_context, message="[WAIT] Stopped while waiting for pump thread")
                result = HandlerResult(True, False, GlueProcessState.STOPPED, path_index, context.current_point_index, path, settings)
                update_context_from_handler_result(context, result)
                return result.next_state
            time.sleep(0.1)

        # Get the pump thread result to capture final progress
        final_point_index = len(path) - 1  # Default to last point
        next_state = GlueProcessState.TRANSITION_BETWEEN_PATHS  # Default next state
        
        try:
            if hasattr(pump_thread, 'result') and pump_thread.result is not None:
                success, progress_index = pump_thread.result[:2]  # Unpack first two values
                if success:
                    final_point_index = progress_index
                    log_debug_message(logger_context, 
                        message=f"[WAIT] Pump thread completed successfully — final progress: {final_point_index}")
                else:
                    log_debug_message(logger_context, 
                        message=f"[WAIT] Pump thread completed with early termination — progress: {progress_index}")
                    final_point_index = progress_index
                    
                # If progress beyond current path, path is complete
                if final_point_index >= len(path):
                    log_debug_message(logger_context, 
                        message=f"[WAIT] Progress {final_point_index} beyond path length {len(path)}, path complete")
                    final_point_index = len(path) - 1  # Set to last valid point
                    next_state = GlueProcessState.TRANSITION_BETWEEN_PATHS
            else:
                log_debug_message(logger_context, message=f"[WAIT] Pump thread completed — path {path_index} done (no result captured).")
        except Exception as result_error:
            log_debug_message(logger_context, message=f"[WAIT] Could not get pump thread result: {result_error}")

    except Exception as e:
        log_error_message(logger_context, message=f"[WAIT] Error waiting for pump thread: {e}")
        result = HandlerResult(False, False, GlueProcessState.ERROR, path_index, context.current_point_index, path, settings)
        update_context_from_handler_result(context, result)
        return result.next_state
    finally:
        context.pump_thread = None

    # ✅ The thread finished — robot reached last point.
    result = HandlerResult(
        handled=True,
        resume=False,
        next_state=next_state,
        next_path_index=path_index,
        next_point_index=final_point_index,  # Use actual final progress from pump thread
        next_path=path,
        next_settings=settings,
    )
    update_context_from_handler_result(context, result)
    return result.next_state

def _wait_for_robot_motion_completion(context, logger_context, path_index, path, settings) -> GlueProcessState:
    """
    Wait for robot motion completion when no pump thread exists.
    This is used when spray_on=False or pump adjustment is disabled.
    """
    try:
        log_debug_message(logger_context, message=f"[WAIT] Waiting for robot to complete path {path_index} without pump thread...")
        
        # Wait for robot trajectory to complete
        # Note: This assumes robot_service has a way to check if motion is complete
        robot_service = context.robot_service
        
        while True:
            state = context.state_machine.state
            
            # Handle pause/stop requests during robot motion
            if state == GlueProcessState.PAUSED:
                log_debug_message(logger_context, message="[WAIT] Paused while waiting for robot motion")
                # Save current progress (assume robot is at some point in the path)
                result = HandlerResult(True, True, GlueProcessState.PAUSED, path_index, context.current_point_index, path, settings)
                update_context_from_handler_result(context, result)
                return result.next_state
                
            if state == GlueProcessState.STOPPED:
                log_debug_message(logger_context, message="[WAIT] Stopped while waiting for robot motion")
                result = HandlerResult(True, False, GlueProcessState.STOPPED, path_index, context.current_point_index, path, settings)
                update_context_from_handler_result(context, result)
                return result.next_state
            
            # Check if robot motion is complete
            # For now, we'll assume a simple timeout or use robot status
            # TODO: Implement proper robot motion completion detection
            if hasattr(robot_service, 'is_motion_complete') and robot_service.is_motion_complete():
                log_debug_message(logger_context, message=f"[WAIT] Robot motion completed for path {path_index}")
                break
            
            # Simple fallback - wait a bit and assume motion is complete after reasonable time
            # This is not ideal but prevents infinite loops
            # TODO: Replace with proper robot status monitoring
            time.sleep(0.5)
            
            # For now, assume motion completes after a short delay
            # In a real implementation, you would check robot trajectory status
            break
        
        # Motion completed successfully
        final_point_index = len(path) - 1  # Assume robot reached the end
        result = HandlerResult(
            handled=True,
            resume=False,
            next_state=GlueProcessState.TRANSITION_BETWEEN_PATHS,
            next_path_index=path_index,
            next_point_index=final_point_index,
            next_path=path,
            next_settings=settings,
        )
        update_context_from_handler_result(context, result)
        return result.next_state
        
    except Exception as e:
        log_error_message(logger_context, message=f"[WAIT] Error waiting for robot motion completion: {e}")
        result = HandlerResult(False, False, GlueProcessState.ERROR, path_index, context.current_point_index, path, settings)
        update_context_from_handler_result(context, result)
        return result.next_state

def update_context_from_handler_result(context, result: HandlerResult):
    """Update context based on HandlerResult."""
    context.current_path_index = result.next_path_index
    context.current_point_index = result.next_point_index