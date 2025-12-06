import os

import numpy as np

from modules.utils.custom_logging import log_if_enabled, LoggingLevel


import os




class DataManager:
    def __init__(self,vision_system,logging_enabled,logger,storage_path):
        self.vision_system = vision_system
        self.storage_path = storage_path

        if storage_path is None:
            raise ValueError("Storage path cannot be None")

        self.ENABLE_LOGGING = logging_enabled
        self.logger = logger
        self.workAreaPoints = None
        self.work_area_polygon = None
        self.pickupAreaPoints = None
        self.sprayAreaPoints = None
        self.cameraToRobotMatrix = None
        self.cameraData = None
        self.perspectiveMatrix = None
        self.isSystemCalibrated = False
        self.build_storage_paths()


    def build_storage_paths(self):
        """Ensure that the storage directories exist."""
        if self.storage_path is not None:
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message = f"VisionSystem DataManager: Building storage paths with path provided {self.storage_path}",)
        else:
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.WARNING,
                           message = f"VisionSystem DataManager: Building storage paths with DEFAULT_STORAGE_PATH",)

        # self.calib_result_path = os.path.join(self.storage_path, 'calibration_result')
        self.camera_data_path = os.path.join(self.storage_path, 'camera_calibration.npz')
        self.perspective_matrix_path = os.path.join(self.storage_path, 'perspectiveTransform.npy')
        self.camera_to_robot_matrix_path = os.path.join(self.storage_path, 'cameraToRobotMatrix_camera_center.npy')
        self.work_area_points_path = os.path.join(self.storage_path, 'workAreaPoints.npy')
        self.pickup_area_points_path = os.path.join(self.storage_path, 'pickupAreaPoints.npy')
        self.spray_area_points_path = os.path.join(self.storage_path, 'sprayAreaPoints.npy')

    def loadWorkAreaPoints(self):
        try:
            self.workAreaPoints = np.load(self.work_area_points_path)
            self.work_area_polygon = np.array(self.workAreaPoints, dtype=np.int32).reshape((-1, 1, 2))
            self.isSystemCalibrated = True
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"Work area points loaded from: {self.work_area_points_path}",
                           broadcast_to_ui=False)

        except FileNotFoundError:
            self.workAreaPoints = None
            self.isSystemCalibrated = False
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"Work area points file not found at {self.work_area_points_path}",
                           broadcast_to_ui=False)

        # Load pickup area points
        try:
            self.pickupAreaPoints = np.load(self.work_area_points_path)
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"Pickup area points loaded successfully from: {self.work_area_points_path}",
                           broadcast_to_ui=False)
        except FileNotFoundError:
            self.pickupAreaPoints = None
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"Pickup area points file not found in {self.work_area_points_path}- will be created when first saved",
                           broadcast_to_ui=False)
        # Load spray area points
        try:
            self.sprayAreaPoints = np.load(self.spray_area_points_path)
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"Spray area points loaded successfully from: {self.spray_area_points_path}",
                           broadcast_to_ui=False)
        except FileNotFoundError:
            self.sprayAreaPoints = None
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"Spray area points file not found in {self.spray_area_points_path} - will be created when first saved",
                           broadcast_to_ui=False)


    def loadCameraToRobotMatrix(self):
        try:
            self.cameraToRobotMatrix = np.load(self.camera_to_robot_matrix_path)
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"Camera to Robot matrix loaded from: {self.camera_to_robot_matrix_path}",
                           broadcast_to_ui=False)
        except FileNotFoundError:
            self.cameraToRobotMatrix = None
            self.isSystemCalibrated = True
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"File not found: {self.camera_to_robot_matrix_path}",
                           broadcast_to_ui=False)


    def loadCameraCalibrationData(self):
        try:
            self.cameraData = np.load(self.camera_data_path)
            self.isSystemCalibrated = True
        except FileNotFoundError:
            self.cameraData = None
            self.isSystemCalibrated = False
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"Camera calibration data file not found at {self.camera_data_path}",
                           broadcast_to_ui=False)


    def loadPerspectiveMatrix(self):
        try:
            self.perspectiveMatrix = np.load(self.perspective_matrix_path)
            print(f"✅ Perspective matrix loaded from: {self.perspective_matrix_path}")
        except FileNotFoundError:
            self.perspectiveMatrix = None
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"No perspective matrix found at: {self.perspective_matrix_path}",
                           broadcast_to_ui=False)




    def saveWorkAreaPoints(self, data):
        """
        Saves the work area points captured by the camera service.
        Supports both legacy format (list of points) and new format (dict with area_type and corners).
        """

        print(f"In  VisionSystem.saveWorkAreaPoints with data: {data}")

        if data is None or len(data) == 0:
            return False, "No data provided to save"

        try:
            # Handle new format with area type
            if isinstance(data, dict) and 'area_type' in data and 'corners' in data:
                area_type = data['area_type']
                points = data['corners']

                if area_type not in ['pickup', 'spray']:
                    return False, f"Invalid area_type: {area_type}. Must be 'pickup' or 'spray'"

                if points is None or len(points) == 0:
                    return False, f"No points provided for {area_type} area"

                points_array = np.array(points, dtype=np.float32)

                # Save to area-specific file
                if area_type == 'pickup':
                    np.save(self.work_area_points_path, points_array)
                    self.pickupAreaPoints = points_array
                    message = f"Pickup area points saved successfully"
                    log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                                   level=LoggingLevel.INFO,
                                   message=f"Saved pickup area points to {self.work_area_points_path}",
                                   broadcast_to_ui=False)
                else:  # spray
                    np.save(self.spray_area_points_path, points_array)
                    log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                                   level=LoggingLevel.INFO,
                                   message=f"Saved spray area points to {self.work_area_points_path}",
                                   broadcast_to_ui=False)
                    self.sprayAreaPoints = points_array
                    message = f"Spray area points saved successfully"

                # Also save to legacy path for backward compatibility if this is the first area saved
                if not hasattr(self, 'workAreaPoints') or self.workAreaPoints is None:
                    np.save(self.work_area_points_path, points_array)
                    self.workAreaPoints = points_array
                    self.work_area_polygon = np.array(self.workAreaPoints, dtype=np.int32).reshape((-1, 1, 2))
                    log_if_enabled(enabled=self.ENABLE_LOGGING,
                                    logger=self.logger,
                                   level=LoggingLevel.INFO,
                                   message=f"Also saved to legacy work area points at {self.work_area_points_path}",
                                   broadcast_to_ui=False)

                return True, message

            # Handle legacy format (list of points)
            else:
                points = data
                points_array = np.array(points, dtype=np.float32)
                np.save(self.work_area_points_path, points_array)
                self.workAreaPoints = points_array
                self.work_area_polygon = np.array(self.workAreaPoints, dtype=np.int32).reshape((-1, 1, 2))
                log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                               level=LoggingLevel.INFO,
                               message=f"Work area points saved successfully (legacy format)",
                               broadcast_to_ui=False)
                return True, "Work area points saved successfully (legacy format)"

        except Exception as e:
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"Error saving work area points: {str(e)}",
                           broadcast_to_ui=False)
            return False, f"Error saving work area points: {str(e)}"

    def get_camera_matrix(self):
        return self.cameraData['mtx'] if self.cameraData is not None else None



    def get_distortion_coefficients(self):
        return self.cameraData['dist'] if self.cameraData is not None else None