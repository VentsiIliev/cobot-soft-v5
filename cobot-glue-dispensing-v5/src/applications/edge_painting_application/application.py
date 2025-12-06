from applications.edge_painting_application.painting_operation import PaintingOperation
from communication_layer.api.v1.topics import SystemTopics
from core.application.interfaces.application_settings_interface import ApplicationSettingsRegistry
from core.application.interfaces.robot_application_interface import RobotApplicationInterface
from core.application_state_management import ApplicationState
from core.base_robot_application import BaseRobotApplication, ApplicationMetadata, PluginType
from core.model.robot.robot_types import RobotType
from core.operation_state_management import OperationResult, OperationStatePublisher, OperationState
from core.services.robot_service.impl.base_robot_service import RobotService
from core.services.settings.SettingsService import SettingsService
from core.services.vision.VisionService import _VisionService
from core.system_state_management import ServiceRegistry
from modules.shared.MessageBroker import MessageBroker



class OperationPublisher:
    pass


class EdgePaintingApplication(BaseRobotApplication, RobotApplicationInterface):

    def __init__(self, vision_service: _VisionService,
                 settings_manager: SettingsService,
                 robot_service: RobotService,
                 settings_registry: ApplicationSettingsRegistry,
                 service_registry: ServiceRegistry,
                 **kwargs):

        self.vision_service = vision_service
        self.settings_manager = settings_manager
        self.robot_service = robot_service
        self.settings_registry = settings_registry
        self.service_registry = service_registry
        super().__init__(vision_service, settings_manager, robot_service, settings_registry, **kwargs)
        # Register application-specific settings after initialization
        self._register_settings()
        self.broker = MessageBroker()
        self.painting_operation = PaintingOperation()
        self.painting_operation.set_state_publisher(OperationStatePublisher(broker=self.broker))
        self.broker.publish(SystemTopics.OPERATION_STATE, OperationState.IDLE)
        self.current_operation = self.painting_operation

    @staticmethod
    def get_metadata() -> ApplicationMetadata:
        return ApplicationMetadata(
            name="Edge Painting Application",
            version="1.0.0",
            robot_type=RobotType.ZERO_ERROR,  # Paint application uses ZeroError robot
            dependencies=["_VisionService",
                          "SettingsService",
                          "GlueRobotService",
                          "ApplicationSettingsRegistry"],
            plugin_dependencies=[
                PluginType.DASHBOARD,
                PluginType.SETTINGS,
                PluginType.CALIBRATION,
                PluginType.USER_MANAGEMENT
            ],
            settings_tabs=["camera", "robot"]
        )


    def get_initial_state(self) -> ApplicationState:
        return ApplicationState.INITIALIZING

    def set_current_operation(self):
        """determine the current operation based on mode"""
        pass

    def _on_operation_start(self, **kwargs) -> OperationResult:
        print(f"Painting in progress")
        print(self.robotService.robot_config)
        print(f"###### Robot Calibration Settings ######")
        print(self.settingsManager.get_robot_calibration_settings().to_dict())
        self.painting_operation.start()
        return OperationResult(success=True, message="Painting started")

    @property
    def operation(self):
        return self.current_operation

    def on_mode_change(self, mode):
        pass

    def reset(self) -> OperationResult:
        pass

    def _register_settings(self):
        # Register application-specific settings here
        pass

    def _initialize_application(self):
        super()._initialize_application()
        print("ROS2 node spinning in background thread")
