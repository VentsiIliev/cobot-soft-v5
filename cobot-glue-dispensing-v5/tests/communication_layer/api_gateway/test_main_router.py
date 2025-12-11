import pytest
from unittest.mock import Mock, MagicMock
from communication_layer.api_gateway.dispatch.main_router import RequestHandler
from communication_layer.api.v1.endpoints import (
    auth_endpoints, operations_endpoints, camera_endpoints,
    settings_endpoints, robot_endpoints, workpiece_endpoints, glue_endpoints, modbus_endpoints
)
from communication_layer.api.v1 import Constants


@pytest.fixture
def mock_application():
    """Mock application with all necessary attributes"""
    app = Mock()
    app.handle.return_value = {"status": "success", "message": "Operation completed"}
    return app


@pytest.fixture
def mock_settings_controller():
    """Mock settings controller"""
    controller = Mock()
    # By default, return success for any call
    controller.handle.return_value = {"status": "success", "data": {}}
    return controller


@pytest.fixture
def mock_camera_controller():
    """Mock camera system controller"""
    controller = Mock()
    controller.handle.return_value = {"status": "success", "data": "camera_data"}
    return controller


@pytest.fixture
def mock_workpiece_controller():
    """Mock workpiece controller"""
    controller = Mock()
    controller.handle.return_value = {"status": "success", "data": "workpiece_data"}
    return controller


@pytest.fixture
def mock_robot_controller():
    """Mock robot controller"""
    controller = Mock()
    controller.handle.side_effect = ValueError("No handler registered for unknown request")
    return controller


@pytest.fixture
def mock_application_factory():
    """Mock application factory"""
    return Mock()


@pytest.fixture
def handler(mock_application, mock_settings_controller, mock_camera_controller,
            mock_workpiece_controller, mock_robot_controller, mock_application_factory):
    """Create RequestHandler with all mocked dependencies"""
    return RequestHandler(
        application=mock_application,
        settingsController=mock_settings_controller,
        cameraSystemController=mock_camera_controller,
        workpieceController=mock_workpiece_controller,
        robotController=mock_robot_controller,
        application_factory=mock_application_factory
    )


class TestRequestHandlerInitialization:
    """Test RequestHandler initialization and setup"""

    def test_handler_initialization(self, handler):
        """Test that handler initializes with all required components"""
        assert handler.application is not None
        assert handler.settingsController is not None
        assert handler.cameraSystemController is not None
        assert handler.workpieceController is not None
        assert handler.robotController is not None

    def test_dispatchers_initialized(self, handler):
        """Test that all dispatchers are properly initialized"""
        assert handler.auth_dispatcher is not None
        assert handler.robot_dispatcher is not None
        assert handler.camera_dispatcher is not None
        assert handler.workpiece_dispatcher is not None
        assert handler.settings_dispatcher is not None
        assert handler.operations_dispatcher is not None

    def test_resource_dispatch_mapping(self, handler):
        """Test that resource dispatch mapping is correctly configured"""
        expected_resources = ['robot', 'camera', 'settings', 'workpieces']  # Note: 'workpieces' not 'workpiece'
        for resource in expected_resources:
            assert resource in handler.resource_dispatch
            assert callable(handler.resource_dispatch[resource])


class TestAuthenticationRequests:
    """Test authentication-related requests"""

    def test_qr_login_request(self, handler):
        """Test QR login authentication request"""
        result = handler.handleRequest(auth_endpoints.QR_LOGIN, data={"code": "test123"})
        assert result is not None

    def test_standard_login_request(self, handler):
        """Test standard login authentication request"""
        result = handler.handleRequest(auth_endpoints.LOGIN, data={"username": "admin", "password": "pass"})
        assert result is not None


class TestOperationsRequests:
    """Test main operations requests"""

    @pytest.mark.parametrize("operation", [
        operations_endpoints.START,
        operations_endpoints.STOP,
        operations_endpoints.PAUSE,
        operations_endpoints.CALIBRATE,
        operations_endpoints.CREATE_WORKPIECE,
    ])
    def test_operations_requests(self, handler, operation):
        """Test that all operations requests are handled"""
        result = handler.handleRequest(operation)
        assert result is not None

    def test_legacy_operations(self, handler):
        """Test legacy operation endpoints"""
        result = handler.handleRequest("handleSetPreselectedWorkpiece", data={})
        assert result is not None

        result = handler.handleRequest("handleExecuteFromGallery", data={})
        assert result is not None


class TestCameraRequests:
    """Test camera-related requests"""

    def test_save_work_area_points(self, handler):
        """Test saving camera work area points"""
        result = handler.handleRequest(
            camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS,
            data={"points": [[0, 0], [100, 100]]}
        )
        assert result is not None

    def test_get_work_area_points(self, handler):
        """Test getting camera work area points"""
        result = handler.handleRequest(camera_endpoints.CAMERA_ACTION_GET_WORK_AREA_POINTS)
        assert result is not None

    def test_get_latest_frame(self, handler):
        """Test getting latest camera frame"""
        result = handler.handleRequest(camera_endpoints.CAMERA_ACTION_GET_LATEST_FRAME)
        assert result is not None

    def test_update_camera_feed(self, handler):
        """Test updating camera feed"""
        result = handler.handleRequest(camera_endpoints.UPDATE_CAMERA_FEED)
        assert result is not None

    def test_camera_calibration(self, handler):
        """Test camera calibration"""
        result = handler.handleRequest(camera_endpoints.CAMERA_ACTION_CALIBRATE)
        assert result is not None

    def test_camera_raw_mode_on(self, handler):
        """Test enabling camera raw mode"""
        result = handler.handleRequest(camera_endpoints.CAMERA_ACTION_RAW_MODE_ON)
        assert result is not None

    def test_camera_raw_mode_off(self, handler):
        """Test disabling camera raw mode"""
        result = handler.handleRequest(camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF)
        assert result is not None

    def test_start_contour_detection(self, handler):
        """Test starting contour detection"""
        result = handler.handleRequest(camera_endpoints.START_CONTOUR_DETECTION)
        assert result is not None

    def test_stop_contour_detection(self, handler):
        """Test stopping contour detection"""
        result = handler.handleRequest(camera_endpoints.STOP_CONTOUR_DETECTION)
        assert result is not None


class TestResourceBasedRouting:
    """Test resource-based routing (robot, camera, settings, workpiece)"""

    def test_robot_resource_routing(self, handler, mock_robot_controller):
        """Test requests with 'robot' resource are routed correctly"""
        mock_robot_controller.handle.return_value = {"status": "success"}
        result = handler.handleRequest(robot_endpoints.ROBOT_MOVE_TO_HOME_POS, data={})
        assert result is not None

    def test_camera_resource_routing(self, handler):
        """Test requests with 'camera' resource are routed correctly"""
        result = handler.handleRequest(camera_endpoints.CAMERA_ACTION_GET_LATEST_FRAME)
        assert result is not None

    def test_settings_resource_routing(self, handler, mock_settings_controller):
        """Test requests with 'settings' resource are routed correctly"""
        mock_settings_controller.handle.return_value = {"status": "success", "data": {}}
        result = handler.handleRequest(settings_endpoints.SETTINGS_ROBOT_GET)
        assert result is not None

    def test_workpiece_resource_routing(self, handler):
        """Test requests with 'workpiece' resource are routed correctly"""
        result = handler.handleRequest(workpiece_endpoints.WORKPIECE_GET_ALL)
        assert result is not None


class TestRequestParsing:
    """Test request path parsing"""

    def test_parse_request_basic(self, handler):
        """Test basic request parsing"""
        result = handler._parseRequest("/api/v1/robot/move")
        assert result == ["api", "v1", "robot", "move"]

    def test_parse_request_with_trailing_slash(self, handler):
        """Test parsing request with trailing slash"""
        result = handler._parseRequest("/api/v1/camera/")
        assert result == ["api", "v1", "camera"]

    def test_parse_request_no_leading_slash(self, handler):
        """Test parsing request without leading slash"""
        result = handler._parseRequest("api/v1/settings/get")
        assert result == ["api", "v1", "settings", "get"]

    def test_parse_request_with_params(self, handler):
        """Test parsing complex request with multiple parts"""
        result = handler._parseRequest("/api/v1/workpieces/create/step-1")
        assert result == ["api", "v1", "workpieces", "create", "step-1"]


class TestErrorHandling:
    """Test error handling and invalid requests"""

    def test_unknown_request_raises_value_error(self, handler):
        """Test that completely unknown requests raise ValueError"""
        with pytest.raises(ValueError) as excinfo:
            handler.handleRequest("/api/v1/unknown/resource/action")
        assert "unknown request" in str(excinfo.value).lower()

    def test_invalid_robot_request(self, handler, mock_robot_controller):
        """Test invalid robot request raises error from controller"""
        mock_robot_controller.handle.side_effect = ValueError("No handler registered")
        with pytest.raises(ValueError):
            handler.handleRequest("/api/v1/robot/invalid_action")

    def test_invalid_settings_request(self, handler, mock_settings_controller):
        """Test invalid settings request is handled by controller"""
        # For invalid requests, settings controller should raise ValueError
        mock_settings_controller.handle.side_effect = ValueError("No handler registered")
        with pytest.raises(ValueError):
            handler.handleRequest("/api/v1/settings/invalid_action")


class TestResourceDetection:
    """Test resource detection in request paths"""

    @pytest.mark.parametrize("path,expected_resource", [
        ("/api/v1/robot/move", "robot"),
        ("/api/v1/camera/capture", "camera"),
        ("/api/v1/settings/get", "settings"),
        ("/api/v1/workpieces/create", "workpieces"),
    ])
    def test_resource_detection(self, handler, path, expected_resource):
        """Test that resources are correctly detected from paths"""
        parts = handler._parseRequest(path)
        detected_resource = next(
            (p.lower() for p in parts if p.lower() in handler.resource_dispatch),
            None
        )
        assert detected_resource == expected_resource

    def test_no_resource_detected(self, handler):
        """Test behavior when no resource is detected"""
        parts = handler._parseRequest("/api/v1/unknown/action")
        detected_resource = next(
            (p.lower() for p in parts if p.lower() in handler.resource_dispatch),
            None
        )
        assert detected_resource is None


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_complete_operation_workflow(self, handler):
        """Test a complete workflow: create workpiece -> start -> stop"""
        # Create workpiece
        result1 = handler.handleRequest(
            operations_endpoints.CREATE_WORKPIECE,
            data={"name": "test_wp"}
        )
        assert result1 is not None

        # Start operation
        result2 = handler.handleRequest(operations_endpoints.START)
        assert result2 is not None

        # Stop operation
        result3 = handler.handleRequest(operations_endpoints.STOP)
        assert result3 is not None

    def test_settings_workflow(self, handler, mock_settings_controller):
        """Test settings get and update workflow"""
        mock_settings_controller.handle.return_value = {"status": "success", "data": {"key": "value"}}

        # Get robot settings (valid endpoint)
        result1 = handler.handleRequest(settings_endpoints.SETTINGS_ROBOT_GET)
        assert result1 is not None

        # Update robot settings (valid endpoint)
        result2 = handler.handleRequest(
            settings_endpoints.SETTINGS_ROBOT_SET,
            data={"key": "new_value"}
        )
        assert result2 is not None


class TestRobotEndpoints:
    """Test all robot-related endpoints"""

    def test_robot_jog_operations(self, handler, mock_robot_controller):
        """Test robot jogging operations"""
        mock_robot_controller.handle.return_value = {"status": "success"}

        # Test all jog directions
        jog_endpoints = [
            robot_endpoints.ROBOT_ACTION_JOG_X_PLUS,
            robot_endpoints.ROBOT_ACTION_JOG_X_MINUS,
            robot_endpoints.ROBOT_ACTION_JOG_Y_PLUS,
            robot_endpoints.ROBOT_ACTION_JOG_Y_MINUS,
            robot_endpoints.ROBOT_ACTION_JOG_Z_PLUS,
            robot_endpoints.ROBOT_ACTION_JOG_Z_MINUS,
        ]

        for endpoint in jog_endpoints:
            result = handler.handleRequest(endpoint)
            assert result is not None

    def test_robot_slot_operations(self, handler, mock_robot_controller):
        """Test robot slot pickup/drop operations"""
        mock_robot_controller.handle.return_value = {"status": "success"}

        slot_endpoints = [
            robot_endpoints.ROBOT_SLOT_0_PICKUP,
            robot_endpoints.ROBOT_SLOT_0_DROP,
            robot_endpoints.ROBOT_SLOT_1_PICKUP,
            robot_endpoints.ROBOT_SLOT_1_DROP,
            robot_endpoints.ROBOT_SLOT_2_PICKUP,
            robot_endpoints.ROBOT_SLOT_2_DROP,
            robot_endpoints.ROBOT_SLOT_3_PICKUP,
            robot_endpoints.ROBOT_SLOT_3_DROP,
        ]

        for endpoint in slot_endpoints:
            result = handler.handleRequest(endpoint)
            assert result is not None

    def test_robot_movement_operations(self, handler, mock_robot_controller):
        """Test robot movement operations"""
        mock_robot_controller.handle.return_value = {"status": "success"}

        movement_endpoints = [
            robot_endpoints.ROBOT_MOVE_TO_HOME_POS,
            robot_endpoints.ROBOT_MOVE_TO_CALIB_POS,
            robot_endpoints.ROBOT_MOVE_TO_LOGIN_POS,
            robot_endpoints.ROBOT_EXECUTE_NOZZLE_CLEAN,
            robot_endpoints.ROBOT_STOP,
            robot_endpoints.ROBOT_CALIBRATE,
            robot_endpoints.ROBOT_CALIBRATE_PICKUP,
        ]

        for endpoint in movement_endpoints:
            result = handler.handleRequest(endpoint)
            assert result is not None


class TestGlueEndpoints:
    """Test all glue-related endpoints"""

    def test_glue_settings_operations(self, handler):
        """Test glue settings get/set operations"""
        result = handler.handleRequest(glue_endpoints.SETTINGS_GLUE_GET)
        assert result is not None

        result = handler.handleRequest(glue_endpoints.SETTINGS_GLUE_SET, data={"key": "value"})
        assert result is not None

    def test_glue_cells_config_operations(self, handler):
        """Test glue cells configuration operations"""
        result = handler.handleRequest(glue_endpoints.GLUE_CELLS_CONFIG_GET)
        assert result is not None

        result = handler.handleRequest(glue_endpoints.GLUE_CELLS_CONFIG_SET, data={"cells": []})
        assert result is not None

        result = handler.handleRequest(glue_endpoints.GLUE_CELL_UPDATE, data={"cell_id": 1})
        assert result is not None

        result = handler.handleRequest(glue_endpoints.GLUE_CELL_CALIBRATE, data={"cell_id": 1})
        assert result is not None

        result = handler.handleRequest(glue_endpoints.GLUE_CELL_TARE, data={"cell_id": 1})
        assert result is not None

    def test_glue_types_operations(self, handler):
        """Test glue types management operations"""
        result = handler.handleRequest(glue_endpoints.GLUE_TYPES_GET)
        assert result is not None

        result = handler.handleRequest(glue_endpoints.GLUE_TYPES_SET, data={"types": []})
        assert result is not None

        result = handler.handleRequest(glue_endpoints.GLUE_TYPE_ADD_CUSTOM, data={"name": "NewType"})
        assert result is not None

        result = handler.handleRequest(glue_endpoints.GLUE_TYPE_REMOVE_CUSTOM, data={"name": "OldType"})
        assert result is not None

    def test_cell_hardware_config(self, handler):
        """Test cell hardware configuration operations"""
        result = handler.handleRequest(glue_endpoints.CELL_HARDWARE_CONFIG_GET)
        assert result is not None

        result = handler.handleRequest(glue_endpoints.CELL_HARDWARE_CONFIG_SET, data={"config": {}})
        assert result is not None

        result = handler.handleRequest(glue_endpoints.CELL_HARDWARE_MOTOR_ADDRESS_GET)
        assert result is not None


class TestModbusEndpoints:
    """Test all modbus-related endpoints"""

    def test_modbus_config_operations(self, handler):
        """Test modbus configuration operations"""
        result = handler.handleRequest(modbus_endpoints.MODBUS_CONFIG_GET)
        assert result is not None

        result = handler.handleRequest(
            modbus_endpoints.MODBUS_CONFIG_UPDATE,
            data={"port": "COM1", "baudrate": 9600}
        )
        assert result is not None

    def test_modbus_connection_operations(self, handler):
        """Test modbus connection testing"""
        result = handler.handleRequest(modbus_endpoints.MODBUS_TEST_CONNECTION)
        assert result is not None

        result = handler.handleRequest(modbus_endpoints.MODBUS_GET_AVAILABLE_PORT)
        assert result is not None


class TestWorkpieceEndpoints:
    """Test all workpiece-related endpoints"""

    def test_workpiece_crud_operations(self, handler):
        """Test workpiece CRUD operations"""
        result = handler.handleRequest(workpiece_endpoints.WORKPIECE_GET_ALL)
        assert result is not None

        result = handler.handleRequest(
            workpiece_endpoints.WORKPIECE_SAVE,
            data={"name": "test_wp"}
        )
        assert result is not None

        result = handler.handleRequest(
            workpiece_endpoints.WORKPIECE_GET_BY_ID,
            data={"id": "123"}
        )
        assert result is not None

        result = handler.handleRequest(
            workpiece_endpoints.WORKPIECE_DELETE,
            data={"id": "123"}
        )
        assert result is not None

    def test_workpiece_import_operations(self, handler):
        """Test workpiece import operations"""
        result = handler.handleRequest(
            workpiece_endpoints.WORKPIECE_SAVE_DXF,
            data={"file": "test.dxf"}
        )
        assert result is not None


class TestSettingsEndpoints:
    """Test all settings-related endpoints"""

    def test_camera_settings_operations(self, handler):
        """Test camera settings get/set operations"""
        result = handler.handleRequest(settings_endpoints.SETTINGS_CAMERA_GET)
        assert result is not None

        result = handler.handleRequest(
            settings_endpoints.SETTINGS_CAMERA_SET,
            data={"width": 1920}
        )
        assert result is not None

    def test_robot_calibration_settings(self, handler):
        """Test robot calibration settings operations"""
        result = handler.handleRequest(settings_endpoints.SETTINGS_ROBOT_CALIBRATION_GET)
        assert result is not None

        result = handler.handleRequest(
            settings_endpoints.SETTINGS_ROBOT_CALIBRATION_SET,
            data={"calibration": {}}
        )
        assert result is not None

