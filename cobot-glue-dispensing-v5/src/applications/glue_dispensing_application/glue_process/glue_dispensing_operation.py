import json
import os
from datetime import datetime

from applications.glue_dispensing_application.glue_process.state_handlers.compleated_state_handler import \
    handle_completed_state
from applications.glue_dispensing_application.glue_process.state_handlers.initial_pump_boost_state_handler import \
    handle_pump_initial_boost
from applications.glue_dispensing_application.glue_process.state_handlers.moving_to_first_point_state_handler import \
    handle_moving_to_first_point_state
from applications.glue_dispensing_application.glue_process.state_handlers.pause_operation import pause_operation
from applications.glue_dispensing_application.glue_process.state_handlers.resume_operation import resume_operation
from applications.glue_dispensing_application.glue_process.state_handlers.sending_path_to_robot_state_handler import \
    handle_send_path_to_robot
from applications.glue_dispensing_application.glue_process.state_handlers.start_pump_adjustment_thread_handler import \
    handle_start_pump_adjustment_thread
from applications.glue_dispensing_application.glue_process.state_handlers.start_state_handler import \
    handle_starting_state
from applications.glue_dispensing_application.glue_process.state_handlers.stop_operation import stop_operation
from applications.glue_dispensing_application.glue_process.state_handlers.transition_between_paths_state_handler import \
    handle_transition_between_paths
from applications.glue_dispensing_application.glue_process.state_handlers.wait_for_path_completion_state_handler import \
    handle_wait_for_path_completion

from applications.glue_dispensing_application.glue_process.state_machine.ExecutableStateMachine import \
    ExecutableStateMachine, StateRegistry, State, ExecutableStateMachineBuilder
from applications.glue_dispensing_application.glue_process.ExecutionContext import ExecutionContext
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings

from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState, \
    GlueProcessTransitionRules

from modules.utils.custom_logging import log_debug_message, log_error_message, \
    log_calls_with_timestamp_decorator, setup_logger, LoggerContext
from applications.glue_dispensing_application.glue_process.PumpController import PumpController
from communication_layer.api.v1.topics import GlueTopics
from core.operation_state_management import OperationResult, IOperation
from modules.shared.MessageBroker import MessageBroker

# glue dispensing process configuration
USE_SEGMENT_SETTINGS = True
TURN_OFF_PUMP_BETWEEN_PATHS = True
ADJUST_PUMP_SPEED_WHILE_SPRAY = True

# logging configuration
ENABLE_GLUE_DISPENSING_LOGGING = True
glue_dispensing_logger = setup_logger("Glue Dispensing") if ENABLE_GLUE_DISPENSING_LOGGING else None
glue_dispensing_logger_context = LoggerContext(enabled=ENABLE_GLUE_DISPENSING_LOGGING, logger=glue_dispensing_logger)

# debug configuration
ENABLE_CONTEXT_DEBUG = True
DEBUG_DIR = os.path.join(os.path.dirname(__file__), "debug")

class GlueDispensingOperation(IOperation):
    def __init__(self, robot_service, glue_service, glue_application=None):
        super().__init__()
        self.robot_service = robot_service
        self.glue_application = glue_application
        self.glue_service = glue_service
        self.broker=MessageBroker()
        # Get glue settings from the glue application
        if glue_application is not None:
            glue_settings = glue_application.get_glue_settings()
        else:
            # Fallback to default settings if no application provided
            glue_settings = GlueSettings()

        self.glue_service.settings = glue_settings
        self.pump_controller = PumpController(USE_SEGMENT_SETTINGS, glue_dispensing_logger_context, glue_settings)
        self.execution_context = ExecutionContext()
        self.glue_process_state_machine = self.get_state_machine()

        # Create debug directory if it doesn't exist
        if ENABLE_CONTEXT_DEBUG:
            os.makedirs(DEBUG_DIR, exist_ok=True)

    def _write_context_debug(self, state_name: str):
        """
        Write execution context to debug file after state execution.

        Args:
            state_name: Name of the state that just completed
        """
        if not ENABLE_CONTEXT_DEBUG:
            return

        try:
            # Create debug directory if it doesn't exist
            os.makedirs(DEBUG_DIR, exist_ok=True)

            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            # Get context as dict
            context_dict = self.execution_context.to_debug_dict()

            # Add metadata
            debug_data = {
                "timestamp": timestamp,
                "state": state_name,
                "context": context_dict
            }

            # Generate filename
            filename = f"{timestamp}_{state_name}.json"
            filepath = os.path.join(DEBUG_DIR, filename)

            # Write to file
            with open(filepath, 'w') as f:
                json.dump(debug_data, f, indent=2, default=str)


        except Exception as e:
            log_error_message(
                glue_dispensing_logger_context,
                message=f"Failed to write debug context: {e}"
            )

    def setup_execution_context(self, paths, spray_on):
        self.execution_context.reset()
        self.execution_context.paths = paths
        self.execution_context.spray_on = spray_on
        self.execution_context.service = self.glue_service
        self.execution_context.robot_service = self.robot_service
        self.execution_context.state_machine = self.glue_process_state_machine
        self.execution_context.operation = self  # ✅ Store reference to operation for completion
        self.execution_context.glue_type = self.glue_service.glueA_addresses
        self.execution_context.current_path_index = 0
        self.execution_context.current_point_index = 0
        self.execution_context.is_resuming = False
        self.execution_context.current_settings = None
        self.execution_context.pump_controller = self.pump_controller

        # ✅ Add these for pump adjustment
        self.execution_context.pump_thread = None
        self.execution_context.pump_ready_event = None

    @log_calls_with_timestamp_decorator(enabled=ENABLE_GLUE_DISPENSING_LOGGING, logger=glue_dispensing_logger)
    def _do_start(self, paths, spray_on=False, resume=False) -> OperationResult:
        try:
            if resume is False or not self.execution_context.has_valid_context():
                self.setup_execution_context(paths, spray_on)
                # Transition to start
                if self.execution_context.state_machine.state == GlueProcessState.IDLE:
                    self.execution_context.state_machine.transition(GlueProcessState.STARTING)

            # Start execution loop (non-blocking if needed, blocking here)
            self.execution_context.state_machine.start_execution(delay=0.2)

            return OperationResult(True, "Execution completed")

        except Exception as e:
            log_error_message(glue_dispensing_logger_context, message=f"Error during execution: {e}")
            self.execution_context.state_machine.transition(GlueProcessState.ERROR)
            return OperationResult(False, "Execution error", error=str(e))

    def _do_pause(self)->OperationResult:
        return pause_operation(self, self.execution_context,glue_dispensing_logger_context)

    def _do_stop(self)->OperationResult:
        return stop_operation(self, self.execution_context,glue_dispensing_logger_context)

    def _do_resume(self)->OperationResult:
        """Resume operation from paused state"""
        return resume_operation(self.execution_context,glue_dispensing_logger_context)

    def _resume_execution(self):
        """Resume execution from saved context"""

        try:
            paths = self.execution_context.paths
            spray_on = self.execution_context.spray_on
            self.start(paths, spray_on, resume=True)
        except Exception as e:
            log_debug_message(glue_dispensing_logger_context, message=f"Error during resume execution: {e}")
            self.execution_context.state_machine.transition(GlueProcessState.ERROR)

    def _handle_starting_state(self, context):

        # Return whatever the handler returns so the caller can update its local execution context variables
        return handle_starting_state(context,glue_dispensing_logger_context)

    def _handle_moving_to_first_point_state(self, context, resume):

        return handle_moving_to_first_point_state(context, resume)

    def _handle_transition_between_paths(self, context):

        return handle_transition_between_paths(context,glue_dispensing_logger_context,TURN_OFF_PUMP_BETWEEN_PATHS)

    def _handle_pump_initial_boost(self, context):

        return handle_pump_initial_boost(context,glue_dispensing_logger_context)

    def _handle_start_pump_adjustment_thread(self, execution_context):

        return handle_start_pump_adjustment_thread(execution_context,glue_dispensing_logger_context,ADJUST_PUMP_SPEED_WHILE_SPRAY)

    def _handle_send_path_to_robot_state(self, execution_context):

        return handle_send_path_to_robot(execution_context,glue_dispensing_logger_context)

    def _handle_wait_for_path_completion(self, execution_context):

        return handle_wait_for_path_completion(execution_context,glue_dispensing_logger_context)

    def _handle_completed_state(self, context):
        return handle_completed_state(context)

    def _handle_idle_state(self, context):
        """Handle IDLE state - truly idle, only stop if operation just completed"""
        operation_just_completed = getattr(context, 'operation_just_completed', False)
        print(f"[IDLE_HANDLER] operation_just_completed = {operation_just_completed}")
        
        if operation_just_completed:
            print("[IDLE_HANDLER] Operation just completed - marking completion in IOperation")
            self._mark_completed()
            
            print("[IDLE_HANDLER] Stopping execution...")
            context.state_machine.stop_execution()
            
        return None  # Stay in IDLE

    def get_state_machine(self)->ExecutableStateMachine:
        transition_rules = GlueProcessTransitionRules.get_glue_transition_rules()
        # Register all states and link to their respective handler functions
        state_handlers_map = {
            GlueProcessState.IDLE: self._handle_idle_state,  # IDLE state stops execution when operation is complete
            GlueProcessState.STARTING: self._handle_starting_state,
            GlueProcessState.MOVING_TO_FIRST_POINT: lambda ctx: self._handle_moving_to_first_point_state(ctx,
                                                                                                         resume=False),
            GlueProcessState.EXECUTING_PATH: lambda ctx: GlueProcessState.PUMP_INITIAL_BOOST,
            GlueProcessState.PUMP_INITIAL_BOOST: self._handle_pump_initial_boost,
            GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD: self._handle_start_pump_adjustment_thread,
            GlueProcessState.SENDING_PATH_POINTS: self._handle_send_path_to_robot_state,
            GlueProcessState.WAIT_FOR_PATH_COMPLETION: self._handle_wait_for_path_completion,
            GlueProcessState.TRANSITION_BETWEEN_PATHS: self._handle_transition_between_paths,
            GlueProcessState.PAUSED: lambda ctx: GlueProcessState.PAUSED,
            GlueProcessState.STOPPED: lambda ctx: GlueProcessState.COMPLETED,
            GlueProcessState.ERROR: lambda ctx: GlueProcessState.ERROR,
            GlueProcessState.COMPLETED: self._handle_completed_state,
            GlueProcessState.INITIALIZING: lambda ctx: GlueProcessState.IDLE,
        }
        registry = StateRegistry()
        # Create and register State objects
        for state_enum, handler in state_handlers_map.items():
            registry.register_state(State(
                state=state_enum,
                handler=handler,
                on_enter=lambda ctx, s=state_enum: self._write_context_debug(f"{s.name}_ENTER"),
                on_exit=lambda ctx, s=state_enum: self._write_context_debug(f"{s.name}_EXIT")
            ))

        # Build the executable state machine
        transition_rules = GlueProcessTransitionRules.get_glue_transition_rules()
        state_machine = (
            ExecutableStateMachineBuilder()
        .with_initial_state(GlueProcessState.IDLE)
        .with_transition_rules(transition_rules)
        .with_state_registry(registry)
        .with_context(self.execution_context)
        .with_state_topic(GlueTopics.PROCESS_STATE)
        .build()
        )

        return state_machine

