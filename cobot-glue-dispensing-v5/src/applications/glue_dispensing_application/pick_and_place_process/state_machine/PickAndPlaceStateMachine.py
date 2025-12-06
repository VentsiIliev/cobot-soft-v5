"""
Pick and Place State Machine Implementation

This module provides the complete state machine implementation for the pick and place process,
with full pause/resume/stop control capabilities.
"""

from typing import Optional, Dict
from modules.utils.custom_logging import setup_logger, LoggerContext, log_info_message

from applications.glue_dispensing_application.glue_process.state_machine.ExecutableStateMachine import (
    ExecutableStateMachine, ExecutableStateMachineBuilder, StateRegistry, State
)
from modules.shared.MessageBroker import MessageBroker

from .PickAndPlaceState import PickAndPlaceState, PickAndPlaceTransitionRules
from .PickAndPlaceContext import PickAndPlaceContext
from .state_handlers.vision_state_handlers import (
    moving_to_capture_position_handler,
    setting_up_vision_handler,
    detecting_contours_handler,
    filtering_contours_handler,
    matching_workpieces_handler
)
from .state_handlers.execution_state_handlers import (
    processing_workpiece_handler,
    calculating_pickup_position_handler,
    calculating_placement_position_handler,
    executing_pick_and_place_handler,
    updating_debug_info_handler,
    checking_for_more_workpieces_handler
)


class PickAndPlaceStateMachine:
    """
    Main state machine controller for pick and place operations.
    
    Provides full control over the nesting process with pause/resume/stop capabilities
    similar to the glue dispensing process.
    """
    
    def __init__(self, broker: Optional[MessageBroker] = None):
        self.broker = broker or MessageBroker()
        self.state_machine: Optional[ExecutableStateMachine] = None
        self.context: Optional[PickAndPlaceContext] = None
        
        # Setup logging
        enable_logging = True
        self.logger = setup_logger("PickAndPlaceStateMachine") if enable_logging else None
        self.logger_context = LoggerContext(enabled=enable_logging, logger=self.logger)
    
    def setup_state_machine(self, context: PickAndPlaceContext) -> bool:
        """
        Setup the state machine with the given context.
        
        Args:
            context: Pick and place context with all required data
            
        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.context = context
            
            # Create state registry and register all states
            registry = self._create_state_registry()
            
            # Build the state machine
            self.state_machine = (
                ExecutableStateMachineBuilder()
                .with_initial_state(PickAndPlaceState.INITIALIZING)
                .with_transition_rules(PickAndPlaceTransitionRules.get_pick_and_place_transition_rules())
                .with_state_registry(registry)
                .with_message_broker(self.broker)
                .with_context(context)
                .with_state_topic("PICK_AND_PLACE_STATE")
                .build()
            )
            
            log_info_message(self.logger_context, "Pick and place state machine setup completed")
            return True
            
        except Exception as e:
            log_info_message(self.logger_context, f"Failed to setup state machine: {str(e)}")
            return False
    
    def _create_state_registry(self) -> StateRegistry:
        """Create and populate the state registry with all state handlers."""
        registry = StateRegistry()
        
        # Map states to their handlers
        state_handlers = {
            PickAndPlaceState.INITIALIZING: self._initializing_handler,
            PickAndPlaceState.IDLE: self._idle_handler,
            PickAndPlaceState.MOVING_TO_CAPTURE_POSITION: moving_to_capture_position_handler,
            PickAndPlaceState.SETTING_UP_VISION: setting_up_vision_handler,
            PickAndPlaceState.DETECTING_CONTOURS: detecting_contours_handler,
            PickAndPlaceState.FILTERING_CONTOURS: filtering_contours_handler,
            PickAndPlaceState.MATCHING_WORKPIECES: matching_workpieces_handler,
            PickAndPlaceState.PROCESSING_WORKPIECE: processing_workpiece_handler,
            PickAndPlaceState.CALCULATING_PICKUP_POSITION: calculating_pickup_position_handler,
            PickAndPlaceState.CALCULATING_PLACEMENT_POSITION: calculating_placement_position_handler,
            PickAndPlaceState.CHANGING_GRIPPER: self._changing_gripper_handler,
            PickAndPlaceState.VERIFYING_GRIPPER: self._verifying_gripper_handler,
            PickAndPlaceState.MEASURING_HEIGHT: self._measuring_height_handler,
            PickAndPlaceState.EXECUTING_PICK_AND_PLACE: executing_pick_and_place_handler,
            PickAndPlaceState.UPDATING_DEBUG_INFO: updating_debug_info_handler,
            PickAndPlaceState.CHECKING_FOR_MORE_WORKPIECES: checking_for_more_workpieces_handler,
            PickAndPlaceState.COMPLETED: self._completed_handler,
            PickAndPlaceState.ERROR: self._error_handler,
            PickAndPlaceState.STOPPED: self._stopped_handler,
            PickAndPlaceState.PAUSED: self._paused_handler,
            PickAndPlaceState.CLEANING_UP: self._cleaning_up_handler,
            PickAndPlaceState.DROPPING_GRIPPER: self._dropping_gripper_handler
        }
        
        # Register all states
        for state, handler in state_handlers.items():
            state_obj = State(
                state=state,
                handler=handler,
                on_enter=lambda ctx, s=state: self._on_state_enter(s, ctx),
                on_exit=lambda ctx, s=state: self._on_state_exit(s, ctx)
            )
            registry.register_state(state_obj)
        
        return registry
    
    def _on_state_enter(self, state: PickAndPlaceState, context: PickAndPlaceContext):
        """Called when entering any state."""
        log_info_message(self.logger_context, f"Entering state: {state.name}")
    
    def _on_state_exit(self, state: PickAndPlaceState, context: PickAndPlaceContext):
        """Called when exiting any state."""
        log_info_message(self.logger_context, f"Exiting state: {state.name}")
    
    # ==================== Control Methods ====================
    
    def start(self) -> bool:
        """Start the pick and place operation."""
        if not self.state_machine or not self.context:
            log_info_message(self.logger_context, "State machine not properly initialized")
            return False
        
        try:
            # Transition to idle state to begin operation
            self.state_machine.transition(PickAndPlaceState.IDLE)
            log_info_message(self.logger_context, "Pick and place operation started")
            return True
        except Exception as e:
            log_info_message(self.logger_context, f"Failed to start operation: {str(e)}")
            return False
    
    def pause(self) -> bool:
        """Pause the pick and place operation."""
        if not self.context:
            return False
        
        self.context.request_pause(self.get_current_state())
        log_info_message(self.logger_context, "Pause requested")
        return True
    
    def resume(self) -> bool:
        """Resume the pick and place operation from pause."""
        if not self.state_machine or not self.context:
            return False
        
        if self.get_current_state() == PickAndPlaceState.PAUSED:
            previous_state = self.context.resume_from_pause()
            if previous_state:
                self.state_machine.transition(previous_state)
                log_info_message(self.logger_context, f"Resumed from pause to state: {previous_state.name}")
                return True
        return False
    
    def stop(self) -> bool:
        """Stop the pick and place operation."""
        if not self.context:
            return False
        self.state_machine.transition(PickAndPlaceState.STOPPED)
        self.context.request_stop()
        log_info_message(self.logger_context, "Stop requested")
        return True
    
    def emergency_stop(self) -> bool:
        """Emergency stop - immediate halt of operations."""
        if not self.state_machine or not self.context:
            return False
        
        try:
            self.context.request_stop()
            self.state_machine.transition(PickAndPlaceState.ERROR)
            log_info_message(self.logger_context, "Emergency stop executed")
            return True
        except:
            return False
    
    def get_current_state(self) -> Optional[PickAndPlaceState]:
        """Get the current state of the state machine."""
        return self.state_machine.state if self.state_machine else None
    
    def get_operation_status(self) -> Dict:
        """Get the current operation status."""
        if not self.context:
            return {}
        
        status = self.context.get_operation_summary()
        status['current_state'] = self.get_current_state().name if self.get_current_state() else None
        return status
    
    def start_execution_loop(self, delay: float = 0.1):
        """Start the execution loop (blocking)."""
        if self.state_machine:
            self.state_machine.start_execution(delay)
    
    def stop_execution_loop(self):
        """Stop the execution loop."""
        if self.state_machine:
            self.state_machine.stop_execution()
    
    # ==================== State Handlers ====================
    
    def _initializing_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle initialization of the pick and place system."""
        try:
            log_info_message(self.logger_context, "Initializing pick and place system...")
            # Any initialization logic here
            return PickAndPlaceState.IDLE
        except Exception as e:
            context.record_error(f"Initialization failed: {str(e)}")
            return PickAndPlaceState.ERROR
    
    def _idle_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle idle state - ready to begin operation."""
        if context.stop_requested:
            return PickAndPlaceState.STOPPED
        
        # Begin operation
        return PickAndPlaceState.MOVING_TO_CAPTURE_POSITION
    
    def _changing_gripper_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle changing gripper if needed."""
        try:
            if context.pause_requested:
                context.request_pause(PickAndPlaceState.CHANGING_GRIPPER)
                return PickAndPlaceState.PAUSED
            
            if context.stop_requested:
                return PickAndPlaceState.STOPPED
            
            target_gripper_id = int(context.current_match.gripperID.value)
            
            if context.robot_service.current_tool == target_gripper_id:
                log_info_message(context.logger_context, f"Gripper {target_gripper_id} already attached")
                return PickAndPlaceState.MEASURING_HEIGHT
            
            result = context.robot_workflow.change_gripper_if_needed(target_gripper_id, context.laser)
            
            if not result.success:
                context.record_error(f"Failed to change gripper: {result.message}")
                return PickAndPlaceState.ERROR
            
            context.current_gripper_id = target_gripper_id
            return PickAndPlaceState.VERIFYING_GRIPPER
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            context.record_error(f"Error changing gripper: {str(e)}")
            return PickAndPlaceState.ERROR
    
    def _verifying_gripper_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle verifying gripper change."""
        # Gripper verification is handled in the robot workflow
        return PickAndPlaceState.MEASURING_HEIGHT
    
    def _measuring_height_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle height measurement."""
        try:
            if context.pause_requested:
                context.request_pause(PickAndPlaceState.MEASURING_HEIGHT)
                return PickAndPlaceState.PAUSED
            
            if context.stop_requested:
                return PickAndPlaceState.STOPPED
            
            # Height measurement is handled in the placement workflow
            return PickAndPlaceState.EXECUTING_PICK_AND_PLACE
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            context.record_error(f"Error measuring height: {str(e)}")
            return PickAndPlaceState.ERROR
    
    def _completed_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle completion of the operation."""
        log_info_message(self.logger_context, f"Pick and place operation completed. Total workpieces placed: {context.count}")

        # Drop off the current gripper if one is attached
        if context.robot_service.current_tool is not None:
            gripper_id = context.robot_service.current_tool
            log_info_message(self.logger_context, f"Dropping gripper {gripper_id} on completion")
            success, message = context.robot_service.dropOffGripper(gripper_id)
            if not success:
                log_info_message(self.logger_context, f"Error dropping gripper on completion: {message}")
            else:
                log_info_message(self.logger_context, f"Successfully dropped gripper {gripper_id}")
        else:
            log_info_message(self.logger_context, "No gripper to drop off on completion")

        # Turn off laser
        context.laser.turnOff()

        self.state_machine.stop_execution()
        return None  # Stay in completed state
    
    def _error_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle error state."""
        if context.last_error:
            log_info_message(self.logger_context, f"Error state: {context.last_error}")
        return None  # Stay in error state
    
    def _stopped_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle stopped state."""
        log_info_message(self.logger_context, "Operation stopped by user")
        self.stop()
        return PickAndPlaceState.CLEANING_UP
    
    def _paused_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle paused state."""
        # Stay paused until resume is called
        return None
    
    def _cleaning_up_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle cleanup operations."""
        return PickAndPlaceState.DROPPING_GRIPPER
    
    def _dropping_gripper_handler(self, context: PickAndPlaceContext) -> Optional[PickAndPlaceState]:
        """Handle dropping the gripper."""
        try:
            if context.robot_service.current_tool:
                context.robot_service.dropOffGripper(context.robot_service.current_tool)
            context.laser.turnOff()
            return PickAndPlaceState.COMPLETED
        except Exception as e:
            import traceback
            traceback.print_exc()
            context.record_error(f"Error dropping gripper: {str(e)}")
            return PickAndPlaceState.ERROR