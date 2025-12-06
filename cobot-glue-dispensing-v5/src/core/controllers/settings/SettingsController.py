import traceback

from core.application.interfaces.application_settings_interface import ApplicationSettingsRegistry
from core.controllers.BaseController import BaseController
from communication_layer.api.v1 import Constants
from communication_layer.api.v1.Response import Response
import communication_layer.api.v1.endpoints.settings_endpoints as settings_endpoints

from core.services.settings.SettingsService import SettingsService
from core.services.vision.VisionService import VisionServiceSingleton


class SettingsController(BaseController):
    """
    Controller for managing system settings via API requests.

    Supports:
        - Core settings (robot and camera)
        - Application-specific settings through registry
        - Generic settings routing
        - Dynamic endpoint handling
    """

    def __init__(self, settingsService: SettingsService, settings_registry: ApplicationSettingsRegistry):
        self.settingsService = settingsService
        self.settings_registry = settings_registry
        super().__init__()
        self._initialize_handlers()

        # Dynamic resolver
        self._dynamic_handler_resolver = self._resolve_dynamic_handler
    # ============================================================
    # REGISTER HANDLERS
    # ============================================================
    def _initialize_handlers(self):
        # ------------------------------
        # CORE SETTINGS - GET
        # ------------------------------
        self.register_handler(
            settings_endpoints.SETTINGS_ROBOT_GET,
            lambda data=None: self._handleGet("robot")
        )

        self.register_handler(
            settings_endpoints.SETTINGS_ROBOT_CALIBRATION_GET,
            lambda data=None: self._handleGet("robot_calibration_settings")
        )

        self.register_handler(
            settings_endpoints.SETTINGS_ROBOT_CALIBRATION_SET,
            lambda data=None: self._handleSet("robot_calibration_settings", data)
        )

        self.register_handler(
            settings_endpoints.SETTINGS_CAMERA_GET,
            lambda data=None: self._handleGet("camera")
        )
        self.register_handler(
            settings_endpoints.SETTINGS_GET,
            lambda data=None: self._handleGet("general")
        )

        # ------------------------------
        # CORE SETTINGS - SET / UPDATE
        # ------------------------------
        self.register_handler(
            settings_endpoints.SETTINGS_ROBOT_SET,
            lambda data=None: self._handleSet("robot", data)
        )
        self.register_handler(
            settings_endpoints.SETTINGS_CAMERA_SET,
            lambda data=None: self._handleSet("camera", data)
        )
        self.register_handler(
            settings_endpoints.SETTINGS_UPDATE,
            lambda data=None: self._handleSet("general", data)
        )

        # ------------------------------
        # APPLICATION-SPECIFIC SETTINGS (dynamic)
        # ------------------------------
        def make_application_handler(ep):
            def handler(data=None):
                return self._handle_application_settings(ep, data)

            return handler

        for endpoint in self.settings_registry.get_all_endpoints():
            self.register_handler(endpoint, make_application_handler(endpoint))

    # Called at request time for dynamic endpoints
    def _resolve_dynamic_handler(self, request):
        endpoint_mapping = self.settings_registry.get_all_endpoints()
        if request not in endpoint_mapping:
            return None

        def handler(data):
            return self._handle_application_settings(request, data)

        return handler

    # =========================
    # INTERNAL HELPERS
    # =========================

    def _handle_application_settings(self, request, data=None):
        """
        Handle application-specific settings requests using the registry.
        """
        print(f"[_handle_application_settings] HANDLING request: {request} with data: {data}")

        try:
            # Re-add this line — you must fetch the mapping from the registry
            endpoint_mapping = self.settings_registry.get_all_endpoints()

            if request not in endpoint_mapping:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message=f"Unknown settings endpoint: {request}"
                ).to_dict()

            settings_type = endpoint_mapping[request]

            try:
                handler = self.settings_registry.get_handler(settings_type)
            except KeyError:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message=f"Settings handler not found for type: {settings_type}"
                ).to_dict()

            # Decide GET/SET by endpoint suffix
            if request.endswith("/get"):
                result_data = handler.handle_get_settings()
                return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Success", data=result_data).to_dict()
            elif request.endswith("/set"):
                if data is None:
                    return Response(Constants.RESPONSE_STATUS_ERROR, message="No data provided for setting").to_dict()
                success, message = handler.handle_set_settings(data)
                if success:
                    return Response(Constants.RESPONSE_STATUS_SUCCESS, message=message).to_dict()
                else:
                    return Response(Constants.RESPONSE_STATUS_ERROR, message=message).to_dict()
            else:
                return Response(Constants.RESPONSE_STATUS_ERROR, message="Unknown operation type").to_dict()

        except Exception as e:
            traceback.print_exc()
            return Response(Constants.RESPONSE_STATUS_ERROR,
                            message=f"Error handling application settings: {e}").to_dict()

    def _handleGet(self, resource):
        """
        Get settings for a given domain.
        """
        try:
            # Map lowercase resource names to proper constants
            resource_map = {
                "robot": Constants.REQUEST_RESOURCE_ROBOT,
                "camera": Constants.REQUEST_RESOURCE_CAMERA
            }
            
            # Use mapped resource if available, otherwise use as-is (for application settings)
            actual_resource = resource_map.get(resource, resource)
            
            data = self.settingsService.get_settings_by_resource(actual_resource)
            if data is not None:
                return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Success", data=data).to_dict()
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error getting {resource} settings").to_dict()
        except Exception as e:
            traceback.print_exc()
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error retrieving {resource} settings: {e}").to_dict()

    def _handleSet(self, resource, data):
        """
        Set/update settings for a given domain.
        """
        if data is None:
            # This is a GET request, nothing to update
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"No data provided for setting {resource} settings"
            ).to_dict()

        try:
            print(f"SettingsController._handleSet: resource={resource}, data={data}")
            
            # Handle robot calibration settings and camera settings using the new method
            if resource == "robot_calibration_settings":
                self.settingsService.update_settings("robot_calibration_settings", data)
            elif resource == "camera":
                # Use the clean repository approach for camera settings
                camera_data = {k: v for k, v in data.items() if k != 'header'}
                print(f"[SettingsController] Calling settingsService.update_settings('camera', {camera_data})")
                self.settingsService.update_settings("camera", camera_data)
                print(f"[SettingsController] Camera settings update completed")
            else:
                # Use legacy method for other settings that have headers
                self.settingsService.updateSettings(data)

            # After robot settings are saved, reload robot config to update in-memory settings
            if resource == "robot":
                try:
                    print(f"Robot settings updated, reloading robot configuration in memory...")
                    self.settingsService.reload_robot_config()
                    print(f"Robot configuration reloaded successfully")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"Warning: Failed to reload robot config after settings update: {e}")
                    # Don't fail the entire operation, just log the warning

            return Response(
                Constants.RESPONSE_STATUS_SUCCESS,
                message=f"{resource.capitalize()} settings saved successfully"
            ).to_dict()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error setting {resource} settings: {e}"
            ).to_dict()