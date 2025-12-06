from communication_layer.api.v1.topics import RobotTopics
from core.model.robot.IRobot import IRobot
from core.model.robot.enums.axis import Direction
from frontend.core.services.domain.RobotService import RobotAxis
# ROS2 imports for MoveIt integration

# ROS2 imports for MoveIt integration (import on demand with safe fallbacks)
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from geometry_msgs.msg import Pose, PoseStamped, PoseArray
    from std_msgs.msg import Float64MultiArray, Float32MultiArray, Bool, Int32MultiArray
    from sensor_msgs.msg import JointState
    try:
        from moveit_msgs.action import MoveGroup
        from moveit_msgs.msg import MotionSequenceRequest
        from moveit_msgs.srv import GetPositionFK
    except Exception:
        MoveGroup = object
        MotionSequenceRequest = object
        GetPositionFK = object
except Exception:
    # Import stubs when ROS2 is not available
    from core.model.robot.rclpy_stubs import (
        rclpy,
        Node,
        ActionClient,
        Pose,
        PoseStamped,
        PoseArray,
        Float64MultiArray,
        Float32MultiArray,
        Bool,
        Int32MultiArray,
        JointState,
        MoveGroup,
        MotionSequenceRequest,
        GetPositionFK
    )
    print(f"[ZeroErrRobot] Warning: ROS2 imports failed, using stubs.")


from enum import Enum
import logging
import platform
import time

from modules.utils.custom_logging import LoggerContext, log_info_message, log_error_message, log_debug_message, \
    setup_logger

ENABLE_LOGGING = True  # Enable or disable logging
# Initialize logger if enabled
if ENABLE_LOGGING:
    robot_logger = setup_logger("RobotWrapper")
else:
    robot_logger = None



class ZeroErrRobot(Node, IRobot):
    """
      A wrapper for the real robot controller, abstracting motion and I/O operations.
      """

    def __init__(self, ip):
        """
               Initializes the robot wrapper and connects to the robot via RPC.

               Args:
                   ip (str): IP address of the robot controller.
               """
        # Initialize ROS2 node
        super().__init__('zero_err_robot_wrapper')

        self.ip = ip
        self.logger_context = LoggerContext(logger=robot_logger, enabled=ENABLE_LOGGING)

        # ROS2 Publishers for robot commands (same as cartesian_gui)
        self.cartesian_pub = self.create_publisher(Pose, '/gui_cartesian_command', 10)
        self.joint_pub = self.create_publisher(Float64MultiArray, '/gui_joint_command', 10)
        self.speed_pub = self.create_publisher(Float32MultiArray, '/gui_speed_scaling', 10)
        self.cartesian_path_pub = self.create_publisher(PoseArray, '/gui_cartesian_path', 10)

        # Publisher for PILZ motion sequences (smooth jogging with blend radii)
        self.motion_sequence_pub = self.create_publisher(MotionSequenceRequest, '/gui_motion_sequence', 10)

        # Publisher for digital I/O
        self.digital_io_pub = self.create_publisher(Int32MultiArray, '/gui_digital_output', 10)

        # ROS2 Subscribers for robot state
        self.joint_state_sub = self.create_subscription(
            JointState, '/joint_states', self._joint_state_callback, 10
        )
        self.command_complete_sub = self.create_subscription(
            Bool, '/gui_command_complete', self._command_complete_callback, 10
        )

        # FK service client for getting current position (like cartesian_gui)
        self.fk_client = self.create_client(GetPositionFK, '/compute_fk')

        # State variables
        self.current_joint_state = None
        self.joint_names = ['Joint_1', 'Joint_2', 'Joint_3', 'Joint_4', 'Joint_5', 'Joint_6']

        # Initialize with HOME position (87mm, -353mm, 203mm, -90°, 0°, -180°)
        self.current_pose = [0.087, -0.353, 0.203, -90.0, 0.0, -180.0]  # [x, y, z, rx, ry, rz]
        self.command_in_progress = False
        self.last_command_success = True
        self.last_command_time = 0.0
        self.velocity_scaling = 0.9
        self.acceleration_scaling = 0.8

        # Digital output simulation
        self.digital_outputs = {}

        # TCP Calibration state
        self.tcp_calibration_points = []
        self._init_tcp_calibration_subscribers()

        log_info_message(self.logger_context, f"ROS2 RobotWrapper initialized (MoveIt interface)")
        log_info_message(self.logger_context, f"Initial position: HOME [87mm, -353mm, 203mm, -90°, 0°, -180°]")

        # Timer to query FK for current position (like cartesian_gui does)
        self.fk_timer = self.create_timer(0.05, self._update_current_pose_from_moveit)  # 10Hz

        # Give time for connections
        time.sleep(0.2)
        pass

    def _joint_state_callback(self, msg: JointState):
        """Store joint states for FK queries"""
        if len(msg.position) >= 6:
            self.current_joint_state = msg

    def _command_complete_callback(self, msg: Bool):
        """Callback when command completes (success or failure)"""
        self.command_in_progress = False
        self.last_command_success = msg.data
        if msg.data:
            log_debug_message(self.logger_context, "Command completed successfully")
        else:
            log_debug_message(self.logger_context, "Command failed")

    def _update_current_pose_from_moveit(self):
        """
        Query MoveIt for current EE pose using FK service (same as cartesian_gui).
        MoveIt does the FK computation, we just READ the result.
        """
        if not self.current_joint_state:
            return

        if not self.fk_client.service_is_ready():
            return

        req = GetPositionFK.Request()
        req.header.frame_id = 'base_link'
        req.fk_link_names = ['tcp']
        req.robot_state.joint_state.name = self.joint_names
        req.robot_state.joint_state.position = list(self.current_joint_state.position[:6])

        future = self.fk_client.call_async(req)
        future.add_done_callback(self._fk_result_callback)

    def _fk_result_callback(self, future):
        """Handle FK result from MoveIt - just READ and store"""
        try:
            result = future.result()
            if result and len(result.pose_stamped) > 0:
                pose = result.pose_stamped[0].pose

                # Store position in meters
                self.current_pose[0] = pose.position.x
                self.current_pose[1] = pose.position.y
                self.current_pose[2] = pose.position.z

                # Store orientation in degrees
                from scipy.spatial.transform import Rotation as R
                quat = [pose.orientation.x, pose.orientation.y,
                        pose.orientation.z, pose.orientation.w]
                rot = R.from_quat(quat)
                euler = rot.as_euler('xyz', degrees=True)
                self.current_pose[3] = euler[0]
                self.current_pose[4] = euler[1]
                self.current_pose[5] = euler[2]
        except Exception as e:
            log_error_message(self.logger_context, f'FK result processing failed: {e}')

    def move_cartesian(self, position, tool=0, user=0, vel=30, acc=30, blendR=0):
        """
              Moves the robot in Cartesian space.

              Args:
                  position (list): Target Cartesian position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.

              Returns:
                  list: Result from robot move command.
              """

        # NOTE: Removed command_in_progress check because:
        # 1. moveCart is already non-blocking (just publishes and returns)
        # 2. Sequential movements with waitToReachPosition handle synchronization
        # 3. The flag was never reliably cleared, blocking all subsequent movements

        print(f"[FairinoRobot] moveCart called with position: {position}")
        print(f"[FairinoRobot]   X={position[0]:.2f}mm, Y={position[1]:.2f}mm, Z={position[2]:.2f}mm")
        print(f"[FairinoRobot]   RX={position[3]:.2f}°, RY={position[4]:.2f}°, RZ={position[5]:.2f}°")
        print(f"[FairinoRobot]   vel={vel}, acc={acc}")

        # Reset command status before sending new command
        self.last_command_success = True
        self.command_in_progress = True

        # Convert position from mm to meters and degrees to radians for quaternion
        pose = Pose()
        pose.position.x = position[0] / 1000.0  # mm to m
        pose.position.y = position[1] / 1000.0
        pose.position.z = position[2] / 1000.0

        print(
            f"[FairinoRobot]   Pose in meters: X={pose.position.x:.4f}m, Y={pose.position.y:.4f}m, Z={pose.position.z:.4f}m")

        # Convert RPY (degrees) to quaternion
        from scipy.spatial.transform import Rotation as R
        rot = R.from_euler('xyz', [position[3], position[4], position[5]], degrees=True)
        quat = rot.as_quat()  # [x, y, z, w]
        pose.orientation.x = quat[0]
        pose.orientation.y = quat[1]
        pose.orientation.z = quat[2]
        pose.orientation.w = quat[3]

        # Update speed scaling
        self._set_speed_scaling(vel, acc)

        # Publish command
        print(f"[FairinoRobot]   Publishing to ROS2 cartesian topic...")
        self.cartesian_pub.publish(pose)
        print(f"[FairinoRobot]   ✓ Command published to ROS2")

        # log_debug_message(self.logger_context,
        # f"MoveCart to [{position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}] mm, "
        # f"orientation [{position[3]:.1f}, {position[4]:.1f}, {position[5]:.1f}]°")

        return 0

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

        # For single moves, MoveL is same as MoveCart with Pilz LIN
        result = self.moveCart(position, tool, user, vel, acc)
        # log_debug_message(self.logger_context,
        # f"MoveL to {position} with blendR {blendR} -> routed to MoveCart")
        return result

    def moveCartesianPath(self, waypoints, vel=100, acc=30, decimate=True):
        """
        Execute smooth Cartesian path through many waypoints (1000-2000 points).
        Uses MoveIt's Cartesian path planner for ultra-smooth motion without deviations.

        Args:
            waypoints (list): List of positions [[x,y,z,rx,ry,rz], ...] in mm and degrees
            vel (float): Velocity percentage (0-100)
            acc (float): Acceleration percentage (0-100)
            decimate (bool): Remove redundant waypoints for faster computation (default: True)

        Returns:
            int: 0 for success, -1 for failure
        """
        print(f"[FairinoRobot] moveCartesianPath: {len(waypoints)} waypoints")
        print(f"[FairinoRobot]   vel={vel}, acc={acc}, decimate={decimate}")

        # Debug: Log first and last waypoints
        if len(waypoints) > 0:
            first = waypoints[0]
            last = waypoints[-1]
            print(
                f"[FairinoRobot]   First waypoint: [{first[0]:.1f}, {first[1]:.1f}, {first[2]:.1f}] mm, [{first[3]:.1f}, {first[4]:.1f}, {first[5]:.1f}]°")
            print(
                f"[FairinoRobot]   Last waypoint:  [{last[0]:.1f}, {last[1]:.1f}, {last[2]:.1f}] mm, [{last[3]:.1f}, {last[4]:.1f}, {last[5]:.1f}]°")

            # Check for suspicious angle values
            import numpy as np
            all_rz = [w[5] for w in waypoints]
            rz_min, rz_max = min(all_rz), max(all_rz)
            rz_range = rz_max - rz_min
            print(f"[FairinoRobot]   RZ range: {rz_min:.1f}° to {rz_max:.1f}° (span: {rz_range:.1f}°)")

            if rz_range > 180:
                print(f"[FairinoRobot]   ⚠️  WARNING: RZ range exceeds 180° - may cause path planning issues")

        # Reset command status before sending new command
        self.last_command_success = True
        self.command_in_progress = True

        # Decimate waypoints if enabled and path is large
        if decimate and len(waypoints) > 1000:
            original_count = len(waypoints)
            waypoints = self._decimate_waypoints(waypoints)
            print(f"[FairinoRobot]   Decimated {original_count} → {len(waypoints)} waypoints")

        # Update speed scaling
        self._set_speed_scaling(vel, acc)

        # Convert waypoints to PoseArray with quaternion continuity
        pose_array = PoseArray()
        pose_array.header.frame_id = 'base_link'

        from scipy.spatial.transform import Rotation as R
        import numpy as np

        prev_quat = None

        for i, position in enumerate(waypoints):
            pose = Pose()
            pose.position.x = position[0] / 1000.0  # mm to m
            pose.position.y = position[1] / 1000.0
            pose.position.z = position[2] / 1000.0

            # Convert RPY to quaternion
            rot = R.from_euler('xyz', [position[3], position[4], position[5]], degrees=True)
            quat = rot.as_quat()  # [x, y, z, w]

            # CRITICAL: Ensure quaternion continuity to prevent 180° turns
            # Quaternions q and -q represent the same rotation, but MoveIt picks shortest path
            # We must ensure we always use the quaternion closest to the previous one
            if prev_quat is not None:
                # Calculate dot product with previous quaternion
                dot = np.dot(quat, prev_quat)
                # If dot product is negative, quaternions point in "opposite" directions
                # Flip the sign to get the closest representation
                if dot < 0:
                    quat = -quat
                    if i < 5:  # Log first few flips for debugging
                        print(f"[FairinoRobot]   Waypoint {i}: Flipped quaternion for continuity (dot={dot:.3f})")

            pose.orientation.x = quat[0]
            pose.orientation.y = quat[1]
            pose.orientation.z = quat[2]
            pose.orientation.w = quat[3]

            prev_quat = quat
            pose_array.poses.append(pose)

        # Publish to Cartesian path topic
        print(f"[FairinoRobot]   Publishing {len(pose_array.poses)} waypoints to /gui_cartesian_path...")
        print(f"[FairinoRobot]   Quaternion continuity enforced for smooth rotation")
        self.cartesian_path_pub.publish(pose_array)
        print(f"[FairinoRobot]   ✓ Cartesian path published")

        log_debug_message(self.logger_context,
                          f"moveCartesianPath: {len(waypoints)} waypoints sent to MoveIt Cartesian planner")

        return 0

    def _decimate_waypoints(self, waypoints, position_threshold=0.5, angle_threshold=1.0):
        """
        Remove redundant waypoints that are too close to neighbors.

        Args:
            waypoints: List of [x,y,z,rx,ry,rz] in mm and degrees
            position_threshold: Minimum distance between points in mm (default: 0.5mm)
            angle_threshold: Minimum angle change in degrees (default: 1.0°)

        Returns:
            Decimated waypoint list
        """
        if len(waypoints) < 3:
            return waypoints

        decimated = [waypoints[0]]  # Always keep first point

        for i in range(1, len(waypoints) - 1):
            prev = decimated[-1]
            curr = waypoints[i]

            # Calculate position distance
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            dz = curr[2] - prev[2]
            pos_dist = (dx * dx + dy * dy + dz * dz) ** 0.5

            # Calculate orientation change
            drx = abs(curr[3] - prev[3])
            dry = abs(curr[4] - prev[4])
            drz = abs(curr[5] - prev[5])
            angle_change = max(drx, dry, drz)

            # Keep point if it's far enough from previous
            if pos_dist > position_threshold or angle_change > angle_threshold:
                decimated.append(curr)

        decimated.append(waypoints[-1])  # Always keep last point

        return decimated

    def get_current_position(self, use_cached=True):
        """
              Retrieves the current TCP (tool center point) position.

              Returns:
                  list: Current robot TCP pose.
              """
        # If not using cached, do a blocking FK call for most accurate position
        if not use_cached and self.current_joint_state and self.fk_client.service_is_ready():
            try:
                req = GetPositionFK.Request()
                req.header.frame_id = 'base_link'
                req.fk_link_names = ['tcp']
                req.robot_state.joint_state.name = self.joint_names
                req.robot_state.joint_state.position = list(self.current_joint_state.position[:6])

                # Call service and wait for result (blocking but doesn't interfere with spin thread)
                future = self.fk_client.call_async(req)

                # Wait for result with timeout
                timeout_start = time.time()
                while not future.done() and (time.time() - timeout_start) < 0.1:
                    time.sleep(0.005)  # Small sleep to not block everything

                if future.done() and future.result():
                    result = future.result()
                    if result and len(result.pose_stamped) > 0:
                        pose = result.pose_stamped[0].pose

                        # Update cached position
                        self.current_pose[0] = pose.position.x
                        self.current_pose[1] = pose.position.y
                        self.current_pose[2] = pose.position.z

                        from scipy.spatial.transform import Rotation as R
                        quat = [pose.orientation.x, pose.orientation.y,
                                pose.orientation.z, pose.orientation.w]
                        rot = R.from_quat(quat)
                        euler = rot.as_euler('xyz', degrees=True)
                        self.current_pose[3] = euler[0]
                        self.current_pose[4] = euler[1]
                        self.current_pose[5] = euler[2]

                        log_debug_message(self.logger_context,
                                          f'Sync FK query: [{self.current_pose[0] * 1000:.1f}, {self.current_pose[1] * 1000:.1f}, {self.current_pose[2] * 1000:.1f}] mm')
            except Exception as e:
                log_debug_message(self.logger_context, f'Synchronous FK failed, using cached: {e}')

        # Return cached pose (from FK service updated at 10Hz or from sync call above)
        # Converting from meters to mm
        pose_mm = [
            self.current_pose[0] * 1000.0,  # x
            self.current_pose[1] * 1000.0,  # y
            self.current_pose[2] * 1000.0,  # z
            self.current_pose[3],  # rx (already in degrees)
            self.current_pose[4],  # ry
            self.current_pose[5]  # rz
        ]
        return pose_mm

    def get_current_velocity(self):
        """
               Retrieves the current linear speed of the TCP.

               Returns:
                   float: TCP composite speed.
               """

        log_debug_message(self.logger_context, "GetCurrentLinerSpeed called (mock data)")
        return (0, [0.0])

    def get_current_acceleration(self):
        """
               Retrieves the current linear acceleration of the TCP.

               Returns:
                   float: TCP composite acceleration.
               """

        log_debug_message(self.logger_context, "GetCurrentAcceleration called (mock data)")
        return (0, [0.0])

    def enable(self):
        """
               Enables the robot, allowing motion.
               """

        log_info_message(self.logger_context, "Enable called (handled by controller)")
        pass

    def disable(self):
        """
             Disables the robot, preventing motion.
             """
        log_info_message(self.logger_context, "Disable called (handled by controller)")
        pass

    def printSdkVersion(self):
        """Prints the SDK version."""
        version = "ROS2 MoveIt Interface v1.0 (TracIK + Pilz)"
        print(version)
        return version

    def setDigitalOutput(self, portId, value):
        """
        Sets a digital output via ROS2 topic.

        Args:
            portId (int): Output port number.
            value (int): Value to set (0 or 1).

        Returns:
            int: 0 for success.
        """

        msg = Int32MultiArray()
        msg.data = [int(portId), int(value)]
        self.digital_io_pub.publish(msg)

        log_debug_message(self.logger_context,
                          f"SetDigitalOutput port {portId} to {value}")
        return 0

    def start_jog(self, axis: RobotAxis, direction: Direction, step, vel, acc):
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
        # Get current position
        current = self.get_current_position()
        if current is None:
            return -1

        # Calculate new position based on jog
        new_position = current.copy()
        axis_idx = axis.value - 1  # Axis enum is 1-indexed
        step_dir = step * direction.value

        if axis_idx < 3:  # Linear axes (X, Y, Z) - step is in mm
            new_position[axis_idx] += step_dir
        else:  # Rotational axes (RX, RY, RZ) - step is in degrees
            new_position[axis_idx] += step_dir

        log_debug_message(self.logger_context,
                          f"StartJog {axis.name} {direction.name} step={step} vel={vel} acc={acc}")
        log_debug_message(self.logger_context,
                          f"From {current} -> To {new_position}")

        # Convert position from mm to meters and degrees to radians for quaternion
        pose = Pose()
        pose.position.x = new_position[0] / 1000.0  # mm to m
        pose.position.y = new_position[1] / 1000.0
        pose.position.z = new_position[2] / 1000.0

        # Convert RPY (degrees) to quaternion
        from scipy.spatial.transform import Rotation as R
        rot = R.from_euler('xyz', [new_position[3], new_position[4], new_position[5]], degrees=True)
        quat = rot.as_quat()  # [x, y, z, w]
        pose.orientation.x = quat[0]
        pose.orientation.y = quat[1]
        pose.orientation.z = quat[2]
        pose.orientation.w = quat[3]

        # Update speed scaling
        self._set_speed_scaling(vel, acc)

        # Publish command (NON-BLOCKING - just publish and return)
        self.cartesian_pub.publish(pose)

        # NOTE: We do NOT set command_in_progress for jog commands
        # This allows rapid successive jog commands without waiting

        return 0

    def stop_motion(self):
        """
               Stops all current robot motion.

               Returns:
                   object: Result of StopMotion command.
               """
        log_info_message(self.logger_context, "StopMotion called")
        self.command_in_progress = False
        return 0

    def resetAllErrors(self):
        """
        Resets all error states.

        Returns:
            int: 0 for success.
        """
        log_info_message(self.logger_context, "ResetAllError called")
        self.command_in_progress = False
        return 0

    def _set_speed_scaling(self, vel_percent, acc_percent):
        """
        Updates velocity and acceleration scaling and publishes to bridge.

        Args:
            vel_percent (float): Velocity percentage (0-100).
            acc_percent (float): Acceleration percentage (0-100).
        """
        self.velocity_scaling = max(0.01, min(1.0, vel_percent / 100.0))
        self.acceleration_scaling = max(0.01, min(1.0, acc_percent / 100.0))

        msg = Float32MultiArray()
        msg.data = [self.velocity_scaling, self.acceleration_scaling]
        self.speed_pub.publish(msg)

    def wait_for_motion_complete(self, timeout=30.0):
        """
        Waits for current motion to complete.

        Args:
            timeout (float): Maximum time to wait in seconds.

        Returns:
            bool: True if motion completed, False if timeout.
        """
        start_time = time.time()

        while self.command_in_progress and (time.time() - start_time) < timeout:
            rclpy.spin_once(self, timeout_sec=0.01)

        if self.command_in_progress:
            log_error_message(self.logger_context, "Motion timeout")
            return False

        return True

    def _init_tcp_calibration_subscribers(self):
        """Initialize MessageBroker subscribers for TCP calibration"""
        try:
            from modules.shared.MessageBroker import MessageBroker

            self.broker = MessageBroker()
            self.broker.subscribe(RobotTopics.TCP_CALIBRATION_SAVE_POINT, self._on_tcp_save_point)
            self.broker.subscribe(RobotTopics.TCP_CALIBRATION_CLEAR_POINTS, self._on_tcp_clear_points)
            self.broker.subscribe(RobotTopics.TCP_CALIBRATION_COMPUTE, self._on_tcp_compute)

            log_info_message(self.logger_context, "TCP calibration subscribers initialized")
        except Exception as e:
            log_error_message(self.logger_context, f"Failed to initialize TCP calibration: {e}")

    def _on_tcp_save_point(self, message):
        """Save current robot pose for TCP calibration"""
        try:
            current_pose = self.get_current_position()
            current_joints = self.current_joint_state.position[:6] if self.current_joint_state else None

            if current_joints is None:
                self.broker.publish(RobotTopics.TCP_CALIBRATION_STATUS, {
                    "message": "Error: Joint state not available"
                })
                return

            point_data = {
                "point_number": len(self.tcp_calibration_points) + 1,
                "pose": current_pose,
                "joints": list(current_joints)
            }

            self.tcp_calibration_points.append(point_data)

            log_info_message(self.logger_context,
                             f"TCP point {len(self.tcp_calibration_points)} saved: {current_pose}")

            self.broker.publish(RobotTopics.TCP_CALIBRATION_STATUS, {
                "message": f"Point {len(self.tcp_calibration_points)}/4 saved",
                "points_count": len(self.tcp_calibration_points)
            })

        except Exception as e:
            log_error_message(self.logger_context, f"Failed to save TCP point: {e}")
            self.broker.publish(RobotTopics.TCP_CALIBRATION_STATUS, {
                "message": f"Error saving point: {str(e)}"
            })

    def _on_tcp_clear_points(self, message):
        """Clear all saved TCP calibration points"""
        try:

            self.tcp_calibration_points.clear()
            log_info_message(self.logger_context, "TCP calibration points cleared")

            self.broker.publish(RobotTopics.TCP_CALIBRATION_STATUS, {
                "message": "All points cleared",
                "points_count": 0
            })

        except Exception as e:
            log_error_message(self.logger_context, f"Failed to clear TCP points: {e}")

    def _on_tcp_compute(self, message):
        """Compute TCP offset from saved points and send to MoveIt"""
        try:
            import numpy as np

            if len(self.tcp_calibration_points) != 4:
                self.broker.publish(RobotTopics.TCP_CALIBRATION_RESULT, {
                    "success": False,
                    "error": f"Need exactly 4 points, have {len(self.tcp_calibration_points)}"
                })
                return

            # Extract positions (in meters for MoveIt)
            positions = []
            for point in self.tcp_calibration_points:
                pose = point["pose"]
                # Convert from mm to meters
                positions.append([pose[0] / 1000.0, pose[1] / 1000.0, pose[2] / 1000.0])

            positions = np.array(positions)

            # Compute TCP offset as centroid of the 4 points
            tcp_offset = np.mean(positions, axis=0)

            log_info_message(self.logger_context,
                             f"Computed TCP offset: [{tcp_offset[0]:.4f}, {tcp_offset[1]:.4f}, {tcp_offset[2]:.4f}]")

            # Publish TCP offset to MoveIt via ROS2 topic
            tcp_msg = Pose()
            tcp_msg.position.x = tcp_offset[0]
            tcp_msg.position.y = tcp_offset[1]
            tcp_msg.position.z = tcp_offset[2]
            tcp_msg.orientation.w = 1.0  # Identity quaternion

            # Create publisher for TCP offset (MoveIt will use this)
            if not hasattr(self, 'tcp_offset_pub'):
                self.tcp_offset_pub = self.create_publisher(Pose, '/tcp_offset', 10)

            self.tcp_offset_pub.publish(tcp_msg)

            log_info_message(self.logger_context, "TCP offset published to MoveIt")

            self.broker.publish(RobotTopics.TCP_CALIBRATION_RESULT, {
                "success": True,
                "tcp_offset": {
                    "x": tcp_offset[0],
                    "y": tcp_offset[1],
                    "z": tcp_offset[2]
                },
                "points_used": len(self.tcp_calibration_points)
            })

        except Exception as e:
            log_error_message(self.logger_context, f"TCP computation failed: {e}")
            self.broker.publish(RobotTopics.TCP_CALIBRATION_RESULT, {
                "success": False,
                "error": str(e)
            })
