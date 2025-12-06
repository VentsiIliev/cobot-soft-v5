import queue
import time

import numpy as np

from modules import utils
from communication_layer.api.v1.topics import VisionTopics
from modules.VisionSystem.VisionSystem import VisionSystem
import os
import json
import cv2
import threading
from pathlib import Path
from modules.shared.MessageBroker import MessageBroker




class _VisionService(VisionSystem):
    """
        Vision service class for processing camera frames and detecting contours, workpieces, and ArUco markers.

    This class extends the VisionSystem and handles real-time frame processing, contour detection,
    filtering workpieces within a defined area, and interfacing with robot calibration and workpieces services.

    Attributes:
        MAX_QUEUE_SIZE (int): Maximum number of frames to store in the queue.
        frameQueue (queue.Queue): A queue to store the most recent frames for processing.
        contours (list): Detected contours in the current frame.
        workAreaCorners (dict): Coordinates defining the workpieces pickup area.
        filteredContours (list): Contours that are filtered based on the work area.
        drawOverlay (bool): Flag to determine whether to draw overlays on the frame.


    """

    def __init__(self):
        """
            Initializes the VisionService with camera settings and prepares the frame queue and other attributes.

            This constructor initializes the camera service, the frame queue to store the latest frames,
            and loads the camera-to-robot matrix for transformation.

            Args:
                None
            """
        from core.application.ApplicationContext import get_core_settings_path
        from core.application.ApplicationContext import get_calibration_storage_path

        # Get camera settings path from application context
        config_file_path = get_core_settings_path("camera_settings.json", create_if_missing=True)
        storage_path = get_calibration_storage_path(create_if_missing=True)
        
        # Fallback to the actual calibration storage location if ApplicationContext not set
        if storage_path is None:
            # Use the actual path where calibration data is stored
            fallback_storage_path = os.path.join(
                os.path.dirname(__file__), '..', '..', '..',
                'applications', 'glue_dispensing_application', 'storage', 'data', 'calibration'
            )
            storage_path = os.path.abspath(fallback_storage_path)
            print(f"VisionService: Warning - No application context set, using fallback calibration storage path: {storage_path}")
        if config_file_path is None:
            # Fallback to hardcoded path for backward compatibility
            config_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'system', 'storage',
                                            'settings', 'camera_settings.json')
            print("VisionService: Warning - No application context set, using fallback camera settings path")

        # Check if the settings file exists, create with defaults if missing
        if not os.path.exists(config_file_path):
            print(f"VisionService: Camera settings file not found at {config_file_path}")
            print("VisionService: Creating default camera settings...")
            if not self._create_default_camera_settings(config_file_path):
                raise RuntimeError(f"Failed to create default camera settings at {config_file_path}")

        super().__init__(configFilePath=config_file_path, storage_path=storage_path)

        self.MAX_QUEUE_SIZE = 100  # Maximum number of frames to store in the queue
        self.frameQueue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self.superRun = super().run
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.frame_id = 0  # Track unique frame updates
        self.contours = None
        self.workAreaCorners = None
        self.filteredContours = None

        broker = MessageBroker()
        broker.subscribe(VisionTopics.TRANSFORM_TO_CAMERA_POINT, self.transformRobotPointToCamera)

    @staticmethod
    def _get_default_camera_settings():
        """
        Returns the default camera settings configuration.

        Returns:
            dict: Default camera settings
        """
        return {
            "Index": 0,
            "Width": 1280,
            "Height": 720,
            "Skip frames": 30,
            "Capture position offset": 0,
            "Threshold": 100,
            "Threshold pickup area": 150,
            "Epsilon": 0.004,
            "Min contour area": 1000,
            "Max contour area": 10000000,
            "Contour detection": True,
            "Draw contours": False,
            "Preprocessing": {
                "Gaussian blur": True,
                "Blur kernel size": 5,
                "Threshold type": "binary_inv",
                "Dilate enabled": True,
                "Dilate kernel size": 3,
                "Dilate iterations": 2,
                "Erode enabled": True,
                "Erode kernel size": 3,
                "Erode iterations": 4
            },
            "Calibration": {
                "Chessboard width": 32,
                "Chessboard height": 20,
                "Square size (mm)": 25,
                "Skip frames": 30
            },
            "Brightness Control": {
                "Enable auto adjust": False,
                "Kp": 0.7,
                "Ki": 0.2,
                "Kd": 0.05,
                "Target brightness": 200
            },
            "Aruco": {
                "Enable detection": True,
                "Dictionary": "DICT_4X4_1000",
                "Flip image": False
            }
        }

    @staticmethod
    def _create_default_camera_settings(file_path):
        """
        Creates a camera settings file with default values.

        Args:
            file_path (str): Path where the settings file should be created

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Get default settings
            default_settings = _VisionService._get_default_camera_settings()

            # Write to file
            with open(file_path, 'w') as f:
                json.dump(default_settings, f, indent=2)

            print(f"VisionService: Created default camera settings at {file_path}")
            return True

        except Exception as e:
            print(f"VisionService: Error creating default camera settings: {e}")
            return False


    def run(self):
        """
              Main loop that continuously processes frames from the camera.

              It detects contours, applies overlays if necessary, and processes workpieces within the defined work area.

              This method keeps running indefinitely, so it should be called in a separate thread or process.

              Returns:
                  None
              """
        print("Starting VisionService run loop...")
        broker = MessageBroker()
        prev_time = time.time()  # store time of previous frame

        while True:
            # print(f"VisionService: Calling super().run() in thread {threading.current_thread().name}")
            self.contours, frame, _ = super().run()
            if frame is None:
                continue

            # Calculate FPS
            current_time = time.time()
            fps = 1.0 / (current_time - prev_time)
            prev_time = current_time
            # print(f"[VisionService] FPS -> {fps:.2f}")
            with self.frame_lock:
                self.latest_frame = frame
                broker.publish(VisionTopics.LATEST_IMAGE, frame)
                broker.publish(VisionTopics.FPS, fps)
                # print(f"[VisionService] Published latest frame and FPS: {fps:.2f}")
                self.frame_id += 1  # Increment frame ID on new frame

    def getLatestFrame(self):
        """
            Retrieves the latest frame from the queue.

            Returns:
                numpy.ndarray or None: The most recent frame, or None if the queue is empty.
            """

        with self.frame_lock:
            if self.latest_frame is None:
                return None
        # convert to RGB before returning
        return self.latest_frame
        # return cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)

    def getContours(self):
        """
               Returns the detected contours from the most recent frame.

               Returns:
                   list: A list of contours detected in the most recent frame.
               """
        return self.contours

    def updateCameraSettings(self, settings: dict):
        """
             Updates the camera settings with the provided dictionary of settings.

             Args:
                 settings (dict): The new camera settings to apply.

             Returns:
                 bool: True if the settings were updated successfully, otherwise False.
             """
        return self.updateSettings(settings)

    def getFrameWidth(self):
        """
              Returns the width of the captured frame.

              Returns:
                  int: The width of the frame.
              """
        return self.frameHeight

    def getFrameHeight(self):
        """
               Returns the height of the captured frame.

               Returns:
                   int: The height of the frame.
               """
        return self.frameWidth

    def getCameraToRobotMatrix(self):
        """
              Returns the camera-to-robot transformation matrix.

              Returns:
                  numpy.ndarray or None: The matrix if successfully loaded, otherwise None.
              """
        return self.cameraToRobotMatrix

    def calibrateCamera(self):
        """
               Initiates the camera calibration process.

               Returns:
                   bool: Calibration result indicating success or failure.
               """
        result = super().calibrateCamera()
        print("Calibration result: ", result)
        return result

    def calibrate(self):
        """
        Backwards-compatible adapter: call calibrateCamera.
        Some controllers expect a `calibrate()` method on the service — forward to the implemented method.
        """
        return self.calibrateCamera()

    def setRawMode(self, rawMode: bool):
        """
                Sets the camera's raw mode, enabling or disabling it.

                Args:
                    rawMode (bool): True to enable raw mode, False to disable.
                """
        print("Setting raw mode to: ", rawMode)
        self.rawMode = rawMode

    def detectArucoMarkers(self, flip=False, image=None):
        """
              Detects ArUco markers in the provided image.

              Args:
                  flip (bool): If True, the image will be flipped before processing.
                  image (numpy.ndarray): The image in which to detect ArUco markers.

              Returns:
                  tuple: The detected ArUco marker corners, ids, and the processed image.
              """
        return super().detectArucoMarkers(flip, image)

    def captureImage(self):
        """
              Captures an image from the camera.

              Returns:
                  numpy.ndarray: The captured image.
              """
        image = super().captureImage()
        return image

    def detectQrCode(self):
        return super().detectQrCode()

    def stopContourDetection(self):
        self.contourDetection = False

    def startContourDetection(self):
        self.contourDetection = True

    def captureFrameThreadSafe(self):
        """
        Thread-safe method to capture a single frame using the camera lock.
        This prevents conflicts when multiple threads try to access camera frames.
        
        Returns:
            tuple: (contours, frame, filtered_contours) - same as superRun() but thread-safe
        """
        with self.frame_lock:
            print(f"Calling superRun() in thread {threading.current_thread().name}")
            return self.superRun()



    def transformRobotPointToCamera(self, message):
        # message format {"x": x, "y": y}
        x = message.get("x")
        y = message.get("y")
        point = (x, y)
        return utils.transformSinglePointToCamera(point, self.cameraToRobotMatrix)


class VisionServiceSingleton:
    """
        A Singleton class to manage a single instance of VisionService.

        This class ensures that only one instance of the VisionService is created and accessed globally.
        The `get_instance` method returns the same instance every time it is called.

        Methods:
            get_instance():
                Returns the single instance of the VisionService.
        """
    _visionServiceInstance = None  # Static variable to hold the instance

    @staticmethod
    def get_instance() -> _VisionService:
        """
               Returns the singleton instance of the VisionService.

               If the instance has not been created yet, it initializes the _VisionService class.

               Returns:
                   VisionService: The singleton instance of the VisionService.
               """
        if VisionServiceSingleton._visionServiceInstance is None:
            VisionServiceSingleton._visionServiceInstance = _VisionService()
        return VisionServiceSingleton._visionServiceInstance


if __name__ == "__main__":
    # Test Vision Service performance without UI interference
    import cv2
    import threading
    import psutil

    print("=== VisionService Performance Test ===")
    print("This will test camera performance without the UI to isolate performance issues.")
    print("Press 'q' to quit, 'r' to toggle raw mode, 'c' to toggle contour detection")
    
    vision_service = VisionServiceSingleton.get_instance()
    print(f"Vision service instantiated: {vision_service}")
    print(f"System calibrated: {vision_service.isSystemCalibrated}")
    print(f"Camera settings: {vision_service.camera_settings.get_camera_width()}x{vision_service.camera_settings.get_camera_height()}")
    
    # Set CPU affinity for better performance
    try:
        p = psutil.Process()
        available_cores = list(range(psutil.cpu_count()))
        if len(available_cores) >= 2:
            p.cpu_affinity(available_cores[:2])
            print(f"Process bound to CPU cores: {available_cores[:2]}")
    except Exception as e:
        print(f"Could not set CPU affinity: {e}")

    # Start vision processing in daemon thread
    vision_thread = threading.Thread(target=vision_service.run, daemon=True)
    vision_thread.start()
    print("Vision thread started...")

    # Display loop
    frame_count = 0
    start_time = time.time()
    last_fps_time = time.time()
    last_frame_id = 0
    display_fps = 0.0
    avg_fps = 0.0
    last_image = None
    
    while True:
        image = vision_service.getLatestFrame()
        
        # Check if we got a new frame by comparing frame IDs
        with vision_service.frame_lock:
            current_frame_id = vision_service.frame_id
        
        if image is not None:
            # Only update FPS if we have a new frame
            if current_frame_id > last_frame_id:
                frame_count += 1
                last_frame_id = current_frame_id
                
                # Calculate instantaneous FPS only for new frames
                current_time = time.time()
                if current_time > last_fps_time:
                    display_fps = 1.0 / (current_time - last_fps_time)
                last_fps_time = current_time
                
                # Calculate average FPS every 30 frames
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    avg_fps = 30 / elapsed
                    print(f"[UI Thread] New Frame FPS over last 30 frames: {avg_fps:.2f}")
                    start_time = time.time()
                
                last_image = image
            
            # Use the latest image for display (new or repeated)
            display_image_source = last_image if last_image is not None else image
            
            # Convert back to BGR for OpenCV display
            display_image = cv2.cvtColor(display_image_source, cv2.COLOR_RGB2BGR)
            
            # Add FPS and status overlays - show processing thread FPS as "Vision FPS"
            cv2.putText(display_image, f"Vision FPS: {display_fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(display_image, f"Avg FPS: {avg_fps:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(display_image, f"Frame: {frame_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_image, f"Raw Mode: {vision_service.rawMode}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(display_image, f"Contour Detection: {vision_service.camera_settings.get_contour_detection()}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(display_image, f"Brightness Auto: {vision_service.camera_settings.get_brightness_auto()}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            cv2.imshow("VisionService Performance Test", display_image)
            
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Exiting...")
            break
        elif key == ord('r'):
            vision_service.rawMode = not vision_service.rawMode
            print(f"Raw mode toggled: {vision_service.rawMode}")
        elif key == ord('c'):
            current = vision_service.camera_settings.get_contour_detection()
            vision_service.camera_settings.set_contour_detection(not current)
            print(f"Contour detection toggled: {not current}")
        elif key == ord('b'):
            current = vision_service.camera_settings.get_brightness_auto()
            vision_service.camera_settings.set_brightness_auto(not current)
            print(f"Brightness auto adjustment toggled: {not current}")
    
    cv2.destroyAllWindows()
    print("Performance test completed.")
