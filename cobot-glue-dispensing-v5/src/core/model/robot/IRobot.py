from abc import abstractmethod, ABC
from enum import IntEnum

from core.model.robot.enums.axis import RobotAxis, Direction

class FeedbackCode(IntEnum):
    SUCCESS = 0                 # Command completed
    FAIL = 1                    # Generic failure
    INVALID_ARGUMENT = 2        # Bad or missing parameters
    ROBOT_NOT_READY = 3         # Disabled, estop, or not initialized
    MOTION_ERROR = 4            # Motion could not be completed

class IRobot(ABC):

    @abstractmethod
    def move_cartesian(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
              Moves the robot in a linear Cartesian path to the specified position.

              Args:
                  position (list): Target TCP pose [X, Y, Z, A, B, C].
                  tool (int): Tool number to use.
                  user (int): User frame number to use.
                  vel (float): Velocity percentage (0-100).
                  acc (float): Acceleration percentage (0-100).
                  blendR (float): Blending radius for smooth transitions.
                Returns:
                    list: Result from robot move command.
                """


    def move_liner(self,position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
              Executes a linear movement to the specified position.

              Args:
                  position (list): Target TCP pose [X, Y, Z, A, B, C].
                  tool (int): Tool number to use.
                  user (int): User frame number to use.
                  vel (float): Velocity percentage (0-100).
                  acc (float): Acceleration percentage (0-100).
                  blendR (float): Blending radius for smooth transitions.

              Returns:
                  list: Result from robot linear move command.
              """

    def get_current_position(self):
        """
              Retrieves the current TCP (tool center point) position.

              Returns:
                  list: Current robot TCP pose [X, Y, Z, A, B, C].
              """

    def get_current_velocity(self):
        """
              Retrieves the current velocity of the robot.

              Returns:
                  float: Current robot velocity.
              """

    def get_current_acceleration(self):
        """
              Retrieves the current acceleration of the robot.

              Returns:
                  float: Current robot acceleration.
              """

    def stop_motion(self):
        """
              Stops the robot's motion immediately.

              Returns:
                  bool: True if the stop command was successful, False otherwise.
              """

    def enable(self):
        """
               Enables the robot, allowing motion.
               """

    def disable(self):
        """
             Disables the robot, preventing motion.
             """

    def start_jog(self,axis:RobotAxis,direction:Direction,step,vel,acc):
        """
                  Starts jogging the robot along a specified axis.

                  Args:
                      axis (str): Axis to jog ('X', 'Y', 'Z', 'A', 'B', 'C').
                      direction (int): Direction of jog (1 for positive, -1 for negative).
                      step (float): Step size for each jog increment.
                      vell (float): Velocity percentage (0-100).
                      acc (float): Acceleration percentage (0-100).

                  Returns:
                      bool: True if the jog command was successful, False otherwise.
                  """