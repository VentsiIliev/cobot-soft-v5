"""
Robot Domain Service

Handles all robot-related operations with explicit return values.
No callbacks - just clean, clear method calls!
"""

import logging
from typing import TYPE_CHECKING
from enum import Enum

from communication_layer.api.v1 import Constants
from communication_layer.api.v1.endpoints import robot_endpoints
from communication_layer.api.v1.endpoints.robot_endpoints import ROBOT_SLOT_0_PICKUP
from ..types.ServiceResult import ServiceResult

# Import endpoint constants

if TYPE_CHECKING:
    from frontend.core.ui_controller.Controller import Controller


class RobotAxis(Enum):
    """Valid robot axes for movement operations"""
    X = "x"
    Y = "y" 
    Z = "z"
    RX = "rx"
    RY = "ry"
    RZ = "rz"


class RobotDirection(Enum):
    """Valid movement directions"""
    POSITIVE = "+"
    NEGATIVE = "-"


class RobotService:
    """
    Domain service for all robot operations.
    
    Provides explicit, type-safe methods for robot control.
    All methods return ServiceResult - no callbacks needed!
    
    Usage:
        result = robot_service.move_to_home()
        if result:
            print("Robot homed successfully!")
        else:
            print(f"Failed to home: {result.message}")
    """
    
    def __init__(self, controller: 'Controller', logger: logging.Logger):
        """
        Initialize the robot service.
        
        Args:
            controller: The main controller instance
            logger: Logger for this service
        """
        self.controller = controller
        self.logger = logger.getChild(self.__class__.__name__)
    
    def move_to_home(self) -> ServiceResult:
        """
        Move robot to home position.
        
        Args:

        
        Returns:
            ServiceResult with success/failure status
        """
        try:
            print("Moving robot to home position")
            
            status = self.controller.homeRobot()
            if status == Constants.RESPONSE_STATUS_SUCCESS:
                return ServiceResult.success_result("Robot moved to home position successfully")
            else:
                return ServiceResult.error_result("Failed to move robot to home position")
                
        except Exception as e:
            error_msg = f"Failed to move robot home: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def jog_robot(self, axis: str, direction: str, step: float) -> ServiceResult:
        """
        Jog robot in specified axis and direction.
        
        Args:
            axis: Robot axis (x, y, z, rx, ry, rz)
            direction: Movement direction (+ or -)
            step: Step size for movement
        
        Returns:
            ServiceResult with success/failure status
        """
        print(f"Attempting to jog robot: axis={axis}, direction={direction}, step={step}")
        try:
            # Validate inputs

            if axis.lower() not in [a.value for a in RobotAxis]:
                return ServiceResult.error_result(f"Invalid axis: {axis}. Valid axes: {[a.value for a in RobotAxis]}")

            if direction == "Plus":
                direction = "+"
            elif direction == "Minus":
                direction = "-"

            if direction not in [d.value for d in RobotDirection]:
                return ServiceResult.error_result(f"Invalid direction: {direction}. Valid directions: {[d.value for d in RobotDirection]}")
            
            if not isinstance(step, (int, float)) or step <= 0:
                return ServiceResult.error_result("Step size must be a positive number")
            
            self.logger.info(f"Jogging robot: {axis} {direction} {step}")
            
            self.controller.handleJog(axis, direction, step)
            
            return ServiceResult.success_result(f"Robot jogged {axis} {direction} {step}")
                
        except Exception as e:
            error_msg = f"Failed to jog robot: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def move_to_calibration_position(self) -> ServiceResult:
        """Move robot to calibration position."""
        try:
            self.logger.info("Moving robot to calibration position")
            
            self.controller.handleMoveToCalibrationPos()
            
            return ServiceResult.success_result("Robot moved to calibration position")
                
        except Exception as e:
            error_msg = f"Failed to move to calibration position: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def move_to_login_position(self) -> ServiceResult:
        """Move robot to login position."""
        try:
            self.logger.info("Moving robot to login position")
            
            status = self.controller.handleLoginPos()
            if status == Constants.RESPONSE_STATUS_SUCCESS:
                return ServiceResult.success_result("Robot moved to login position successfully")
            else:
                return ServiceResult.error_result("Failed to move robot to login position")
                
        except Exception as e:
            error_msg = f"Failed to move to login position: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def calibrate_robot(self) -> ServiceResult:
        """
        Calibrate robot system.
        
        Returns:
            ServiceResult with success/failure status and message
        """
        try:
            self.logger.info("Starting robot calibration")
            
            success, message = self.controller.handleCalibrateRobot()
            
            if success:
                return ServiceResult.success_result(f"Robot calibration successful: {message}")
            else:
                return ServiceResult.error_result(f"Robot calibration failed: {message}")
                
        except Exception as e:
            error_msg = f"Robot calibration failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def save_calibration_point(self) -> ServiceResult:
        """Save current position as calibration point."""
        try:
            self.logger.info("Saving robot calibration point")
            
            result = self.controller.handle(robot_endpoints.ROBOT_SAVE_POINT)
            
            return ServiceResult.success_result("Calibration point saved successfully")
                
        except Exception as e:
            error_msg = f"Failed to save calibration point: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def reset_errors(self) -> ServiceResult:
        """Reset robot errors."""
        try:
            self.logger.info("Resetting robot errors")
            
            status = self.controller.handleResetErrors()
            
            return ServiceResult.success_result("Robot errors reset successfully")
                
        except Exception as e:
            error_msg = f"Failed to reset robot errors: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def clean_nozzle(self) -> ServiceResult:
        """Execute nozzle cleaning procedure."""
        try:
            self.logger.info("Starting nozzle cleaning procedure")
            
            status = self.controller.handleCleanNozzle()
            
            return ServiceResult.success_result("Nozzle cleaning completed successfully")
                
        except Exception as e:
            error_msg = f"Failed to clean nozzle: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def update_config(self) -> ServiceResult:
        """Update robot configuration."""
        try:
            self.logger.info("Updating robot configuration")
            
            status = self.controller.handleRobotUpdateConfig()
            
            if str(status) == "SUCCESS":
                return ServiceResult.success_result("Robot configuration updated successfully")
            else:
                return ServiceResult.error_result("Failed to update robot configuration")
                
        except Exception as e:
            error_msg = f"Failed to update robot config: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)

    def get_current_position(self) -> ServiceResult:
        """Get current robot position."""
        try:
            self.logger.info("Retrieving current robot position")

            position = self.controller.handle_get_robot_current_position()

            if position is not None:
                return ServiceResult.success_result("Current position retrieved successfully", data=position)
            else:
                return ServiceResult.error_result("Failed to retrieve current position")

        except Exception as e:
            error_msg = f"Failed to get current position: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)

    def move_to_position(self, position: list[float],vel,acc) -> ServiceResult:
        """Move robot to specified position."""
        try:
            self.logger.info(f"Moving robot to position: {position} with vel={vel}, acc={acc}")

            status = self.controller.handle_move_robot_to_position(position,vel,acc)

            if str(status) == "SUCCESS":
                return ServiceResult.success_result("Robot moved to position successfully")
            else:
                return ServiceResult.error_result("Failed to move robot to position")

        except Exception as e:
            error_msg = f"Failed to move to position: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)

    def pickup_gripper(self,slot_id:int)-> ServiceResult:
        print(f"[Frontend/RobotService.py] Sending pickup command for slot {slot_id}")
        # return ServiceResult.success_result(f"Pickup command sent for slot {slot_id}")
        if slot_id == 0:
            self.controller.handle(ROBOT_SLOT_0_PICKUP)
        elif slot_id == 1:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_1_PICKUP)
        elif slot_id == 2:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_2_PICKUP)
        elif slot_id == 3:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_3_PICKUP)
        elif slot_id == 4:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_4_PICKUP)
        else:
            raise ValueError(f"Invalid slot ID: {slot_id}")

        return ServiceResult.success_result(f"Pickup command sent for slot {slot_id}")

    def drop_gripper(self,slot_id:int)-> ServiceResult:
        print(f"[Frontend/RobotService.py] Sending drop command for slot {slot_id}")
        # return ServiceResult.success_result(f"Drop command sent for slot {slot_id}")
        if slot_id == 0:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_0_DROP)
        elif slot_id == 1:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_1_DROP)
        elif slot_id == 2:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_2_DROP)
        elif slot_id == 3:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_3_DROP)
        elif slot_id == 4:
            self.controller.handle(robot_endpoints.ROBOT_SLOT_4_DROP)
        else:
            raise ValueError(f"Invalid slot ID: {slot_id}")

        return ServiceResult.success_result(f"Drop command sent for slot {slot_id}")