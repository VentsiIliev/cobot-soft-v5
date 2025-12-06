"""
Robot Factory

This module provides a factory for creating robot instances based on robot type.
The factory abstracts the creation logic and allows easy extension for new robot types.
"""

from typing import Optional
import logging

from .robot_types import RobotType
from .IRobot import IRobot
from .fairino_robot import FairinoRobot
from .ZeroErrRobot import ZeroErrRobot

logger = logging.getLogger(__name__)


class RobotCreationError(Exception):
    """Raised when robot creation fails"""
    pass


class RobotFactory:
    """
    Factory for creating robot instances based on type.
    
    This factory provides a centralized way to create different robot implementations
    while maintaining a consistent interface.
    """
    
    @staticmethod
    def create_robot(robot_type: RobotType, ip: str, **kwargs) -> IRobot:
        """
        Create a robot instance based on the specified type.
        
        Args:
            robot_type: Type of robot to create
            ip: IP address of the robot controller
            **kwargs: Additional arguments for robot initialization
            
        Returns:
            IRobot: Instance of the requested robot type
            
        Raises:
            RobotCreationError: If robot creation fails
        """
        try:
            logger.info(f"Creating robot of type: {robot_type.value} with IP: {ip}")
            
            if robot_type == RobotType.FAIRINO:
                return FairinoRobot(ip, **kwargs)
            
            elif robot_type == RobotType.ZERO_ERROR:
                return ZeroErrRobot(ip, **kwargs)
            
            elif robot_type == RobotType.TEST:
                # Import here to avoid circular dependencies
                from . import TestRobotWrapper
                return TestRobotWrapper(**kwargs)
            
            else:
                raise RobotCreationError(
                    f"Unsupported robot type: {robot_type.value}. "
                    f"Available types: {[t.value for t in RobotType]}"
                )
                
        except Exception as e:
            logger.error(f"Failed to create robot {robot_type.value}: {e}")
            raise RobotCreationError(f"Failed to create {robot_type.value} robot: {e}") from e
    
    @staticmethod
    def get_supported_types() -> list[RobotType]:
        """
        Get list of supported robot types.
        
        Returns:
            List of supported RobotType enum values
        """
        return list(RobotType)
    
    @staticmethod
    def is_supported(robot_type: RobotType) -> bool:
        """
        Check if a robot type is supported by this factory.
        
        Args:
            robot_type: Robot type to check
            
        Returns:
            True if supported, False otherwise
        """
        return robot_type in RobotType


# Convenience function for direct use
def create_robot(robot_type: RobotType, ip: str, **kwargs) -> IRobot:
    """
    Convenience function to create a robot instance.
    
    Args:
        robot_type: Type of robot to create
        ip: IP address of the robot controller
        **kwargs: Additional arguments for robot initialization
        
    Returns:
        IRobot: Instance of the requested robot type
    """
    return RobotFactory.create_robot(robot_type, ip, **kwargs)