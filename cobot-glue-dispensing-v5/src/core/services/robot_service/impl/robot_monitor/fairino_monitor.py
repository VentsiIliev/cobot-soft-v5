from modules.utils import robot_utils
from core.model.robot import fairino_robot
from core.services.robot_service.impl.robot_monitor.base_robot_monitor import BaseRobotMonitor


class FairinoRobotMonitor(BaseRobotMonitor):
    """
    Continuously fetches robot position, computes velocity and acceleration,
    and reports results via a callback to the manager.
    """
    def __init__(self, robot_ip, cycle_time=0.03):
        super().__init__(cycle_time=cycle_time)
        self.robot = fairino_robot.FairinoRobot(robot_ip)

    def get_current_position(self):
        return self.robot.get_current_position()

    def get_current_velocity(self):
        return robot_utils.calculate_velocity(self.current_pos, self.prev_pos, self.dt)

    def get_current_acceleration(self):
        return robot_utils.calculate_acceleration(self.current_velocity, self.prev_velocity, self.dt, use_dt=False)

