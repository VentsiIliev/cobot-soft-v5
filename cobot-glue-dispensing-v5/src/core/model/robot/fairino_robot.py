import platform
import logging
from typing import List

import requests

from modules.utils.custom_logging import setup_logger, LoggerContext, log_info_message, log_error_message, \
    log_debug_message
from core.model.robot.IRobot import IRobot
from core.model.robot.enums.axis import Direction
from frontend.core.services.domain.RobotService import RobotAxis

if platform.system() == "Windows":
    pass

elif platform.system() == "Linux":
    logging.info("Linux detected")
    from libs.fairino.linux.fairino import Robot
else:
    raise Exception("Unsupported OS")

ENABLE_LOGGING = True  # Enable or disable logging
# Initialize logger if enabled
if ENABLE_LOGGING:
    robot_logger = setup_logger("RobotWrapper")
else:
    robot_logger = None


class TestRobotWrapper(IRobot):
    """
       A full mock of the Fairino Robot interface.
       Implements every method used by FairinoRobot and returns safe dummy values.
       """

    def __init__(self):
        print("⚙️  TestRobot initialized (mock robot).")

    # --- Motion commands ---
    def move_cartesian(self, position, tool=0, user=0, vel=100, acc=30, blendR=0):
        print(f"[MOCK] MoveCart -> pos={position}, tool={tool}, user={user}, vel={vel}, acc={acc}")
        return 0

    def move_liner(self, position, tool=0, user=0, vel=100, acc=30, blendR=0):
        print(f"[MOCK] MoveL -> pos={position}, tool={tool}, user={user}, vel={vel}, acc={acc}, blendR={blendR}")
        return 0

    def start_jog(self, axis: RobotAxis, direction: Direction, step, vel, acc):
        print(f"[MOCK] StartJOG -> axis={axis}, direction={direction}, step={step}, vel={vel}, acc={acc}")
        return 0

    def stop_motion(self):
        print("[MOCK] StopMotion called")
        return 0

    def ResetAllError(self):
        print("[MOCK] ResetAllError called")
        return 0

    # --- State queries ---
    def GetActualTCPPose(self):
        # print("[MOCK] GetActualTCPPose called")
        # Returning tuple to match expected structure (status, pose)
        return (0, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def get_current_position(self):
        # print("[MOCK] GetActualTCPPose called")
        # Returning tuple to match expected structure (status, pose)
        return (0, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def get_current_velocity(self):
        print("[MOCK] GetActualTCPCompositeSpeed called")
        return (0, [0.0])  # mimic real return: (status, [speed])

    def GetSDKVersion(self):
        print("[MOCK] GetSDKVersion called")
        return "TestRobot SDK v1.0"



class FairinoRobot(IRobot):
    """
      A wrapper for the real robot controller, abstracting motion and I/O operations.
      """

    def __init__(self, ip):
        """
               Initializes the robot wrapper and connects to the robot via RPC.

               Args:
                   ip (str): IP address of the robot controller.
               """
        self.ip = ip
        self.robot = Robot.RPC(self.ip)  # Real robot - use in production
        # self.robot = TestRobotWrapper()  # For testing purposes, replace with a real robot in production
        self.logger_context = LoggerContext(logger=robot_logger, enabled=ENABLE_LOGGING)
        if self.robot is not None:
            log_info_message(self.logger_context, f"RobotWrapper initialized for robot at {self.ip}")
        else:
            log_error_message(self.logger_context, f"Failed to connect to robot at {self.ip}")
            raise ConnectionError(f"Could not connect to robot at {self.ip}")

        """overSpeedStrategy: over speed handling strategy
        0 - strategy off;
        1 - standard;
        2 - stop on error when over speeding;
        3 - adaptive speed reduction, default 0"""
        self.overSpeedStrategy = 3

    def move_cartesian(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
              Moves the robot in Cartesian space.

              Args:
                  blendR
                  position (list): Target Cartesian position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.

              Returns:
                  list: Result from robot move command.
              """

        result = self.robot.MoveCart(position, tool, user, vel=vel, acc=acc)
        log_debug_message(self.logger_context,
                          f"MoveCart to {position} with tool {tool}, user {user}, vel {vel}, acc {acc} -> result: {result}")
        return result

    def move_liner(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
              Executes a linear movement with blending.

              Args:
                  position (list): Target position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.
                  blendR (float): Blend radius.

              Returns:
                  list: Result from robot linear move command.
              """

        result = self.robot.MoveL(position, tool, user, vel=vel, acc=acc, blendR=blendR)
        log_debug_message(self.logger_context,
                          f"MoveL to {position} with tool {tool}, user {user}, vel {vel}, acc {acc}, blendR {blendR} -> result: {result}")
        return result

    def get_current_position(self):
        """
              Retrieves the current TCP (tool center point) position.

              Returns:
                  list: Current robot TCP pose.
              """
        try:
            currentPose = self.robot.GetActualTCPPose()
        except Exception as e:
            log_error_message(self.logger_context, f"get_current_position failed: {e}")
            return None
        # print(f"GetCurrentPosition raw -> {currentPose}")
        # check if int
        if isinstance(currentPose, int):
            currentPose = None
        else:
            currentPose = currentPose[1]
        # log_debug_message(self.logger_context, f"GetCurrentPosition -> {currentPose}")
        return currentPose

    def get_current_velocity(self):
        pass

    def get_current_acceleration(self):
        pass

    def enable(self):
        """
               Enables the robot, allowing motion.
               """
        self.robot.RobotEnable(1)

    def disable(self):
        """
             Disables the robot, preventing motion.
             """
        self.robot.RobotEnable(0)

    def printSdkVersion(self):
        """
              Prints the current SDK version of the robot controller.
              """
        version = self.robot.GetSDKVersion()
        print(version)
        return version

    def setDigitalOutput(self, portId, value):
        """
              Sets a digital output pin on the robot.

              Args:
                  portId (int): Output port number.
                  value (int): Value to set (0 or 1).
              """
        result = self.robot.SetDO(portId, value)
        log_debug_message(self.logger_context, f"SetDigitalOutput port {portId} to {value} -> result: {result}")
        return result

    def start_jog(self, axis, direction, step, vel, acc):
        """
              Starts jogging the robot in a specified axis and direction.

              Args:
                  axis (Axis): Axis to jog.
                  direction (Direction): Jog direction (PLUS or MINUS).
                  step (float): Distance to move.
                  vel (float): Velocity of jog.
                  acc (float): Acceleration of jog.

              Returns:
                  object: Result of the StartJOG command.
              """
        axis = axis.value
        direction = direction.value

        result = self.robot.StartJOG(ref=4, nb=axis, dir=direction, vel=vel, acc=acc, max_dis=step)
        log_debug_message(self.logger_context,
                          f"StartJog axis {axis} direction {direction} step {step} vel {vel} acc {acc} -> result: {result}")
        return result

    def stop_motion(self):
        """
               Stops all current robot motion.

               Returns:
                   object: Result of StopMotion command.
               """
        return self.robot.StopMotion()

    def resetAllErrors(self):
        """
               Resets all current error states on the robot.

               Returns:
                   object: Result of ResetAllError command.
               """
        print(f"RobotWrapper: ResetAllError called")
        return self.robot.ResetAllError()
