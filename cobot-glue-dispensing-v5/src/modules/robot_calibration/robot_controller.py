import numpy as np

from modules.utils.custom_logging import log_debug_message


class CalibrationRobotController:
    def __init__(self, robot_service, adaptive_movement_config, logger_context):
        self.robot_service = robot_service
        self.adaptive_movement_config = adaptive_movement_config
        self.logger_context = logger_context


    def move_to_position(self,position,blocking=False):
        result = self.robot_service.move_to_position(position=position,
                                                     tool=self.robot_service.robot_config.robot_tool,
                                                     workpiece=self.robot_service.robot_config.robot_user,
                                                     velocity=30,
                                                     acceleration=10,
                                                     waitToReachPosition=blocking)

        return result


    def get_iterative_align_position(self,current_error_mm, offset_x_mm, offset_y_mm,alignment_threshold_mm):
        # --- Adaptive movement scaling (fast convergence + derivative control) ---
        min_step_mm = self.adaptive_movement_config.min_step_mm  # minimum movement (for very small errors)
        max_step_mm = self.adaptive_movement_config.max_step_mm  # maximum movement for very large misalignments
        target_error_mm = alignment_threshold_mm
        max_error_ref = self.adaptive_movement_config.max_error_ref  # error at which we reach max step
        k = self.adaptive_movement_config.k  # responsiveness (1.0 = smooth, 2.0 = faster reaction)
        derivative_scaling = self.adaptive_movement_config.derivative_scaling  # how strongly derivative term reduces step (tune this)

        # Compute normalized error
        normalized_error = min(current_error_mm / max_error_ref, 1.0)

        # Tanh curve for smooth aggressive scaling
        step_scale = np.tanh(k * normalized_error)
        max_move_mm = min_step_mm + step_scale * (max_step_mm - min_step_mm)

        # Near the target, apply soft damping
        if current_error_mm < target_error_mm * 2:
            damping_ratio = (current_error_mm / (target_error_mm * 2)) ** 2  # quadratic damping
            max_move_mm *= max(damping_ratio, 0.05)

        # Derivative control to reduce overshoot
        # Requires storing previous_error_mm (from last iteration)
        if hasattr(self, 'previous_error_mm'):
            error_change = current_error_mm - self.previous_error_mm
            derivative_factor = 1.0 / (1.0 + derivative_scaling * abs(error_change))
            max_move_mm *= derivative_factor

        # Save current error for next iteration
        self.previous_error_mm = current_error_mm

        # Optional: hard stop when very close to target
        if current_error_mm < target_error_mm * 0.5:
            max_move_mm = min_step_mm

        # For robot movement:
        # - If marker is to the RIGHT of image center (offset_x_mm > 0), move robot RIGHT (+X)
        # - If marker is to the LEFT of image center (offset_x_mm < 0), move robot LEFT (-X)
        # - If marker is BELOW image center (offset_y_mm > 0), move robot BACK (+Y)
        # - If marker is ABOVE image center (offset_y_mm < 0), move robot FORWARD (-Y)

        # move_x_mm = max(-max_move_mm, min(max_move_mm, offset_x_mm))  # Move toward marker
        # move_y_mm = max(-max_move_mm, min(max_move_mm, -offset_y_mm))  # Y inverted: image down = robot back

        move_x_mm = max(-max_move_mm, min(max_move_mm, offset_x_mm))
        move_y_mm = max(-max_move_mm, min(max_move_mm, offset_y_mm))

        log_debug_message(self.logger_context,f"Adaptive movement: max_move={max_move_mm:.1f}mm (error={current_error_mm:.3f}mm)")
        log_debug_message(self.logger_context,f"Making iterative movement: X+={move_x_mm:.3f}mm, Y+={move_y_mm:.3f}mm")

        # Move robot by small increment
        current_pose = self.robot_service.get_current_position()
        x, y, z, rx, ry, rz = current_pose
        x += move_x_mm
        y += move_y_mm
        iterative_position = [x, y, z, rx, ry, rz]
        return iterative_position

    def move_to_calibration_position(self):
        self.robot_service.move_to_calibration_position()

    def get_current_z_value(self):
        result = self.robot_service.get_current_position()
        print(f"[CalibrationRobotController] Current Z value: {result} mm")
        return  result[2]

    def get_current_position(self):
        return self.robot_service.get_current_position()

    def get_calibration_position(self):
        return self.robot_service.robot_config.getCalibrationPositionParsed()

    def move_y_relative(self,dy_mm,blocking=False):
        current_pose = self.robot_service.get_current_position()
        x, y, z, rx, ry, rz = current_pose
        y += dy_mm
        new_position = [x, y, z, rx, ry, rz]
        result = self.robot_service.move_to_position(position=new_position,
                                                     tool=self.robot_service.robot_config.robot_tool,
                                                     workpiece=self.robot_service.robot_config.robot_user,
                                                     velocity=30,
                                                     acceleration=10,
                                                     waitToReachPosition=blocking)
        return result

    def move_x_relative(self,dx_mm,blocking=False):
        current_pose = self.robot_service.get_current_position()
        x, y, z, rx, ry, rz = current_pose
        x += dx_mm
        new_position = [x, y, z, rx, ry, rz]
        result = self.robot_service.move_to_position(position=new_position,
                                                     tool=self.robot_service.robot_config.robot_tool,
                                                     workpiece=self.robot_service.robot_config.robot_user,
                                                     velocity=30,
                                                     acceleration=10,
                                                     waitToReachPosition=blocking)
        return result