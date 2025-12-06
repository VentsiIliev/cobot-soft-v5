import re

from communication_layer.api.v1 import Constants
from communication_layer.api.v1.Response import Response
from communication_layer.api.v1.endpoints import auth_endpoints, camera_endpoints
from core.controllers.BaseController import BaseController


class CameraSystemController(BaseController):
    """
    Handles all camera-related operations using the endpoint registry
    provided by BaseCameraSystemController.
    """

    def __init__(self, cameraService):
        self.cameraService = cameraService
        super().__init__()
        self._initialize_handlers()

    # ============================================================
    # REGISTER ENDPOINT HANDLERS
    # ============================================================
    def _initialize_handlers(self):
        # FRAME OPERATIONS
        self.register_handler(camera_endpoints.CAMERA_ACTION_GET_LATEST_FRAME, self.handleLatestFrame)
        self.register_handler(camera_endpoints.UPDATE_CAMERA_FEED, self.handleLatestFrame)
        self.register_handler(camera_endpoints.GET_LATEST_IMAGE, self.handleLatestFrame)

        # RAW MODE
        self.register_handler(camera_endpoints.CAMERA_ACTION_RAW_MODE_ON, self.handleRawModeOn)
        self.register_handler(camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF, self.handleRawModeOff)

        # CALIBRATION
        self.register_handler(camera_endpoints.CAMERA_ACTION_CALIBRATE, self.cameraService.calibrate)
        self.register_handler(camera_endpoints.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE, self.captureCalibrationImage)
        self.register_handler(camera_endpoints.CAMERA_ACTION_TEST_CALIBRATION, self.cameraService.testCalibration)

        # WORK AREA (needs request data)
        self.register_handler(
            camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS,
            lambda data: self.saveWorkAreaPoints(data)
        )
        self.register_handler(
            camera_endpoints.CAMERA_ACTION_GET_WORK_AREA_POINTS,
            lambda data: self.getWorkAreaPoints(data)
        )

        # CONTOUR DETECTION
        self.register_handler(camera_endpoints.START_CONTOUR_DETECTION, self.startContourDetection)
        self.register_handler(camera_endpoints.STOP_CONTOUR_DETECTION, self.stopContourDetection)

        # LOGIN
        self.register_handler(auth_endpoints.QR_LOGIN, self.handleLogin)


    # === INDIVIDUAL OPERATION HANDLERS ===

    def handleLatestFrame(self):
        try:
            frame = self.cameraService.getLatestFrame()
            message = "Frame retrieved" if frame is not None else "Frame is None"
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS,
                message=message,
                data={"frame": frame},
            ).to_dict()
        except Exception as e:
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error getting latest frame: {e}",
            ).to_dict()

    def handleRawModeOn(self):
        self.cameraService.setRawMode(True)
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Raw mode enabled").to_dict()

    def handleRawModeOff(self):
        self.cameraService.setRawMode(False)
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Raw mode disabled").to_dict()

    def captureCalibrationImage(self):
        result, message = self.cameraService.captureCalibrationImage()
        status = (
            Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        )
        return Response(status, message=message).to_dict()

    def saveWorkAreaPoints(self, points):
        print("[CameraSystemController] Saving work area points:", points)
        result, message = self.cameraService.saveWorkAreaPoints(points)
        status = (
            Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        )
        return Response(status, message=message).to_dict()
    
    def getWorkAreaPoints(self, data):
        """Get work area points for a specific area type"""
        area_type = data.get('area_type') if data else None
        print(f"[CameraSystemController] Getting work area points for area: {area_type}")
        
        try:
            result, message, points = self.cameraService.getWorkAreaPoints(area_type)
            print(f"[CameraSystemController] VisionService returned: result={result}, message='{message}', points={points}")
            status = (
                Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
            )
            
            response = Response(status, message=message, data=points).to_dict()
            print(f"[CameraSystemController] Returning response: {response}")
            return response
        except Exception as e:
            print(f"[CameraSystemController] Error getting work area points: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error getting work area points: {e}"
            ).to_dict()

    def handleLogin(self):
        data = self.cameraService.detectQrCode()
        if data is None:
            return Response(Constants.RESPONSE_STATUS_ERROR, "No QR code detected").to_dict()

        pattern = r"id\s*=\s*(\S+)\s+password\s*=\s*(\S+)"
        match = re.search(pattern, data)
        if match:
            data = {"id": match.group(1), "password": match.group(2)}
            return Response(Constants.RESPONSE_STATUS_SUCCESS, data=data).to_dict()
        else:
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                "Invalid QR code format",
            ).to_dict()

    def startContourDetection(self):
        self.cameraService.startContourDetection()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Contour detection started").to_dict()

    def stopContourDetection(self):
        self.cameraService.stopContourDetection()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Contour detection stopped").to_dict()
