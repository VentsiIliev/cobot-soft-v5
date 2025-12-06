import time

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.preprocessing import PolynomialFeatures

from core.services.robot_service.impl.base_robot_service import RobotService
from modules.VisionSystem.laser_detection.config import LaserCalibrationConfig
from modules.VisionSystem.laser_detection.storage import LaserCalibrationStorage


class LaserDetectionCalibration:
    def __init__(
        self,
        laser_service,
        robot_service: RobotService,
        config: LaserCalibrationConfig = None,
        storage: LaserCalibrationStorage = None
    ):
        """
        Initialize laser calibration service.

        Args:
            laser_service: LaserDetectionService instance
            robot_service: RobotService instance
            config: LaserCalibrationConfig instance (uses default if None)
            storage: LaserCalibrationStorage instance (creates new if None)
        """
        self.laser_service = laser_service
        self.robot_service = robot_service
        self.config = config if config is not None else LaserCalibrationConfig()
        self.storage = storage if storage is not None else LaserCalibrationStorage()

        self.zero_reference_coords = None
        self.calibration_data = []  # list of tuples holding actual delta in mm -> detected pixel delta
        self.poly_model = None
        self.poly_transform = None
        self.poly_degree = None
        self.poly_r2 = None
        self.robot_initial_position = None

    def print_calibration_data(self):
        for i, entry in enumerate(self.calibration_data, start=1):
            print(f"{i}. [{entry}]")

    def move_to_initial_position(self, position):
        """Move robot to initial calibration position using config values."""
        self.robot_service.move_to_position(
            position=position,
            tool=self.robot_service.robot_config.robot_tool,
            workpiece=self.robot_service.robot_config.robot_user,
            velocity=self.config.calibration_velocity,
            acceleration=self.config.calibration_acceleration,
            waitToReachPosition=False
        )
        self.robot_service._waitForRobotToReachPosition(
            position,
            threshold=self.config.movement_threshold,
            delay=0,
            timeout=self.config.movement_timeout
        )
        return True

    def check_min_safety_limit(self):
        current_pos = self.robot_service.get_current_position()
        if current_pos is None:
            print("[ERROR] Unable to get current robot position.")
            return False
        min_z = self.robot_service.robot_config.robot_calibration_settings.min_safety_z_mm
        if current_pos[2] <= min_z:
            print(f"[ERROR] Current Z position {current_pos[2]}mm is at or below minimum safety limit of {min_z}mm.")
            return False
        return True

    def move_down_by_mm(self, mm):
        """Move robot down by specified mm using config values."""
        current_pos = self.robot_service.get_current_position()
        if current_pos is None:
            print("[ERROR] Unable to get current robot position.")
            return False
        new_pos = current_pos.copy()
        new_pos[2] -= mm  # assuming Z axis is at index 2
        self.robot_service.move_to_position(
            position=new_pos,
            tool=self.robot_service.robot_config.robot_tool,
            workpiece=self.robot_service.robot_config.robot_user,
            velocity=self.config.calibration_velocity,
            acceleration=self.config.calibration_acceleration,
            waitToReachPosition=False
        )
        self.robot_service._waitForRobotToReachPosition(
            new_pos,
            threshold=self.config.movement_threshold,
            delay=0,
            timeout=self.config.movement_timeout
        )
        return True

    def calibrate(self, initial_position, iterations=None, step_mm=None, delay_between_move_detect_ms=None):
        """
        Run laser calibration process.

        Args:
            initial_position: Initial robot position for calibration
            iterations: Number of calibration steps (uses config default if None)
            step_mm: Step size in mm (uses config default if None)
            delay_between_move_detect_ms: Delay between move and detect (uses config default if None)

        Returns:
            bool: True if successful, False otherwise
        """
        # Use config defaults if not specified
        iterations = iterations if iterations is not None else self.config.num_iterations
        step_mm = step_mm if step_mm is not None else self.config.step_size_mm
        delay_between_move_detect_ms = delay_between_move_detect_ms if delay_between_move_detect_ms is not None else self.config.delay_between_move_detect_ms
        self.move_to_initial_position(initial_position)
        self.robot_initial_position = initial_position
        time.sleep(delay_between_move_detect_ms/1000.0)
        mask, bright, closest = self.laser_service.detect(axis='y', delay_ms=delay_between_move_detect_ms)
        self.zero_reference_coords = closest
        if self.zero_reference_coords is None:
            print("[ERROR] Laser line not detected at initial position.")
            return False

        # add the zero point to the calibration data
        self.calibration_data.append((0, 0.0)) # height in mm, delta in pixels

        for i in range(1, iterations + 1):
            # move down the robot by step provided in mm
            self.move_down_by_mm(step_mm)
            time.sleep(delay_between_move_detect_ms/1000.0)

            max_attempts = self.config.calibration_max_attempts
            while max_attempts > 0:
                mask, bright, closest = self.laser_service.detect(
                    axis='y',
                    delay_ms=delay_between_move_detect_ms,
                    max_retries=self.config.calibration_detection_retries
                )
                if closest is None:
                    print(f"[WARN] Laser line not detected at iteration {i}. Skipping.")
                    continue

                delta_pixels = self.zero_reference_coords[0] - closest[0]  # X-axis delta
                if delta_pixels > 0:
                    max_attempts -= 1
                    continue
                current_height = i * step_mm  # assuming Z axis is at index 2
                self.calibration_data.append((current_height, delta_pixels))
                print(f"[INFO] Captured calibration point: Height={current_height}mm, Delta={delta_pixels} pixels")
                max_attempts = 0

        self.pick_best_polynomial_fit(
            max_degree=self.config.max_polynomial_degree,
            save_filename="laser_calibration.json"
        )
        return True

    def save_calibration(self, filename="laser_calibration.json"):
        """
        Save calibration data and best-fit polynomial using storage service.

        Args:
            filename: Name of the calibration file

        Returns:
            bool: True if successful, False otherwise
        """
        data_to_save = {
            "zero_reference_coords": self.zero_reference_coords,
            "calibration_data": self.calibration_data,
            "robot_initial_position": self.robot_initial_position
        }

        if self.poly_model is not None:
            data_to_save["polynomial"] = {
                "coefficients": self.poly_model.coef_.tolist(),
                "intercept": float(self.poly_model.intercept_),
                "degree": self.poly_degree,
                "r2": float(self.poly_r2)
            }

        # Use storage service to save
        return self.storage.save_calibration(data_to_save, filename)

    def pick_best_polynomial_fit(self, max_degree=None, save_filename=None):
        """
        Automatically pick the best polynomial degree for pixel_delta -> height mapping.
        Optionally saves both calibration data and polynomial model using storage service.

        Args:
            max_degree: Maximum polynomial degree to test (uses config default if None)
            save_filename: Filename to save calibration (saves if not None)
        """
        # Use config default if not specified
        max_degree = max_degree if max_degree is not None else self.config.max_polynomial_degree

        if not self.calibration_data or len(self.calibration_data) < 2:
            print("[WARN] Not enough calibration data to fit a model.")
            return None

        heights = np.array([h for h, d in self.calibration_data])
        deltas = np.array([d for h, d in self.calibration_data])

        best_r2 = -np.inf
        best_degree = 1
        best_model = None
        best_poly = None

        for degree in range(1, max_degree + 1):
            poly = PolynomialFeatures(degree)
            X_poly = poly.fit_transform(deltas.reshape(-1, 1))
            model = LinearRegression()
            model.fit(X_poly, heights)
            pred = model.predict(X_poly)
            r2 = r2_score(heights, pred)
            if r2 > best_r2:
                best_r2 = r2
                best_degree = degree
                best_model = model
                best_poly = poly

        self.poly_model = best_model
        self.poly_transform = best_poly
        self.poly_degree = best_degree
        self.poly_r2 = best_r2

        print(f"[INFO] Best polynomial degree: {best_degree}, R²={best_r2:.4f}")

        # Save everything using storage service
        if save_filename:
            self.save_calibration(save_filename)
