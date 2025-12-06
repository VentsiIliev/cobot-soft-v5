from typing import Optional
from modules.utils.custom_logging import log_info_message, log_error_message
from ..models import GrippersConfig
from modules.shared.tools.enums.Gripper import Gripper
import time


class NestingResult:
    """Result object for nesting operations."""
    def __init__(self, success: bool, message: str):
        self.success = success
        self.message = message


class RobotWorkflow:
    """Workflow for robot operations in the nesting process."""
    
    def __init__(self, robot_service, logger_context):
        self.robot_service = robot_service
        self.logger_context = logger_context
    
    def move_to_capture_position(self, application, laser, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        """
        Move robot to nesting capture position with retry logic.

        Args:
            application: Application instance with movement methods
            laser: Laser tool for safety shutdown
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay in seconds between retries (default: 1.0)

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            ret = application.move_to_nesting_capture_position()

            if ret == 0:
                log_info_message(self.logger_context, "Moved to capture position successfully")
                return True

            # Log the failure
            if attempt < max_retries - 1:
                log_info_message(
                    self.logger_context,
                    f"Failed to move to capture position (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
            else:
                log_error_message(
                    self.logger_context,
                    f"Failed to move to capture position after {max_retries} attempts, result code: {ret}"
                )

        # All retries exhausted
        laser.turnOff()
        return False

    def pickup_gripper(self, target_gripper_id: int, laser) -> NestingResult:
        """
        Pick up the specified gripper.
        
        Args:
            target_gripper_id: ID of gripper to pick up
            laser: Laser tool for safety shutdown
            
        Returns:
            NestingResult with operation status
        """
        success, message = self.robot_service.pickupGripper(target_gripper_id)
        if not success:
            log_info_message(
                self.logger_context, 
                f"Failed to pick up gripper {target_gripper_id}: {message}"
            )
            laser.turnOff()
            return NestingResult(
                success=False, 
                message=f"Failed to pick up gripper {target_gripper_id}: {message}"
            )

        log_info_message(self.logger_context, f"Successfully picked up gripper {target_gripper_id}")
        return NestingResult(success=True, message="Gripper picked up successfully")
    
    def change_gripper_if_needed(self, target_gripper_id: int, laser) -> NestingResult:
        """
        Change to the specified gripper if different from current.
        
        Args:
            target_gripper_id: ID of desired gripper
            laser: Laser tool for safety shutdown
            
        Returns:
            NestingResult with operation status
        """
        # Check if gripper change is needed
        if self.robot_service.current_tool == target_gripper_id:
            log_info_message(
                self.logger_context, 
                f"Gripper {target_gripper_id} already attached, no change needed"
            )
            return NestingResult(success=True, message="No gripper change needed")
        
        # Drop current gripper if any
        if self.robot_service.current_tool is not None:
            log_info_message(
                self.logger_context, 
                f"Dropping off current gripper: {self.robot_service.current_tool}"
            )
            success, message = self.robot_service.dropOffGripper(self.robot_service.current_tool)
            if not success:
                log_info_message(
                    self.logger_context, 
                    f"Failed to drop off gripper {self.robot_service.current_tool}: {message}"
                )
                laser.turnOff()
                return NestingResult(
                    success=False, 
                    message=f"Failed to drop off gripper {self.robot_service.current_tool}: {message}"
                )

        # Pick up new gripper
        result = self.pickup_gripper(target_gripper_id, laser)
        if not result.success:
            return result

        # Verify gripper change
        verification_result = self.robot_service.tool_manager.verify_gripper_change(target_gripper_id)
        if verification_result is False:
            laser.turnOff()
            return NestingResult(
                success=False,
                message=f"Gripper change verification failed. Expected: {target_gripper_id}, Current: {self.robot_service.current_tool}"
            )

        log_info_message(self.logger_context, f"Successfully switched to gripper: {target_gripper_id}")
        return NestingResult(success=True, message="Gripper changed successfully")
    
    def finish_nesting(self, laser, workpiece_found: bool,
                      message_success: str, message_failure: str,
                      move_before_finish: bool = False, 
                      application=None) -> NestingResult:
        """
        Handle ending the nesting operation.
        
        Args:
            laser: Laser tool to turn off
            workpiece_found: True if any workpieces were processed
            message_success: Success message
            message_failure: Failure message  
            move_before_finish: Whether to move to capture position before finishing
            application: Application instance for movement
            
        Returns:
            NestingResult with appropriate status and message
        """
        if workpiece_found:
            log_info_message(self.logger_context, "No more workpieces detected, completing nesting.")
            
            # Drop current gripper
            if self.robot_service.current_tool is not None:
                self.robot_service.dropOffGripper(self.robot_service.current_tool)
            
            # Move to finish position if requested
            if move_before_finish and application is not None:
                ret = application.move_to_nesting_capture_position()
                if ret != 0:
                    laser.turnOff()
                    return NestingResult(success=False, message="Failed to move to start position")
            
            laser.turnOff()
            return NestingResult(success=True, message=message_success)
        else:
            laser.turnOff()
            return NestingResult(success=False, message=message_failure)