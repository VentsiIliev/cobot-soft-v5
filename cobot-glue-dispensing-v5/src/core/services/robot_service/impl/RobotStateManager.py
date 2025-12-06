from modules.shared.MessageBroker import MessageBroker
from core.services.robot_service.impl.robot_monitor.base_robot_monitor import BaseRobotMonitor
from core.services.robot_service.enums.RobotState import RobotState
from communication_layer.api.v1.topics import RobotTopics

class RobotStateManager:
    """
    Manages the robot state and communication based on motion data
    received from RobotMonitor.
    """
    def __init__(self, robot_monitor:BaseRobotMonitor, velocity_threshold=1, acceleration_threshold=0.001):
        self.broker = MessageBroker()
        self.velocity_threshold = velocity_threshold
        self.acceleration_threshold = acceleration_threshold
        self.trajectory_update = False

        # Motion variables
        self.position = None
        self.velocity = 0.0
        self.acceleration = 0.0
        self.robotState = RobotState.STATIONARY
        self.robotStateTopic = RobotTopics.ROBOT_STATE
        self.monitor = robot_monitor
        self.monitor.set_data_callback(self.on_motion_data)

    # ----------------------------
    # Callbacks and State Logic
    # ----------------------------

    def on_motion_data(self, pos, velocity, acceleration, timestamp, error=False):
        """Handle new motion data from RobotMonitor."""
        if error:
            self.robotState = RobotState.ERROR
            self.publish_state()
            return

        self.position = pos
        self.velocity = velocity
        self.acceleration = acceleration
        self.update_state()
        self.publish_state()

        if self.robotState != RobotState.STATIONARY and self.trajectory_update:
            self.send_trajectory_point(pos)

    def update_state(self):
        """Determine robot state based on velocity and acceleration."""
        if abs(self.velocity) < self.velocity_threshold:
            self.robotState = RobotState.STATIONARY
        elif self.acceleration > self.acceleration_threshold:
            self.robotState = RobotState.ACCELERATING
        elif self.acceleration < -self.acceleration_threshold:
            self.robotState = RobotState.DECELERATING
        else:
            self.robotState = RobotState.MOVING

    def publish_state(self):
        """Publish current robot state and motion data."""
        self.broker.publish(
            self.robotStateTopic,
            {"state": self.robotState,"position": self.position, "speed": self.velocity, "accel": self.acceleration}
        )

    def send_trajectory_point(self, current_pos):
        x, y = current_pos[:2]
        transformed = self.broker.request("vision/transformToCamera", {"x": x, "y": y})
        t_x, t_y = transformed[0], transformed[1]

        self.broker.publish(RobotTopics.TRAJECTORY_POINT, {
            "x": int(t_x * 0.625),
            "y": int(t_y * 0.625)
        })

    # ----------------------------
    # Control Methods
    # ----------------------------

    def start_monitoring(self):
        self.monitor.start(self.on_motion_data)

    def stop_monitoring(self):
        self.monitor.stop()

    def get_current_state(self):
        """Expose current state for external queries."""
        return {
            "position": self.position,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "state": self.robotState
        }

