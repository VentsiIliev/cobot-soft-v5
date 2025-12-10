"""
Settings Domain Service

Handles all settings-related operations with explicit return values.
No callbacks - just clean, clear method calls!
"""

import logging
from typing import TYPE_CHECKING, Any
from enum import Enum

from applications.glue_dispensing_application.settings import GlueSettings
from communication_layer.api.v1 import Constants
from communication_layer.api.v1.endpoints import settings_endpoints, glue_endpoints
from communication_layer.api.v1.Response import Response
from core.model.settings.CameraSettings import CameraSettings
from core.model.settings.robotConfig.robotConfigModel import RobotConfig

from frontend.core.services.types.ServiceResult import ServiceResult

# Import settings classes for type hints and validation

# Import UI component classes for validation
from plugins.core.settings.ui.CameraSettingsTabLayout import CameraSettingsTabLayout
from plugins.core.glue_settings_plugin.ui.GlueSettingsTabLayout import GlueSettingsTabLayout
from plugins.core.settings.ui.robot_settings_tab.RobotConfigUI import RobotConfigUI




class SettingComponentType(Enum):
    """Valid component types for settings updates"""
    CAMERA = CameraSettingsTabLayout.__module__
    GLUE = GlueSettingsTabLayout.__module__
    ROBOT = RobotConfigUI.__module__



class SettingsService:
    """
    Domain service for all settings operations.
    
    Provides explicit, type-safe methods for settings management.
    All methods return ServiceResult - no callbacks needed!
    
    Usage:
        result = settings_service.update_setting("width", 1920, "CameraSettingsTabLayout")
        if result:
            print("Setting updated successfully!")
        else:
            print(f"Failed: {result.message}")
    """
    
    def __init__(self, controller: 'Controller', logger: logging.Logger):
        """
        Initialize the settings service.
        
        Args:
            controller: The main controller instance
            logger: Logger for this service
        """
        self.controller = controller
        self.logger = logger.getChild(self.__class__.__name__)
    
    def update_setting(self, key: str, value: Any, component_type: str) -> ServiceResult:
        """
        Update a single setting value.
        
        Args:
            key: The setting key to update
            value: The new value for the setting
            component_type: The UI component type (determines setting category)
        
        Returns:
            ServiceResult with success/failure status and message
        """
        try:
            # Validate component type
            if not self._validate_component_type(component_type):
                return ServiceResult.error_result(
                    f"Invalid component type: {component_type}. "
                    f"Valid types: {[t.value for t in SettingComponentType]}"
                )
            
            # Validate key and value
            validation_result = self._validate_setting_value(key, value, component_type)
            if not validation_result.success:
                return validation_result
            
            # Log the operation
            print(f"Updating {component_type} setting: {key} = {value}")
            
            # Call the controller
            self.controller.updateSettings(key, value, component_type)
            
            return ServiceResult.success_result(
                f"Setting '{key}' updated successfully",
                data={"key": key, "value": value, "component": component_type}
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"Failed to update setting '{key}': {str(e)}"
            return ServiceResult.error_result(error_msg)
    
    def get_all_settings(self) -> ServiceResult:
        """
        Get all settings (camera, robot, glue).
        
        Returns:
            ServiceResult with settings data or error message
        """
        try:
            print("Retrieving all settings")
            
            # Call the controller
            camera_settings, glue_settings,robot_settings = self.controller.handleGetSettings()
            
            settings_data = {
                "camera": camera_settings,
                "glue": glue_settings,
                "robot": robot_settings
            }
            
            return ServiceResult.success_result(
                "Settings retrieved successfully",
                data=settings_data
            )
            
        except Exception as e:
            error_msg = f"Failed to retrieve settings: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)
    
    def get_camera_settings(self) -> ServiceResult:
        """Get only camera settings - optimized to avoid fetching all settings"""
        try:
            print("[SettingsService] Fetching camera settings only...")


            camera_request = settings_endpoints.SETTINGS_CAMERA_GET
            camera_response_dict = self.controller.requestSender.send_request(camera_request)
            camera_response = Response.from_dict(camera_response_dict)

            if camera_response.status == Constants.RESPONSE_STATUS_SUCCESS:
                camera_settings_dict = camera_response.data
                camera_settings = CameraSettings(data=camera_settings_dict)
                return ServiceResult.success_result(
                    "Camera settings retrieved successfully",
                    data=camera_settings
                )
            else:
                return ServiceResult.error_result(f"Failed to retrieve camera settings: {camera_response.message}")

        except Exception as e:
            error_msg = f"Failed to retrieve camera settings: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def get_robot_settings(self) -> ServiceResult:
        """Get only robot settings - optimized to avoid fetching all settings"""
        try:
            print("[SettingsService] Fetching robot settings only...")


            robot_request = settings_endpoints.SETTINGS_ROBOT_GET
            robot_response_dict = self.controller.requestSender.send_request(robot_request)
            robot_response = Response.from_dict(robot_response_dict)

            if robot_response.status == Constants.RESPONSE_STATUS_SUCCESS:
                robot_settings_dict = robot_response.data
                robot_config = RobotConfig.from_dict(robot_settings_dict)
                return ServiceResult.success_result(
                    "Robot settings retrieved successfully",
                    data=robot_config
                )
            else:
                return ServiceResult.error_result(f"Failed to retrieve robot settings: {robot_response.message}")

        except Exception as e:
            error_msg = f"Failed to retrieve robot settings: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def get_glue_settings(self) -> ServiceResult:
        """Get only glue settings - optimized to avoid fetching all settings"""
        try:
            print("[SettingsService] Fetching glue settings only...")

            glue_request = glue_endpoints.SETTINGS_GLUE_GET
            glue_response_dict = self.controller.requestSender.send_request(glue_request)
            glue_response = Response.from_dict(glue_response_dict)

            if glue_response.status == Constants.RESPONSE_STATUS_SUCCESS:
                glue_settings_dict = glue_response.data
                glue_settings = GlueSettings(glue_settings_dict)
                return ServiceResult.success_result(
                    "Glue settings retrieved successfully",
                    data=glue_settings
                )
            else:
                return ServiceResult.error_result(f"Failed to retrieve glue settings: {glue_response.message}")

        except Exception as e:
            error_msg = f"Failed to retrieve glue settings: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def get_modbus_settings(self) -> ServiceResult:
        """Get Modbus configuration settings"""
        try:
            print("[SettingsService] Fetching modbus settings...")

            from communication_layer.api.v1.endpoints import modbus_endpoints

            modbus_request = modbus_endpoints.MODBUS_CONFIG_GET
            modbus_response_dict = self.controller.requestSender.send_request(modbus_request)
            modbus_response = Response.from_dict(modbus_response_dict)

            if modbus_response.status == Constants.RESPONSE_STATUS_SUCCESS:
                modbus_config = modbus_response.data
                return ServiceResult.success_result(
                    "Modbus settings retrieved successfully",
                    data=modbus_config
                )
            else:
                return ServiceResult.error_result(f"Failed to retrieve modbus settings: {modbus_response.message}")

        except Exception as e:
            error_msg = f"Failed to retrieve modbus settings: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def update_modbus_setting(self, field: str, value: Any) -> ServiceResult:
        """
        Update a single Modbus configuration field.

        Args:
            field: The field name to update (e.g., 'port', 'baudrate', 'slave_address')
            value: The new value for the field

        Returns:
            ServiceResult with success/failure status and message
        """
        try:
            print(f"[SettingsService] Updating modbus setting: {field} = {value}")

            from communication_layer.api.v1.endpoints import modbus_endpoints

            request_data = {
                'field': field,
                'value': value
            }

            response_dict = self.controller.requestSender.send_request(
                modbus_endpoints.MODBUS_CONFIG_UPDATE,
                data=request_data
            )
            response = Response.from_dict(response_dict)

            if response.status == Constants.RESPONSE_STATUS_SUCCESS:
                return ServiceResult.success_result(
                    f"Modbus setting '{field}' updated successfully",
                    data={"field": field, "value": value}
                )
            else:
                return ServiceResult.error_result(f"Failed to update modbus setting '{field}': {response.message}")

        except Exception as e:
            error_msg = f"Failed to update modbus setting '{field}': {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def test_modbus_connection(self) -> ServiceResult:
        """
        Test the Modbus connection with current configuration.

        Returns:
            ServiceResult with success/failure status and connection test result
        """
        try:
            print("[SettingsService] Testing modbus connection...")

            from communication_layer.api.v1.endpoints import modbus_endpoints

            response_dict = self.controller.requestSender.send_request(modbus_endpoints.MODBUS_TEST_CONNECTION)
            response = Response.from_dict(response_dict)

            if response.status == Constants.RESPONSE_STATUS_SUCCESS:
                return ServiceResult.success_result(
                    f"Connection successful: {response.message}",
                    data={"connected": True}
                )
            else:
                return ServiceResult.error_result(f"Connection failed: {response.message}")

        except Exception as e:
            error_msg = f"Error testing modbus connection: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def detect_modbus_port(self) -> ServiceResult:
        """
        Detect available Modbus serial port.

        Returns:
            ServiceResult with detected port information or error
        """
        try:
            print("[SettingsService] Detecting modbus port...")

            from communication_layer.api.v1.endpoints import modbus_endpoints

            response_dict = self.controller.requestSender.send_request(modbus_endpoints.MODBUS_GET_AVAILABLE_PORT)
            response = Response.from_dict(response_dict)

            if response.status == Constants.RESPONSE_STATUS_SUCCESS:
                detected_port = response.data.get('port', '')
                if detected_port and detected_port.strip():
                    return ServiceResult.success_result(
                        f"Port detected: {detected_port}",
                        data={"port": detected_port}
                    )
                else:
                    return ServiceResult.error_result("No Modbus port detected")
            else:
                return ServiceResult.error_result(f"Failed to detect port: {response.message}")

        except Exception as e:
            error_msg = f"Error detecting modbus port: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)
    
    def get_glue_cells_config(self) -> ServiceResult:
        """
        Get glue cells configuration.

        Returns:
            ServiceResult with glue cells config data or error
        """
        try:
            print("[SettingsService] Fetching glue cells configuration...")

            response_dict = self.controller.requestSender.send_request(glue_endpoints.GLUE_CELLS_CONFIG_GET)
            response = Response.from_dict(response_dict)

            if response.status == Constants.RESPONSE_STATUS_SUCCESS:
                return ServiceResult.success_result(
                    "Glue cells configuration retrieved successfully",
                    data=response.data
                )
            else:
                return ServiceResult.error_result(f"Failed to retrieve glue cells config: {response.message}")

        except Exception as e:
            error_msg = f"Failed to retrieve glue cells configuration: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def update_glue_cells_config(self, config_data: dict) -> ServiceResult:
        """
        Update glue cells configuration (including MODE).

        Args:
            config_data: Dictionary with configuration updates (e.g., {"MODE": "test"})

        Returns:
            ServiceResult with success/failure status
        """
        try:
            print(f"[SettingsService] Updating glue cells configuration: {config_data}")

            response_dict = self.controller.requestSender.send_request(
                glue_endpoints.GLUE_CELLS_CONFIG_SET,
                data=config_data
            )
            response = Response.from_dict(response_dict)

            if response.status == Constants.RESPONSE_STATUS_SUCCESS:
                return ServiceResult.success_result(
                    "Glue cells configuration updated successfully",
                    data=config_data
                )
            else:
                return ServiceResult.error_result(f"Failed to update glue cells config: {response.message}")

        except Exception as e:
            error_msg = f"Failed to update glue cells configuration: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def update_glue_cell(self, cell_id: int, cell_data: dict) -> ServiceResult:
        """
        Update a specific glue cell configuration.

        Args:
            cell_id: The cell ID to update
            cell_data: Dictionary with cell configuration updates

        Returns:
            ServiceResult with success/failure status
        """
        try:
            print(f"[SettingsService] Updating cell {cell_id} configuration: {cell_data}")

            request_data = {
                "cell_id": cell_id,
                **cell_data
            }

            response_dict = self.controller.requestSender.send_request(
                glue_endpoints.GLUE_CELL_UPDATE,
                data=request_data
            )
            response = Response.from_dict(response_dict)

            if response.status == Constants.RESPONSE_STATUS_SUCCESS:
                return ServiceResult.success_result(
                    f"Cell {cell_id} updated successfully",
                    data={"cell_id": cell_id, **cell_data}
                )
            else:
                return ServiceResult.error_result(f"Failed to update cell {cell_id}: {response.message}")

        except Exception as e:
            error_msg = f"Failed to update cell {cell_id}: {str(e)}"
            import traceback
            traceback.print_exc()
            return ServiceResult.error_result(error_msg)

    def _validate_component_type(self, component_type: str) -> bool:
        """Validate that the component type is supported"""
        valid_types = [t.value for t in SettingComponentType]
        return component_type in valid_types
    
    def _validate_setting_value(self, key: str, value: Any, component_type: str) -> ServiceResult:
        """
        Validate setting key and value based on component type.
        
        Args:
            key: Setting key to validate
            value: Setting value to validate
            component_type: Component type for context
        
        Returns:
            ServiceResult indicating validation success/failure
        """
        try:
            # Basic validation
            if not key or key.strip() == "":
                return ServiceResult.error_result("Setting key cannot be empty")
            
            if value is None:
                return ServiceResult.error_result("Setting value cannot be None")
            
            # Component-specific validation
            try:
                component = SettingComponentType(component_type)
            except ValueError:
                # Handle legacy component types that don't match enum values
                print(f"Unknown component type: {component_type}. Allowing for backward compatibility.")
                return ServiceResult.success_result("Validation passed (unknown component type)")
            
            if component == SettingComponentType.CAMERA:
                return self._validate_camera_setting(key, value)
            elif component == SettingComponentType.ROBOT:
                return self._validate_robot_setting(key, value)
            elif component == SettingComponentType.GLUE:
                return self._validate_glue_setting(key, value)
            
            return ServiceResult.success_result("Validation passed")
            
        except Exception as e:
            return ServiceResult.error_result(f"Validation error: {str(e)}")
    
    def _validate_camera_setting(self, key: str, value: Any) -> ServiceResult:
        """Validate camera-specific settings"""
        # Add camera-specific validation logic here
        # For now, just basic type checks
        if key in ["width", "height", "skip_frames"] and not isinstance(value, (int, float)):
            return ServiceResult.error_result(f"Camera setting '{key}' must be a number")
        
        return ServiceResult.success_result("Camera setting validation passed")
    
    def _validate_robot_setting(self, key: str, value: Any) -> ServiceResult:
        """Validate robot-specific settings"""
        # Add robot-specific validation logic here
        if key in ["velocity", "acceleration"] and not isinstance(value, (int, float)):
            return ServiceResult.error_result(f"Robot setting '{key}' must be a number")
        
        return ServiceResult.success_result("Robot setting validation passed")
    
    def _validate_glue_setting(self, key: str, value: Any) -> ServiceResult:
        """Validate glue-specific settings"""
        # Add glue-specific validation logic here
        if key in ["motor_speed", "fan_speed"] and not isinstance(value, (int, float)):
            return ServiceResult.error_result(f"Glue setting '{key}' must be a number")
        
        return ServiceResult.success_result("Glue setting validation passed")