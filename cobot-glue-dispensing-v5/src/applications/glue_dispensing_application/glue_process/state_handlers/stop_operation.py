from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from modules.utils.custom_logging import log_debug_message


def stop_operation(glue_dispensing_operation,context,logger_context):
    """Stop current operation"""

    # Safety check: ensure state machine exists
    if not hasattr(context, 'state_machine') or context.state_machine is None:
        log_debug_message(logger_context, message="Cannot stop: state machine not initialized")
        return False, "State machine not initialized"

    if context.state_machine.transition(GlueProcessState.STOPPED):
        # Set flag to indicate operation was stopped (which counts as completion)
        context.operation_just_completed = True
        
        # Stop robot motion
        try:
            context.robot_service.stop_motion()

        except Exception as e:
            log_debug_message(logger_context,
                           message=f"Error stopping robot on pause: {e}")

        # Get motor address for current path
        motor_address = context.get_motor_address_for_current_path()
        if motor_address == -1:
            context.service.generatorOff()
            log_debug_message(logger_context,
                           message=f"Invalid motor address for current path during stop")
            raise RuntimeError(f"Invalid motor address for current path during stop {motor_address}")

        context.pump_controller.pump_off(context.service, context.robot_service, motor_address,
                                         context.current_settings)
        context.service.generatorOff()
        context.pump_controller.pump_off(context.service,context.robot_service,motor_address,context.current_settings)
        context.service.generatorOff()
        log_debug_message(logger_context,
                          message=f"Operation stopped from current state: {context.state_machine.state}")

        context.robot_service.robot_state_manager.trajectoryUpdate = False
        context.robot_service.message_publisher.publish_trajectory_stop_topic()
        return True, "Operation stopped"
    else:
        log_debug_message(logger_context,
                          message=f"Cannot stop from current state: {context.state_machine.state}")
        return False, "Cannot stop from current state"