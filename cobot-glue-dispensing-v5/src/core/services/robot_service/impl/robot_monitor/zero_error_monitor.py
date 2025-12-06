"""
Zero Error Robot Monitor

This module provides monitoring capabilities for Zero Error robots,
following the same interface as the Fairino robot monitor.
"""


from core.model.robot.ZeroErrRobot import ZeroErrRobot
from core.services.robot_service.impl.robot_monitor.base_robot_monitor import BaseRobotMonitor
from modules.utils import robot_utils


class ZeroErrorRobotMonitor(BaseRobotMonitor):
    """
    Continuously fetches Zero Error robot position, computes velocity and acceleration,
    and reports results via a callback to the manager.
    """
    
    def __init__(self, robot_ip, cycle_time=0.03,robot: ZeroErrRobot=None):
        """
        Initialize Zero Error robot monitor.
        
        Args:
            robot_ip: IP address of the Zero Error robot controller
            cycle_time: Monitoring cycle time in seconds
        """
        super().__init__(cycle_time=cycle_time)
        if robot is None:
            raise ValueError("A ZeroErrRobot instance must be provided")
        self.robot = robot

    def get_current_position(self):
        """Get current robot position from Zero Error robot"""
        return self.robot.get_current_position()

    def get_current_velocity(self):
        """Calculate current velocity based on position changes"""
        return robot_utils.calculate_velocity(self.current_pos, self.prev_pos, self.dt)

    def get_current_acceleration(self):
        """Calculate current acceleration based on velocity changes"""
        return robot_utils.calculate_acceleration(self.current_velocity, self.prev_velocity, self.dt, use_dt=False)