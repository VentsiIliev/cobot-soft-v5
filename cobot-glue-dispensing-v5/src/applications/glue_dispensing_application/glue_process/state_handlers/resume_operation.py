from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from modules.utils.custom_logging import log_debug_message


def resume_operation(context,logger_context):
    """Resume operation from paused state"""
    
    # Safety check: ensure state machine exists
    if not hasattr(context, 'state_machine') or context.state_machine is None:
        log_debug_message(logger_context, message="Cannot resume: state machine not initialized")
        return False, "State machine not initialized"
    
    if context.state_machine.state != GlueProcessState.PAUSED:
        log_debug_message(logger_context,
                          message=f"Cannot resume - not in paused state current state: {context.state_machine.state}")
        return False, "Cannot resume - not in paused state"

    if not context.has_valid_context():
        log_debug_message(logger_context, message=f"Cannot resume - no execution context.")
        return False, "Cannot resume - no execution context"

    log_debug_message(logger_context, message=f"Resuming from paused state")
    # Set the resume flag so the execution thread knows to resume
    context.is_resuming = True
    # Just transition to STARTING - the existing execution thread will handle it
    if context.state_machine.transition(GlueProcessState.STARTING):
        log_debug_message(logger_context, message=f"Operation resumed")
        return True, "Operation resumed"
    else:
        log_debug_message(logger_context, message=f"Cannot resume - invalid state transition")
        return False, "Cannot resume - invalid state transition"