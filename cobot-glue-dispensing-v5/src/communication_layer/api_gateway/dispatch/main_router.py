from communication_layer.api_gateway.dispatch.auth_dispatcher import AuthDispatch
from communication_layer.api_gateway.dispatch.camera_dispatcher import CameraDispatch
from communication_layer.api_gateway.dispatch.operations_dispatcher import OperationsDispatch
from communication_layer.api_gateway.dispatch.robot_dispatcher import RobotDispatch
from communication_layer.api_gateway.dispatch.settings_dispatcher import SettingsDispatch
from communication_layer.api_gateway.dispatch.workpiece_dispatcher import WorkpieceDispatch
from communication_layer.api_gateway.interfaces.request_handler_interface import IRequestHandler
from core.application.interfaces.robot_application_interface import RobotApplicationInterface
from communication_layer.api.v1 import Constants

# Import endpoint modules
from communication_layer.api.v1.endpoints import camera_endpoints, operations_endpoints, auth_endpoints
from core.controllers.vision.camera_system_controller import CameraSystemController
from core.controllers.workpiece.BaseWorkpieceController import BaseWorkpieceController


class RequestHandler(IRequestHandler):
    """
      Handles the incoming requests and routes them to appropriate handlers
      based on the type of request (GET, POST, EXECUTE).

      Attributes:
          application: The main controller for handling operations.
          settingsController: Controller for managing settings.
          cameraSystemController: Controller for camera system operations.
          workpieceController: Controller for managing workpieces.
          robotController: Controller for managing robot operations.
      """

    def __init__(self, application: RobotApplicationInterface, settingsController,
                 cameraSystemController: CameraSystemController, workpieceController: BaseWorkpieceController,
                 robotController, application_factory=None):
        """
              Initializes the RequestHandler with the necessary controllers.

              Args:
                  application (RobotApplicationInterface): The robot application instance.
                  settingsController (object): The settings controller.
                  cameraSystemController (object): The camera system controller.
                  workpieceController (object): The workpieces' controller.
                  robotController (object): The robot controller.
                  application_factory (ApplicationFactory): Optional factory for application switching.
              """
        self.application = application
        self.settingsController = settingsController
        self.cameraSystemController = cameraSystemController
        self.workpieceController = workpieceController
        self.robotController = robotController

        # Initialize specialized dispatchers
        self.auth_dispatcher = AuthDispatch()
        self.robot_dispatcher = RobotDispatch(self.application, self.robotController)
        self.camera_dispatcher = CameraDispatch(self.application, self.cameraSystemController)
        self.workpiece_dispatcher = WorkpieceDispatch(self.application, self.workpieceController)
        self.settings_dispatcher = SettingsDispatch(self.settingsController)
        self.operations_dispatcher = OperationsDispatch(self.application, application_factory)

        self.resource_dispatch = {
            Constants.REQUEST_RESOURCE_ROBOT.lower(): self.robot_dispatcher.dispatch,
            Constants.REQUEST_RESOURCE_CAMERA.lower(): self.camera_dispatcher.dispatch,
            Constants.REQUEST_RESOURCE_SETTINGS.lower(): self.settings_dispatcher.dispatch,
            Constants.REQUEST_RESOURCE_WORKPIECE.lower(): self.workpiece_dispatcher.dispatch,
        }

    def handleRequest(self, request, data=None):
        """
        Main request handler that routes requests to specialized handlers.
        
        This method now delegates to specialized handlers for better organization.
        """
        # print(f"RequestHandler: Processing request: {request}")

        # Authentication requests
        if request in [auth_endpoints.QR_LOGIN]:
            return self.auth_dispatcher.dispatch(parts=[], request=request, data=data)

        # Main operations requests
        operations_requests = [
            operations_endpoints.START, operations_endpoints.STOP, operations_endpoints.PAUSE,
            operations_endpoints.TEST_RUN,
            operations_endpoints.RUN_DEMO, operations_endpoints.STOP_DEMO, operations_endpoints.CALIBRATE,
            operations_endpoints.HELP,
            operations_endpoints.CREATE_WORKPIECE, "handleSetPreselectedWorkpiece", "handleExecuteFromGallery"
        ]

        if request in operations_requests:
            return self.operations_dispatcher.dispatch(parts=[], request=request, data=data)

        # Camera work area points
        if (request in [camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS] or
                (len(self._parseRequest(request)) >= 2 and self._parseRequest(request)[1] == "saveWorkAreaPoints")):
            return self.camera_dispatcher.handle_save_work_area_points(data)

        # Parse request for resource-based routing
        parts = self._parseRequest(request)

        # Try to detect which resource (robot, camera, settings, workpieces) is present in the path
        resource = next((p.lower() for p in parts if p.lower() in self.resource_dispatch), None)
        if resource:
            return self.resource_dispatch[resource](parts=[], request=request, data=data)

        print(f"RequestHandler: No handler found for request: {request}")
        print(f"Resource parsed: {resource}")
        print(f"Available resources: {list(self.resource_dispatch.keys())}")
        raise ValueError(f"Unknown request: {request}")

    def _parseRequest(self, request: str):
        """
        Parses the incoming request path into parts.
        Example:
            '/api/v1/workpieces/create/step-1' -> ['api', 'v1', 'workpieces', 'create', 'step-1']
        """
        return [p for p in request.strip("/").split("/") if p]
