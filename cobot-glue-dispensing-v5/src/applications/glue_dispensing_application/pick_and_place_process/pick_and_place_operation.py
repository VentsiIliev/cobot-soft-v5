"""
State Machine-based Nesting Handler

This module provides a nesting handler that uses the state machine implementation
for full pause/resume/stop control, similar to the glue dispensing process.
"""

from typing import List, Optional, Dict, Any
from threading import Thread
import time

from core.operation_state_management import IOperation, OperationResult
from modules.utils.custom_logging import setup_logger, LoggerContext, log_info_message
from modules.VisionSystem.heightMeasuring.LaserTracker import LaserTrackService

from .models import GrippersConfig
from .services import PickupService, PlacementService, PlaneManagementService, GripperService
from .workflows import VisionWorkflow, RobotWorkflow, MeasurementWorkflow, PlacementWorkflow, NestingResult

from .Plane import Plane
from .state_machine import PickAndPlaceStateMachine, PickAndPlaceContext, PickAndPlaceState
from .workflows.measurement_workflow import HeightMeasureContext


class PickAndPlaceOperation(IOperation):
    """
    Nesting handler with state machine-based pause/resume/stop control.
    
    Provides the same interface as the original nesting handler but with
    full state machine control capabilities.
    """
    
    def __init__(self):
        super().__init__()
        self.state_machine: Optional[PickAndPlaceStateMachine] = None
        self.context: Optional[PickAndPlaceContext] = None
        self.execution_thread: Optional[Thread] = None
        self.is_running = False
        
        # Setup logging
        enable_logging = True
        self.logger = setup_logger("StateMachineNesting") if enable_logging else None
        self.logger_context = LoggerContext(enabled=enable_logging, logger=self.logger)
    
    def _do_start(self, application, workpieces: List) -> OperationResult:
        """
        Start nesting operation using state machine.
        
        Args:
            application: Application instance with movement methods and services
            workpieces: List of workpiece templates to match against
            
        Returns:
            OperationResult with actual completion status (success/stopped/error)
        """
        try:
            # Initialize the state machine and context
            success = self._initialize_state_machine(application, workpieces)
            if not success:
                return OperationResult(success=False, message="Failed to initialize state machine")
            
            # Start the state machine
            success = self.state_machine.start()
            if not success:
                return OperationResult(success=False, message="Failed to start state machine")
            
            # Start execution in a separate thread
            self.is_running = True
            self.execution_thread = Thread(target=self._run_execution_loop, daemon=True)
            self.execution_thread.start()

            # Wait for completion and return the actual result
            result = self.wait_for_completion()
            log_info_message(self.logger_context, f"Nesting completed with result: {result.message}")

            # Return the actual result (success=True only if completed, False if stopped/error)
            return result

        except Exception as e:
            log_info_message(self.logger_context, f"Failed to start nesting: {str(e)}")
            return OperationResult(success=False, error=f"Failed to start nesting: {str(e)}")
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> OperationResult:
        """
        Wait for the nesting operation to complete.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            NestingResult with final operation status
        """
        if self.execution_thread:
            self.execution_thread.join(timeout)

        # Poll until we reach a terminal state
        max_wait_iterations = 100  # Max 10 seconds at 0.1s per iteration
        iterations = 0

        while iterations < max_wait_iterations:
            if self.state_machine and self.context:
                current_state = self.state_machine.get_current_state()

                # Check if we're in a terminal state
                if current_state == PickAndPlaceState.COMPLETED:
                    status = self.state_machine.get_operation_status()
                    return OperationResult(
                        success=True,
                        message=f"Nesting completed successfully. Placed {status.get('workpieces_placed', 0)} workpieces."
                    )
                elif current_state == PickAndPlaceState.ERROR:
                    status = self.state_machine.get_operation_status()
                    return OperationResult(
                        success=False,
                        message=f"Nesting failed: {status.get('last_error', 'Unknown error')}"
                    )
                elif current_state == PickAndPlaceState.STOPPED:
                    status = self.state_machine.get_operation_status()
                    return OperationResult(
                        success=False,
                        message=f"Nesting stopped by user. Placed {status.get('workpieces_placed', 0)} workpieces."
                    )

            # Not in terminal state yet, wait a bit
            time.sleep(0.1)
            iterations += 1

        # Timeout or unknown state
        return OperationResult(success=False, message=f"Operation timeout or unknown state current state: {self.state_machine.get_current_state()}")

    def _initialize_state_machine(self, application, workpieces: List) -> bool:
        """Initialize the state machine with all required services and context."""
        try:
            # Extract services from application
            vision_service = application.visionService
            robot_service = application.robotService
            
            # Create configuration
            grippers_config = GrippersConfig(
                gripper_x_offset=100.429,
                gripper_y_offset=1.991,
                double_gripper_z_offset=14,
                single_gripper_z_offset=19
            )
            
            # Initialize plane and tools
            plane = Plane()
            laser = robot_service.tool_manager.get_tool("laser")
            laser_tracking_service = LaserTrackService()
            
            # Setup services
            pickup_service = PickupService(grippers_config, 150.0)  # DESCENT_HEIGHT_OFFSET
            plane_service = PlaneManagementService(plane)
            placement_service = PlacementService(plane_service)
            gripper_service = GripperService(grippers_config)
            
            # Setup workflows
            vision_workflow = VisionWorkflow(vision_service, self.logger_context)
            robot_workflow = RobotWorkflow(robot_service, self.logger_context)
            
            height_measure_context = HeightMeasureContext(
                robot_service=robot_service,
                vision_service=vision_service,
                laser_tracking_service=laser_tracking_service,
                laser=laser
            )
            measurement_workflow = MeasurementWorkflow(height_measure_context, self.logger_context)
            
            placement_workflow = PlacementWorkflow(
                pickup_service, placement_service, gripper_service,
                measurement_workflow, grippers_config, self.logger_context
            )
            
            # Create context with all services
            self.context = PickAndPlaceContext(
                application=application,
                vision_service=vision_service,
                robot_service=robot_service,
                preselected_workpieces=workpieces,
                pickup_service=pickup_service,
                placement_service=placement_service,
                gripper_service=gripper_service,
                plane_service=plane_service,
                vision_workflow=vision_workflow,
                robot_workflow=robot_workflow,
                measurement_workflow=measurement_workflow,
                placement_workflow=placement_workflow,
                grippers_config=grippers_config,
                plane=plane,
                laser=laser,
                logger_context=self.logger_context
            )
            
            # Create and setup state machine
            self.state_machine = PickAndPlaceStateMachine()
            success = self.state_machine.setup_state_machine(self.context)
            
            return success
            
        except Exception as e:
            log_info_message(self.logger_context, f"Failed to initialize state machine: {str(e)}")
            return False
    
    def _run_execution_loop(self):
        """Run the state machine execution loop."""
        try:
            if self.state_machine:
                self.state_machine.start_execution_loop(delay=0.1)
        except Exception as e:
            log_info_message(self.logger_context, f"Execution loop error: {str(e)}")
        finally:
            self.is_running = False
    
    # ==================== Control Methods ====================
    
    def _do_pause(self) -> bool:
        """Pause the nesting operation."""
        if self.state_machine:

            if self.get_current_state() == PickAndPlaceState.PAUSED: # it is already paused so resume
                log_info_message(logger_context=self.logger_context,message=f"The operation is already paused, resuming now.")
                result = self.resume()
                return result.success
            else:
                return self.state_machine.pause()
        return False
    
    def _do_resume(self) -> bool:
        """Resume the nesting operation."""
        if self.state_machine:
            return self.state_machine.resume()
        return False
    
    def _do_stop(self) -> bool:
        """Stop the nesting operation gracefully."""
        if self.state_machine:
            success = self.state_machine.stop()
            self._cleanup()
            return success
        return False
    
    def get_current_state(self) -> Optional[PickAndPlaceState]:
        """Get the current state of the operation."""
        if self.state_machine:
            return self.state_machine.get_current_state()
        return None
    
    def get_operation_status(self) -> Dict:
        """Get detailed operation status."""
        if self.state_machine:
            return self.state_machine.get_operation_status()
        return {}
    
    def is_paused(self) -> bool:
        """Check if the operation is currently paused."""
        return self.get_current_state() == PickAndPlaceState.PAUSED
    
    def is_completed(self) -> bool:
        """Check if the operation is completed."""
        current_state = self.get_current_state()
        return current_state in [PickAndPlaceState.COMPLETED, PickAndPlaceState.ERROR, PickAndPlaceState.STOPPED]
    
    def _cleanup(self):
        """Clean up resources."""
        try:
            if self.state_machine:
                self.state_machine.stop_execution_loop()
            
            if self.execution_thread and self.execution_thread.is_alive():
                self.execution_thread.join(timeout=5.0)
            
            self.is_running = False
            
        except Exception as e:
            log_info_message(self.logger_context, f"Cleanup error: {str(e)}")
