from PyQt6.QtCore import QThread
from applications.glue_dispensing_application.model.workpiece.GlueWorkpiece import GlueWorkpiece
from core.model.settings.CameraSettings import CameraSettings
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from communication_layer.api.v1 import Constants
from communication_layer.api.v1.Response import Response
from communication_layer.api.v1.endpoints import camera_endpoints, robot_endpoints, workpiece_endpoints, \
    settings_endpoints, auth_endpoints, operations_endpoints, glue_endpoints
from core.model.settings.robotConfig.robotConfigModel import RobotConfig
from frontend.legacy_ui.controller.RequestWorker import RequestWorker
from frontend.feedback.FeedbackProvider import FeedbackProvider
import logging
import json

from plugins.core.settings.ui.camera_settings_tab.CameraSettingsTabLayout import CameraSettingsTabLayout
from plugins.core.glue_settings_plugin.ui.GlueSettingsTabLayout import GlueSettingsTabLayout
from plugins.core.settings.ui.robot_settings_tab.RobotConfigUI import RobotConfigUI


class UIController:
    def __init__(self, requestSender):
        self.logTag = self.__class__.__name__
        self.logger = logging.getLogger(self.__class__.__name__)
        self.requestSender = requestSender
        self.endpointsMap = {}
        self.registerEndpoints()

    def registerEndpoints(self):
        self.endpointsMap = {
            # Settings endpoints
            settings_endpoints.SETTINGS_UPDATE: self.updateSettings,
            settings_endpoints.SETTINGS_GET: self.handleGetSettings,
            settings_endpoints.SETTINGS_ROBOT_CALIBRATION_SET: self.handle_update_robot_calibration_settings,
            settings_endpoints.SETTINGS_ROBOT_CALIBRATION_GET: self.handle_get_robot_calibration_settings,
            
            # Glue types endpoints
            glue_endpoints.GLUE_TYPES_GET: self.handleGetGlueTypes,
            glue_endpoints.GLUE_TYPE_ADD_CUSTOM: self.handleAddGlueType,
            glue_endpoints.GLUE_TYPES_SET: self.handleUpdateGlueType,
            glue_endpoints.GLUE_TYPE_REMOVE_CUSTOM: self.handleRemoveGlueType,

            # Authentication endpoints
            auth_endpoints.LOGIN: self.handleLogin,
            auth_endpoints.QR_LOGIN: self.handleQrLogin,
            
            # Operations endpoints
            operations_endpoints.START: self.handleStart,
            operations_endpoints.PAUSE: self.handlePause,
            operations_endpoints.STOP: self.handleStop,
            operations_endpoints.TEST_RUN: self.handleTestRun,
            operations_endpoints.CALIBRATE: self.handleCalibrate,
            operations_endpoints.HELP: self.handleHelp,
            operations_endpoints.RUN_DEMO: self.handleRunDemo,
            operations_endpoints.STOP_DEMO: self.handleStopDemo,

            # Camera endpoints
            camera_endpoints.CAMERA_ACTION_CALIBRATE: self.handleCalibrateCamera,
            camera_endpoints.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE: self.handleCaptureCalibrationImage,
            camera_endpoints.CAMERA_ACTION_TEST_CALIBRATION: self.handleTestCalibration,
            camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS: self.handleSaveWorkAreaPoints,
            camera_endpoints.UPDATE_CAMERA_FEED: self.updateCameraFeed,
            camera_endpoints.START_CONTOUR_DETECTION: self.handleStartContourDetection,
            camera_endpoints.STOP_CONTOUR_DETECTION: self.handleStopContourDetection,
            camera_endpoints.CAMERA_ACTION_RAW_MODE_ON: self.handleRawModeOn,
            camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF: self.handleRawModeOff,

            # Robot endpoints
            robot_endpoints.ROBOT_CALIBRATE: self.handleCalibrateRobot,
            robot_endpoints.ROBOT_MOVE_TO_HOME_POS: self.homeRobot,
            robot_endpoints.ROBOT_MOVE_TO_CALIB_POS: self.handleMoveToCalibrationPos,
            robot_endpoints.ROBOT_MOVE_TO_LOGIN_POS: self.handleLoginPos,
            robot_endpoints.ROBOT_SAVE_POINT: self.saveRobotCalibrationPoint,
            robot_endpoints.ROBOT_EXECUTE_NOZZLE_CLEAN: self.handleCleanNozzle,
            robot_endpoints.ROBOT_RESET_ERRORS: self.handleResetErrors,
            robot_endpoints.ROBOT_UPDATE_CONFIG: self.handleRobotUpdateConfig,
            robot_endpoints.ROBOT_GET_CURRENT_POSITION: self.handle_get_robot_current_position,
            robot_endpoints.ROBOT_MOVE_TO_POSITION: self.handle_move_robot_to_position,
            robot_endpoints.ROBOT_SLOT_0_PICKUP: self.handle_pickup_gripper_0,
            robot_endpoints.ROBOT_SLOT_0_DROP: self.handle_drop_gripper_0,
            robot_endpoints.ROBOT_SLOT_1_DROP: self.handle_drop_gripper_1,
            robot_endpoints.ROBOT_SLOT_1_PICKUP: self.handle_pickup_gripper_1,
            robot_endpoints.ROBOT_SLOT_2_DROP : self.handle_drop_gripper_2,
            robot_endpoints.ROBOT_SLOT_2_PICKUP : self.handle_pickup_gripper_2,
            robot_endpoints.ROBOT_SLOT_3_DROP : self.handle_drop_gripper_3,
            robot_endpoints.ROBOT_SLOT_3_PICKUP : self.handle_pickup_gripper_3,
            robot_endpoints.ROBOT_SLOT_4_DROP : self.handle_drop_gripper_4,
            robot_endpoints.ROBOT_SLOT_4_PICKUP : self.handle_pickup_gripper_4,


            # Workpiece endpoints
            workpiece_endpoints.WORKPIECE_SAVE: self.save_workpiece,
            workpiece_endpoints.WORKPIECE_SAVE_DXF: self.saveWorkpieceFromDXF,
            operations_endpoints.CREATE_WORKPIECE: self.handle_create_workpiece,
            workpiece_endpoints.WORKPIECE_GET_ALL: self.handleGetAllWorpieces,

            # Legacy special endpoints
            "executeFromGallery": self.handleExecuteFromGallery,
        }

    def handle_drop_gripper_4(self):
        request = robot_endpoints.ROBOT_SLOT_4_DROP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_drop_gripper_4] Response: {response}")

    def handle_pickup_gripper_4(self):
        request = robot_endpoints.ROBOT_SLOT_4_PICKUP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_pickup_gripper_4] Response: {response}")

    def handle_pickup_gripper_3(self):
        request = robot_endpoints.ROBOT_SLOT_3_PICKUP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_pickup_gripper_3] Response: {response}")

    def handle_drop_gripper_3(self):
        request = robot_endpoints.ROBOT_SLOT_3_DROP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_drop_gripper_3] Response: {response}")

    def handle_pickup_gripper_2(self):
        request = robot_endpoints.ROBOT_SLOT_2_PICKUP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_pickup_gripper_2] Response: {response}")

    def handle_drop_gripper_2(self):
        request = robot_endpoints.ROBOT_SLOT_2_DROP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_drop_gripper_2] Response: {response}")

    def handle_pickup_gripper_1(self):
        request = robot_endpoints.ROBOT_SLOT_1_PICKUP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_pickup_gripper_1] Response: {response}")

    def handle_drop_gripper_1(self):
        request = robot_endpoints.ROBOT_SLOT_1_DROP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_drop_gripper_1] Response: {response}")

    def handle_pickup_gripper_0(self):
        request = robot_endpoints.ROBOT_SLOT_0_PICKUP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_pickup_gripper_0] Response: {response}")

    def handle_drop_gripper_0(self):
        request = robot_endpoints.ROBOT_SLOT_0_DROP
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_drop_gripper_0] Response: {response}")

    def handle_move_robot_to_position(self, position, vel, acc):
        print("RAW position:", position, type(position))

        # STEP 1: If position is a string, parse it as JSON
        if isinstance(position, str):
            try:
                position = json.loads(position)
            except Exception:
                print("ERROR: position string could not be parsed:", position)
                return False

        # STEP 2: Ensure each element is a float
        try:
            print("Position before float conversion:", position, "types:", [type(x) for x in position])
            position = [float(p) for p in position]
        except Exception as e:
            print("Error converting position to floats:", position, "type:", [type(x) for x in position])
            print(e)
            return False

        # STEP 3: Convert vel/acc
        try:
            vel = float(vel)
            acc = float(acc)
        except Exception:
            print("Error converting velocity/acceleration:", vel, acc)
            return False

        # Endpoint
        request = robot_endpoints.ROBOT_MOVE_TO_POSITION

        data = {
            "position": position,
            "velocity": vel,
            "acceleration": acc
        }

        # Send request
        response_dict = self.requestSender.send_request(request, data)
        response = Response.from_dict(response_dict)
        print(f"[handle_move_to_position] Response: {response}")

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error moving robot to position:", response.message)
            return False

        return True

    def handle_get_robot_current_position(self):
        request = robot_endpoints.ROBOT_GET_CURRENT_POSITION
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_get_robot_current_position] Response: {response}")
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error fetching robot current position:", response.message)
            return None

        return response.data.get("position")

    def handle_get_robot_calibration_settings(self):
        request = settings_endpoints.SETTINGS_ROBOT_CALIBRATION_GET
        response_dict = self.requestSender.send_request(request)
        response = Response.from_dict(response_dict)
        print(f"[handle_get_robot_calibration_settings] Response: {response}")
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error fetching robot calibration settings:", response.message)
            return None

        return response.data

    def handle_update_robot_calibration_settings(self, key, value):
        request = settings_endpoints.SETTINGS_ROBOT_CALIBRATION_SET
        data = {key: value}
        response_dict = self.requestSender.send_request(request, data)
        response = Response.from_dict(response_dict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error updating robot calibration settings:", response.message)
            return False

        return True

    def handleRobotUpdateConfig(self):
        request = robot_endpoints.ROBOT_UPDATE_CONFIG
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error updating robot config:", response.message)

        return response.status

    def handleRunDemo(self):
        request = operations_endpoints.RUN_DEMO
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error starting demo:", response.message)

        return response.status

    def handleStopDemo(self):
        request = operations_endpoints.STOP_DEMO
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error stopping demo:", response.message)

        return response.status

    def handleResetErrors(self):
        request = robot_endpoints.ROBOT_RESET_ERRORS
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error resetting errors:", response.message)

        return response.status

    def handleCleanNozzle(self):
        print(f"UI Controller handle clean nozzle")
        request = robot_endpoints.ROBOT_EXECUTE_NOZZLE_CLEAN
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error cleaning nozzle:", response.message)

        return response.status

    def handleRawModeOn(self):
        print("Enabling raw mode")
        request = camera_endpoints.CAMERA_ACTION_RAW_MODE_ON
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error enabling raw mode:", response.message)

        return response.status

    def handleRawModeOff(self):
        request = camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error disabling raw mode:", response.message)

        return response.status

    def handleSetPreselectedWorkpiece(self, workpiece):
        self.requestSender.send_request("handleSetPreselectedWorkpiece", workpiece)

    def handleTestRun(self):
        self.requestSender.send_request("test_run")

    def handle(self, endpoint, *args, **kwargs):
        if endpoint in self.endpointsMap:
            try:
                # print(f"{self.logTag} Handling endpoint: '{endpoint}' with args: {args}")
                return self.endpointsMap[endpoint](*args)
            except TypeError as e:
                self.logger.debug(f"{self.logTag} [Method: handle] Parameter mismatch for endpoint '{endpoint}': {e}")
        else:
            self.logger.debug(f"{self.logTag}] [Method: handle] Unknown endpoint: '{endpoint}'")
            return None

    def handlePause(self):
        request = operations_endpoints.PAUSE
        response = self.requestSender.send_request(request)

    def handleStop(self):
        request = operations_endpoints.STOP
        response = self.requestSender.send_request(request)

    def handleStartContourDetection(self):
        requests = camera_endpoints.START_CONTOUR_DETECTION
        self.requestSender.send_request(requests)

    def handleStopContourDetection(self):
        request = camera_endpoints.STOP_CONTOUR_DETECTION
        self.requestSender.send_request(request)

    def handleGetAllWorpieces(self):
        request = workpiece_endpoints.WORKPIECE_GET_ALL
        res = self.requestSender.send_request(request)
        response = Response.from_dict(res)
        workpieces = response.data
        print(f"Received workpieces: {workpieces}")
        return workpieces

    def handleHelp(self):
        self.logger.debug(f"{self.logTag}] [Method: handleHelp] HELP BUTTON PRESSED'")

    def handleGetSettings(self):
        robotSettingsRequest = settings_endpoints.SETTINGS_ROBOT_GET
        cameraSettingsRequest = settings_endpoints.SETTINGS_CAMERA_GET

        robotSettingsResponseDict = self.requestSender.send_request(robotSettingsRequest)
        robotSettingsResponse = Response.from_dict(robotSettingsResponseDict)

        cameraSettingsResponseDict = self.requestSender.send_request(cameraSettingsRequest)
        cameraSettingsResponse = Response.from_dict(cameraSettingsResponseDict)
        print(" get Camera settings response:", cameraSettingsResponse)

        robotSettingsDict = robotSettingsResponse.data if robotSettingsResponse.status == Constants.RESPONSE_STATUS_SUCCESS else {}
        robot_config = RobotConfig.from_dict(robotSettingsDict)
        cameraSettingsDict = cameraSettingsResponse.data if cameraSettingsResponse.status == Constants.RESPONSE_STATUS_SUCCESS else {}

        cameraSettings = CameraSettings(data=cameraSettingsDict)
        print(f"[UIController] Loaded robot settings: {robotSettingsDict}")
        
        # Only load glue settings if the current application supports them
        from core.application.ApplicationContext import get_application_settings_tabs
        needed_tabs = get_application_settings_tabs()
        
        if "glue" in needed_tabs:
            glueSettingsRequest = glue_endpoints.SETTINGS_GLUE_GET
            glueSettingsResponseDict = self.requestSender.send_request(glueSettingsRequest)
            glueSettingsResponse = Response.from_dict(glueSettingsResponseDict)
            glueSettingsDict = glueSettingsResponse.data if glueSettingsResponse.status == Constants.RESPONSE_STATUS_SUCCESS else {}
            glueSettings = GlueSettings(data=glueSettingsDict)
        else:
            glueSettings = None  # Default settings for non-glue applications

        return cameraSettings, glueSettings,robot_config

    def saveWorkpieceFromDXF(self, data):

        request = workpiece_endpoints.WORKPIECE_SAVE_DXF
        responseDict = self.requestSender.send_request(request, data)
        response = Response.from_dict(responseDict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            message = "Error saving workpieces"
            return False, response.message

        return True, response.message

    def save_workpiece(self, data):
        request = workpiece_endpoints.WORKPIECE_SAVE
        responseDict = self.requestSender.send_request(request, data)
        response = Response.from_dict(responseDict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            message = "Error saving workpieces"
            return False, response.message

        return True, response.message

    def handleSaveWorkAreaPoints(self, points):
        print("handleSaveWorkAreaPoints Saving work area points:", points)
        request = camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS
        self.requestSender.send_request(request, data=points)
    
    def handleGetWorkAreaPoints(self, area_type):
        print(f"handleGetWorkAreaPoints Getting work area points for area: {area_type}")
        request = camera_endpoints.CAMERA_ACTION_GET_WORK_AREA_POINTS
        response = self.requestSender.send_request(request, data={'area_type': area_type})
        print(f"[UIController] handleGetWorkAreaPoints received response: {response}")
        print(f"[UIController] response type: {type(response)}")
        
        # Handle both object and dictionary responses
        if response:
            if hasattr(response, 'data'):
                # Response object format
                print(f"[UIController] Using object format, response.data: {response.data}")
                return response.data
            elif isinstance(response, dict) and 'data' in response:
                # Dictionary format - check for double wrapping
                data = response['data']
                if isinstance(data, dict) and 'data' in data:
                    # Double wrapped - get the actual data
                    actual_data = data['data']
                    print(f"[UIController] Found double-wrapped data: {actual_data}")
                    return actual_data
                else:
                    # Single wrapped
                    print(f"[UIController] Using dictionary format, data: {data}")
                    return data
            else:
                print(f"[UIController] Response has no data field")
                return None
        else:
            print(f"[UIController] No response received, returning None")
            return None

    def handleTestCalibration(self):
        request = camera_endpoints.CAMERA_ACTION_TEST_CALIBRATION
        self.requestSender.send_request(request)

    def handleCalibrateRobot(self):
        request = robot_endpoints.ROBOT_CALIBRATE
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        print("Robot calibration response:", response)
        self.logger.debug(f"{self.logTag}] Calibrate robot response: {response}")
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            request = camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF
            response = self.requestSender.send_request(request)
            response = Response.from_dict(response)
            FeedbackProvider.showMessage(response.message)
            return False, response.message

        return True, response.message

    def handleCalibrateCamera(self):
        """ MOVE ROBOT TO CALIBRATION POSITION"""
        print("Calibrating camera")
        request = robot_endpoints.ROBOT_MOVE_TO_CALIB_POS
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        if response.status != Constants.RESPONSE_STATUS_SUCCESS:
            self.logger.debug(f"{self.logTag}] [Method: handleCalibrate] Error moving to calib pos")

        request = camera_endpoints.CAMERA_ACTION_RAW_MODE_ON
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)

        FeedbackProvider.showPlaceCalibrationPattern()

        request = camera_endpoints.CAMERA_ACTION_CALIBRATE
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            request = camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF
            response = self.requestSender.send_request(request)
            response = Response.from_dict(response)
            return False, response.message

        FeedbackProvider.showMessage("Camera Calibration Success\nMove the chessboard")

        # Always return a tuple for consistency
        return True, response.message if hasattr(response, 'message') else "Camera calibration completed successfully"

    def handleCaptureCalibrationImage(self):
        request = camera_endpoints.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            FeedbackProvider.showMessage(response.message)
            return False, response.message

        # FeedbackProvider.showMessage("Calibration image captured successfully")
        return True, "Calibration image captured successfully"

    def handleCalibrate(self):

        self.handleCalibrateCamera()
        self.handleCalibrateRobot()

        # SEND ROBOT CALIBRATION REQUEST

        request = robot_endpoints.ROBOT_CALIBRATE
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        print("Robot calibration response:", response)
        self.logger.debug(f"{self.logTag}] Calibrate robot response: {response}")
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            request = camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF
            response = self.requestSender.send_request(request)
            response = Response.from_dict(response)
            FeedbackProvider.showMessage(response.message)
            return False, response.message

        return True, response.message

    def saveRobotCalibrationPoint(self):
        request = robot_endpoints.ROBOT_SAVE_POINT
        responseDict = self.requestSender.send_request(request)
        response = Response.from_dict(responseDict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            return False, False

        pointsCount = response.data.get("pointsCount", 0)  # Default to 0 if key is missing

        if pointsCount == 9:
            return True, True
        else:
            return True, False


    def is_blue_button_pressed(self):
        return True

    def handleQrLogin(self):
        request = auth_endpoints.QR_LOGIN
        response = self.requestSender.send_request(request)
        # response = Response.from_dict(response)
        return response

    def handleLogin(self, username, password):
        request = auth_endpoints.LOGIN
        response_dict = self.requestSender.send_request(request, data=[username, password])
        response = Response.from_dict(response_dict)
        print("Response: ", response)

        message = response.message

        return message

    def updateSettings(self, key, value, className):
        if className == CameraSettingsTabLayout.__module__:
            print("Updating Settings Camera", key, value)
            resource = Constants.REQUEST_RESOURCE_CAMERA
            request = settings_endpoints.SETTINGS_CAMERA_SET

        elif className == GlueSettingsTabLayout.__module__:
            print("Updating Settings Glue", key, value)
            resource = glue_endpoints.REQUEST_RESOURCE_GLUE
            request = glue_endpoints.SETTINGS_GLUE_SET

        elif className == RobotConfigUI.__module__:
            # Check if this is a robot calibration setting
            if self._is_robot_calibration_setting(key):
                print(f"🔧 Setting change signal received: {className}.{key} = {value}")
                print("Routing to robot calibration settings handler")
                return self.handle_update_robot_calibration_settings(key, value)
            else:
                print("Updating Settings Robot", key, value)
                resource = Constants.REQUEST_RESOURCE_ROBOT
                request = settings_endpoints.SETTINGS_ROBOT_SET
        else:
            self.logger.error(f"{self.logTag}] Updating Unknown Settings {className} : {key} {value}")
            return

        data = {"header": resource,
                key: value}

        self.requestSender.send_request(request, data)
    
    def _is_robot_calibration_setting(self, key):
        """Check if the setting key belongs to robot calibration settings"""
        try:
            # Import robot calibration setting keys for detection
            from plugins.core.settings.enums.RobotCalibrationSettingKeys import RobotCalibrationSettingKeys
            # Check if the key is a valid robot calibration setting
            calibration_keys = [setting.value for setting in RobotCalibrationSettingKeys]
            return key in calibration_keys
        except Exception as e:
            print(f"Error checking robot calibration setting key: {e}")
            return False

    """ REFACTORED METHODS BELOW """

    def updateCameraFeed(self):
        # print("Controller.updateCameraFeed: Requesting latest camera frame")
        request = camera_endpoints.CAMERA_ACTION_GET_LATEST_FRAME
        responseDict = self.requestSender.send_request(request)
        response = Response.from_dict(responseDict)
        # print("Update camera feed response, ",response)
        if response.status != Constants.RESPONSE_STATUS_SUCCESS:
            print(f"Image in updateCameraFeed not received: {response.message}")
            return
        frame = response.data['frame']
        # print(f"Returning image in updateCameraFeed")
        return frame

    def handleJog(self, axis, direction, step):
        request = f"robot/jog/{axis}/{direction}/{step}"

        def onSuccess(req, resp):
            if resp.status == Constants.RESPONSE_STATUS_ERROR:
                FeedbackProvider.showMessage(resp.message)
            else:
                pass

        def onError(req, err):
            self.logger.error(f"{self.logTag}] CALLBACK ERROR MESSAGE {err}")

        self._runAsyncRequest(request, onSuccess, onError)

    def handleLoginPos(self):
        request = robot_endpoints.ROBOT_MOVE_TO_LOGIN_POS
        response = self.requestSender.send_request(request)
        response = Response.from_dict(response)
        return response.status

    def handleMoveToCalibrationPos(self):
        request = robot_endpoints.ROBOT_MOVE_TO_CALIB_POS
        self.requestSender.send_request(request)

    def homeRobot(self):
        request = robot_endpoints.ROBOT_MOVE_TO_HOME_POS


        resp = self.requestSender.send_request(request)
        resp = Response.from_dict(resp)
        if resp.status == Constants.RESPONSE_STATUS_ERROR:
            FeedbackProvider.showMessage(resp.message)
            return Constants.RESPONSE_STATUS_ERROR
        else:
            return Constants.RESPONSE_STATUS_SUCCESS

    def handleStart(self):
        request = operations_endpoints.START
        def onSuccess(req, resp):
            if resp.status == Constants.RESPONSE_STATUS_ERROR:
                FeedbackProvider.showMessage(resp.message)
            else:
                pass

        def onError(req, err):
            self.logger.error(f"{self.logTag}] CALLBACK ERROR MESSAGE {err}")

        self._runAsyncRequest(request, onSuccess, onError)

    def get_workpiece_by_id(self, workpieceId):
        request = workpiece_endpoints.WORKPIECE_GET_BY_ID
        data = {"workpieceId": workpieceId}
        responseDict = self.requestSender.send_request(request, data)
        response = Response.from_dict(responseDict)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error fetching workpiece:", response.message)
            return False, response.message
        
        # Convert the response data to a Workpiece object
        try:
            if isinstance(response.data, dict):
                workpiece = GlueWorkpiece.from_dict(response.data)
                return True, workpiece
            else:
                # response.data is already a Workpiece object
                return True, response.data
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error converting response data to Workpiece: {e}")
            return False, f"Error converting response data: {e}"

    def handleDeleteWorkpiece(self,workpieceId):
        request = workpiece_endpoints.WORKPIECE_DELETE
        data = {"workpieceId": workpieceId}
        responseDict = self.requestSender.send_request(request, data)
        response = Response.from_dict(responseDict)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error deleting workpiece:", response.message)
            return False, response.message
        return True, response.message

    def handle_create_workpiece(self,data=None):
        request = operations_endpoints.CREATE_WORKPIECE
        responseDict = self.requestSender.send_request(request,data)
        response = Response.from_dict(responseDict)
        has_data= response.data is not None
        print(f"Received create workpiece response: {response.status}, message {response.message} has_data: {has_data}")
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error in CreateWorkpieceStep1:", response.message)
            return False, response.message,response.data
        return True, response.message,response.data

    def _runAsyncRequest(self, request, onSuccess, onError=None):
        thread = QThread()
        worker = RequestWorker(self.requestSender, request)
        worker.moveToThread(thread)

        def cleanup():
            thread.quit()
            thread.wait()
            worker.deleteLater()
            thread.deleteLater()

        def handleFinished(req, resp):
            cleanup()
            if onSuccess:
                onSuccess(req, resp)

        def handleError(req, error):
            cleanup()
            if onError:
                self.logger.error(f"{self.logTag}] [_runAsyncRequest onError] {req} {error}")
                onError(req, error)


        thread.started.connect(worker.run)
        worker.finished.connect(handleFinished)
        worker.error.connect(handleError)
        thread.start()


    def handleExecuteFromGallery(self, workpiece):
        self.requestSender.send_request("handleExecuteFromGallery", workpiece)

    # Glue Types Management Methods
    def handleGetGlueTypes(self):
        """Get all glue types"""
        request = glue_endpoints.GLUE_TYPES_GET
        response_dict = self.requestSender.send_request(request, {})
        return response_dict

    def handleAddGlueType(self, name, description=""):
        """Add new glue type"""
        request = glue_endpoints.GLUE_TYPE_ADD_CUSTOM
        data = {
            "header": glue_endpoints.REQUEST_RESOURCE_GLUE,
            "name": name,
            "description": description
        }
        response_dict = self.requestSender.send_request(request, data)
        return response_dict

    def handleUpdateGlueType(self, glue_id, name, description=""):
        """Update existing glue type"""
        request = glue_endpoints.GLUE_TYPES_SET
        data = {
            "header": glue_endpoints.REQUEST_RESOURCE_GLUE,
            "id": glue_id,
            "name": name,
            "description": description
        }
        response_dict = self.requestSender.send_request(request, data)
        return response_dict

    def handleRemoveGlueType(self, glue_id):
        """Remove glue type"""
        request = glue_endpoints.GLUE_TYPE_REMOVE_CUSTOM
        data = {
            "header": glue_endpoints.REQUEST_RESOURCE_GLUE,
            "id": glue_id
        }
        response_dict = self.requestSender.send_request(request, data)
        return response_dict

