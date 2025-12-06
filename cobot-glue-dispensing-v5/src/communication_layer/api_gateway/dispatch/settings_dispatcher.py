"""
Settings Handler - API Gateway

Handles all settings-related requests including robot, camera, and glue system configuration.
"""
from communication_layer.api.v1 import Constants
from communication_layer.api.v1.Response import Response
from communication_layer.api.v1.endpoints import glue_endpoints, settings_endpoints
from communication_layer.api_gateway.interfaces.dispatch import IDispatcher


class SettingsDispatch(IDispatcher):
    """
    Handles settings operations for the API gateway.
    
    This handler manages configuration for robot, camera, glue system, and general settings.
    """
    
    def __init__(self, settingsController):
        """
        Initialize the SettingsHandler.
        
        Args:
            settingsController: Settings controller instance
        """
        self.settingsController = settingsController
    
    def dispatch(self, parts: list, request: str, data: dict = None) -> dict:
        """
        Route settings requests to appropriate handlers.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response dictionary with operation result
        """
        print(f"SettingsDispatch: Handling request: {request} with parts: {parts} and data: {data}")
        
        # Handle both new RESTful endpoints and legacy endpoints
        # Robot settings
        if request in [settings_endpoints.SETTINGS_ROBOT_GET]:
            return self.handle_robot_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_ROBOT_SET]:
            return self.handle_robot_settings(parts, request, data)
        # Camera settings
        elif request in [settings_endpoints.SETTINGS_CAMERA_GET]:
            return self.handle_camera_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_CAMERA_SET]:
            return self.handle_camera_settings(parts, request, data)
        elif request in [glue_endpoints.SETTINGS_GLUE_GET]:
            return self.handle_glue_settings(parts, request, data)
        elif request in [glue_endpoints.SETTINGS_GLUE_SET]:
            return self.handle_glue_settings(parts, request, data)
        # Glue cells settings
        elif request in [glue_endpoints.GLUE_CELLS_CONFIG_GET]:
            return self.handle_glue_cells_settings(parts, request, data)
        elif request in [glue_endpoints.GLUE_CELLS_CONFIG_SET, glue_endpoints.GLUE_CELL_UPDATE, 
                        glue_endpoints.GLUE_CELL_CALIBRATE, glue_endpoints.GLUE_CELL_TARE, 
                        glue_endpoints.GLUE_CELL_UPDATE_TYPE]:
            return self.handle_glue_cells_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_GET]:
            return self.handle_general_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_UPDATE]:
            return self.handle_general_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_ROBOT_CALIBRATION_SET]:
            return self.handle_robot_calibration_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_ROBOT_CALIBRATION_GET]:
            return self.handle_robot_calibration_settings(parts, request, data)
        else:
            # Delegate to settings controller which handles all the logic
            return self.settingsController.handle(request, parts, data)

    def handle_robot_calibration_settings(self, parts, request, data=None):
        """
        Handle robot calibration settings operations.

        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data

        Returns:
            dict: Response with robot calibration settings data or operation result
        """
        print(f"SettingsHandler: Handling robot calibration settings: {request} with data: {data}")

        result =  self.settingsController.handle(request, parts, data)
        print(f"[SettingsHandler]: Robot calibration settings response: {result}")
        return result
    def handle_robot_settings(self, parts, request, data=None):
        """
        Handle robot-specific settings operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with robot settings data or operation result
        """
        print(f"SettingsHandler: Handling robot settings: {request} with data: {data}")
        
        return self.settingsController.handle(request, parts, data)
    
    def handle_camera_settings(self, parts, request, data=None):
        """
        Handle camera-specific settings operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with camera settings data or operation result
        """
        print(f"SettingsHandler: Handling camera settings: {request}")
        print(f"SettingsHandler: Data received: {data}")
        print(f"SettingsHandler: Data type: {type(data)}")
        
        return self.settingsController.handle(request, parts, data)
    
    def handle_glue_settings(self, parts, request, data=None):
        """
        Handle glue system settings operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with glue settings data or operation result
        """

        try:
            print(f"handle_glue_settings: Handling glue settings: {request} with data: {data}")
            response = self.settingsController.handle(request, parts, data)
            print(f"SettingsHandler: Glue settings response: {response}")
            return response
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"SettingsHandler: Error handling glue settings: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error handling glue settings: {e}"
            ).to_dict()
    
    def handle_glue_cells_settings(self, parts, request, data=None):
        """
        Handle glue cells configuration operations using shared models and DTOs.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with glue cells data or operation result
        """
        try:
            from modules.shared.tools.glue_monitor_system.models.dto import GlueCellsResponseDTO, CellUpdateRequestDTO
            from modules.shared.tools.glue_monitor_system.config import load_config
            from modules.shared.tools.glue_monitor_system.service_factory import get_service_factory
            from pathlib import Path
            from core.application.ApplicationStorageResolver import get_app_settings_path
            
            print(f"handle_glue_cells_settings: Handling request: {request} with data: {data}")
            
            if request == glue_endpoints.GLUE_CELLS_CONFIG_GET:
                # Load configuration and convert to DTO
                try:
                    config_path = Path(get_app_settings_path("glue_dispensing_application", "glue_cell_config"))
                    config = load_config(config_path)
                    
                    # Convert to response DTO
                    response_dto = GlueCellsResponseDTO.from_cell_configs(
                        environment=config.environment,
                        server_url=config.server.base_url,
                        cell_configs=config.cells
                    )
                    
                    return Response(
                        Constants.RESPONSE_STATUS_SUCCESS,
                        data=response_dto.to_dict()
                    ).to_dict()
                    
                except Exception as e:
                    print(f"Error loading glue cells config: {e}")
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=f"Error loading glue cells configuration: {e}"
                    ).to_dict()
            
            elif request == glue_endpoints.GLUE_CELL_UPDATE_TYPE:
                # Handle glue type updates
                if not data or 'cell_id' not in data or 'type' not in data:
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message="Missing required fields: cell_id and type"
                    ).to_dict()
                
                try:
                    cells_manager = get_service_factory().create_cells_manager()
                    result = cells_manager.update_glue_type_by_id(
                        cell_id=data['cell_id'],
                        glue_type=data['type']
                    )
                    
                    return Response(
                        Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR,
                        message="Glue type updated successfully" if result else "Failed to update glue type"
                    ).to_dict()
                    
                except Exception as e:
                    print(f"Error updating glue type: {e}")
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=f"Error updating glue type: {e}"
                    ).to_dict()
            
            else:
                # For other operations, delegate to settings controller for now
                return self.settingsController.handle(request, parts, data)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"SettingsHandler: Error handling glue cells settings: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error handling glue cells settings: {e}"
            ).to_dict()
    
    def handle_general_settings(self, parts, request, data=None):
        """
        Handle general system settings operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with general settings data or operation result
        """
        print(f"SettingsHandler: Handling general settings: {request}")
        
        return self.settingsController.handle(request, parts, data)
    
    def handle_settings_get(self, domain=None):
        """
        Handle settings retrieval operations.
        
        Args:
            domain (str): Settings domain (robot, camera, glue, or None for all)
            
        Returns:
            dict: Response with settings data
        """
        print(f"SettingsHandler: Handling settings get for domain: {domain}")
        
        try:
            if domain:
                # Domain-specific settings
                request = f"settings/{domain}/get"
            else:
                # All settings
                request = "settings/get"
            
            return self.settingsController.handle(request, [], None)
            
        except Exception as e:
            print(f"SettingsHandler: Error getting settings: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error getting settings: {e}"
            ).to_dict()
    
    def handle_settings_set(self, domain, data):
        """
        Handle settings update operations.
        
        Args:
            domain (str): Settings domain (robot, camera, glue)
            data (dict): Settings data to update
            
        Returns:
            dict: Response indicating success or failure
        """
        print(f"SettingsHandler: Handling settings set for domain: {domain}")
        
        try:
            request = f"settings/{domain}/set"
            return self.settingsController.handle(request, [], data)
            
        except Exception as e:
            print(f"SettingsHandler: Error setting settings: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error setting settings: {e}"
            ).to_dict()