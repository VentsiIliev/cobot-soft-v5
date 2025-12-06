"""
Robot Calibration Handler

This handler manages robot calibration operations using the refactored
ExecutableStateMachine-based calibration pipeline for improved modularity,
maintainability, and consistency with other system components.

Updated to use:
- RefactoredRobotCalibrationPipeline (with ExecutableStateMachine)
- Better error handling and state monitoring
- Enhanced logging and debugging capabilities
"""

import threading
import time

from communication_layer.api.v1.topics import RobotTopics
from core.model.settings.robot_calibration_settings import RobotCalibrationSettings
from modules.VisionSystem.laser_detection.height_measuring import HeightMeasuringService
from modules.VisionSystem.laser_detection.laser_detection_service import LaserDetectionService
from modules.VisionSystem.laser_detection.laser_detector import LaserDetector, LaserDetectionConfig
from modules.robot_calibration.newRobotCalibUsingExecutableStateMachine import RefactoredRobotCalibrationPipeline

from modules.shared.MessageBroker import MessageBroker
from modules.robot_calibration.config_helpers import AdaptiveMovementConfig, RobotCalibrationEventsConfig, \
    RobotCalibrationConfig


def get_height_measuring_service(application):
    vs = application.visionService
    rs = application.robotService
    ld = LaserDetector(LaserDetectionConfig())
    lds = LaserDetectionService(detector=ld, laser=application.robotService.tool_manager.get_tool("laser"), vision_service=vs)
    hms = HeightMeasuringService(laser_detection_service=lds, robot_service=rs)
    return hms

def calibrate_robot(application,robot_calibration_settings:RobotCalibrationSettings):

        print(f"calibration_robot: Starting calibration with settings: {robot_calibration_settings.to_dict()}")

        try:

            adaptive_movement_config = AdaptiveMovementConfig(
                min_step_mm=robot_calibration_settings.min_step_mm, # minimum movement (for very small errors)
                max_step_mm=robot_calibration_settings.max_step_mm,# maximum movement for very large misalignment's
                target_error_mm=robot_calibration_settings.target_error_mm, # desired error to reach
                max_error_ref=robot_calibration_settings.max_error_ref, # error at which we reach max step
                k=robot_calibration_settings.k, # responsiveness (1.0 = smooth, 2.0 = faster reaction)
                derivative_scaling=robot_calibration_settings.derivative_scaling # how strongly derivative term reduces step
            )

            robot_events_config = RobotCalibrationEventsConfig(
                broker=MessageBroker(),
                calibration_start_topic=RobotTopics.ROBOT_CALIBRATION_START,
                calibration_log_topic=RobotTopics.ROBOT_CALIBRATION_LOG,
                calibration_image_topic=RobotTopics.ROBOT_CALIBRATION_IMAGE,
                calibration_stop_topic=RobotTopics.ROBOT_CALIBRATION_STOP,
            )
            height_measuring_service = get_height_measuring_service(application)

            config = RobotCalibrationConfig(
                vision_system=application.visionService,
                robot_service=application.robotService,
                height_measuring_service=height_measuring_service,
                required_ids=set(robot_calibration_settings.required_ids),
                z_target=robot_calibration_settings.z_target,# height for refined marker search
                debug=False,
                step_by_step=False,
                live_visualization=False
            )

            robot_calib_pipeline = RefactoredRobotCalibrationPipeline(config=config,
                                                                      events_config=robot_events_config,
                                                                      adaptive_movement_config=adaptive_movement_config)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Failed to initialize calibration pipeline: {e}", None

        application.visionService.drawContours = False
        
        # Create a thread wrapper that handles the ExecutableStateMachine properly
        def calibration_thread_worker():
            """Worker function for calibration thread with proper error handling"""
            try:
                print("=== Starting ExecutableStateMachine-based Robot Calibration ===")
                success = robot_calib_pipeline.run()
                
                if success:
                    print("✅ Robot calibration completed successfully!")
                    # Get final state and context for debugging
                    final_state = robot_calib_pipeline.get_state_machine().current_state
                    context = robot_calib_pipeline.get_context()
                    print(f"Final state: {final_state}")
                    print(f"Processed {len(context.robot_positions_for_calibration)} markers")
                else:
                    print("❌ Robot calibration failed!")
                    
            except Exception as e:
                print(f"❌ Robot calibration thread error: {e}")
                import traceback
                traceback.print_exc()
        
        # Start calibration in background thread
        print("About to start ExecutableStateMachine calibration thread...")
        calibration_thread = threading.Thread(target=calibration_thread_worker, daemon=False)
        print(f"Created thread: {calibration_thread}")
        calibration_thread.start()
        print(f"Thread started: {calibration_thread.is_alive()}")
        
        # Store reference for potential monitoring/cancellation
        robot_calib_pipeline._calibration_thread = calibration_thread
        
        message = "ExecutableStateMachine-based calibration started in background thread"
        image = None
        return True, message, image


def get_calibration_status(robot_calib_pipeline):
    """
    Get the current status of the robot calibration process.
    
    This function leverages the ExecutableStateMachine to provide
    real-time status information about the calibration progress.
    
    Args:
        robot_calib_pipeline: RefactoredRobotCalibrationPipeline instance
        
    Returns:
        dict: Status information including current state, progress, and timing
    """
    try:
        state_machine = robot_calib_pipeline.get_state_machine()
        context = robot_calib_pipeline.get_context()
        
        # Calculate progress
        total_markers = len(context.required_ids) if context.required_ids else 0
        current_marker = context.current_marker_id
        markers_completed = len(context.robot_positions_for_calibration)
        progress_percentage = (markers_completed / total_markers * 100) if total_markers > 0 else 0
        
        # Get timing information
        total_time = 0
        if context.total_calibration_start_time:
            total_time = time.time() - context.total_calibration_start_time
        
        status = {
            "current_state": state_machine.current_state.name if state_machine.current_state else "UNKNOWN",
            "is_running": not state_machine._stop_requested,
            "total_markers": total_markers,
            "current_marker_id": current_marker,
            "markers_completed": markers_completed,
            "progress_percentage": round(progress_percentage, 1),
            "total_time_seconds": round(total_time, 2),
            "state_timings": context.state_timings,
            "has_error": state_machine.current_state.name == "ERROR" if state_machine.current_state else False,
            "thread_alive": getattr(robot_calib_pipeline, '_calibration_thread', None) and 
                           robot_calib_pipeline._calibration_thread.is_alive(),
        }
        
        return status
        
    except Exception as e:
        return {
            "error": f"Failed to get calibration status: {e}",
            "current_state": "UNKNOWN",
            "is_running": False,
        }


def stop_calibration(robot_calib_pipeline):
    """
    Stop the robot calibration process.
    
    This function uses the ExecutableStateMachine's stop mechanism
    to gracefully terminate the calibration process.
    
    Args:
        robot_calib_pipeline: RefactoredRobotCalibrationPipeline instance
        
    Returns:
        bool: True if stop was initiated successfully
    """
    try:
        state_machine = robot_calib_pipeline.get_state_machine()
        state_machine.stop_execution()
        
        print("🛑 Robot calibration stop requested")
        return True
        
    except Exception as e:
        print(f"❌ Failed to stop calibration: {e}")
        return False
