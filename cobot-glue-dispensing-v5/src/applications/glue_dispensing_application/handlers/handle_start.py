# Action functions
import time
from applications.glue_dispensing_application.handlers.spraying_handler import publish_robot_trajectory, \
    start_path_execution
from core.base_robot_application import ApplicationState
from core.operation_state_management import OperationResult
from frontend.contour_editor.widgets.SegmentSettingsWidget import default_settings
from modules.shared.localization.enums.Message import Message


def start(application, contourMatching=True,nesting= False, debug=False)->OperationResult:
    """
    Main method to start the robotic operation, either performing contour matching and nesting of workpieces
    or directly tracing contours. If contourMatching is False, only contour tracing is performed.
    """
    if contourMatching:
        print(f"Starting in Contour Matching Mode. Nesting: {nesting}, Debug: {debug}")
        result = handle_contour_matching_mode(application, nesting, debug)
    else:
        result = handle_direct_tracing_mode(application)

    # Only move to calibration position if robot service is not stopped/paused
    if application.state not in [ApplicationState.STOPPED, ApplicationState.PAUSED,ApplicationState.ERROR]:
        application.move_to_spray_capture_position()
    # application.state = ApplicationState.IDLE
    return result


def handle_contour_matching_mode(application,nesting,debug)->OperationResult:

    if nesting:
        result = application.start_nesting(debug)
        print(f"start_nesting result: {result}")
        if result.success is False:
            return result

    application.clean_nozzle()
    application.move_to_spray_capture_position()
    application.message_publisher.publish_brightness_region(region="spray")

    workpieces = application.get_workpieces()
    time.sleep(2)  # wait for camera to stabilize
    new_contours = application.visionService.contours
    result,matches = application.workpiece_matcher.perform_matching(workpieces,new_contours,debug)
    print(f"perform_matching result: {result} matches: {matches}")
    if not result:
        return OperationResult(success=False, message=Message.NO_WORKPIECE_DETECTED)

    return application.start_spraying(matches,debug)

def handle_direct_tracing_mode(application):

    # application.clean_nozzle()
    application.move_to_spray_capture_position()
    application.message_publisher.publish_brightness_region(region="spray")
    # ✅ Direct contour tracing without matching
    time.sleep(2)

    newContours = application.visionService.contours
    if newContours is None:
        return OperationResult(success=False, message="No contours found")

    # Transform contours to robot coordinates and convert to proper format
    paths = []
    generator = application.workpiece_to_spray_paths_generator
    for contour in newContours:
        robot_path = generator.contour_to_robot_path( contour, default_settings, 0, 0)
        paths.append((robot_path, default_settings))
        print(f"Final path points No Contour Matching: {len(robot_path)}")

    if paths:
        publish_robot_trajectory(application)
        application.move_to_spray_capture_position()
        start_path_execution(application,paths)

    return OperationResult(success=True, message="Direct tracing mode completed")