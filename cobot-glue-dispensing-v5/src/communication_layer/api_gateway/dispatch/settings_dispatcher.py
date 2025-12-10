"""
Settings Handler - API Gateway

Handles all settings-related requests including robot, camera, and glue system configuration.
"""
from communication_layer.api.v1 import Constants
from communication_layer.api.v1.Response import Response
from communication_layer.api.v1.endpoints import glue_endpoints, settings_endpoints, modbus_endpoints
from communication_layer.api_gateway.interfaces.dispatch import IDispatcher
from applications.glue_dispensing_application.handlers.glue_types_handler import GlueTypesHandler
from applications.glue_dispensing_application.handlers.cell_hardware_handler import CellHardwareHandler


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
        self.glue_types_handler = GlueTypesHandler()
        self.cell_hardware_handler = CellHardwareHandler()

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
        # Glue types endpoints (NEW)
        if request in [glue_endpoints.GLUE_TYPES_GET,
                       glue_endpoints.GLUE_TYPE_ADD_CUSTOM,
                       glue_endpoints.GLUE_TYPES_SET,
                       glue_endpoints.GLUE_TYPE_REMOVE_CUSTOM]:
            return self.handle_glue_types(parts, request, data)
        elif request in [glue_endpoints.CELL_HARDWARE_CONFIG_GET,
                         glue_endpoints.CELL_HARDWARE_CONFIG_SET,
                         glue_endpoints.CELL_HARDWARE_MOTOR_ADDRESS_GET]:
            return self.handle_cell_hardware_config(parts, request, data)
        # Robot settings
        elif request in [settings_endpoints.SETTINGS_ROBOT_GET]:
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
        # Modbus settings
        elif request in [modbus_endpoints.MODBUS_CONFIG_GET, modbus_endpoints.MODBUS_CONFIG_UPDATE,
                         modbus_endpoints.MODBUS_TEST_CONNECTION, modbus_endpoints.MODBUS_GET_AVAILABLE_PORT]:
            return self.handle_modbus_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_GET]:
            return self.handle_general_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_UPDATE]:
            return self.handle_general_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_ROBOT_CALIBRATION_SET]:
            return self.handle_robot_calibration_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_ROBOT_CALIBRATION_GET]:
            return self.handle_robot_calibration_settings(parts, request, data)
        else:
            # Delegate to a settings controller which handles all the logic
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

        result = self.settingsController.handle(request, parts, data)
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
            from modules.shared.tools.glue_monitor_system.config.config import load_config
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

            elif request == glue_endpoints.GLUE_CELL_UPDATE:
                # Handle generic cell field updates (motor_address, url, capacity, etc.)
                if not data or 'cell_id' not in data or 'field' not in data or 'value' not in data:
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message="Missing required fields: cell_id, field, and value"
                    ).to_dict()

                try:
                    from pathlib import Path
                    import json

                    cell_id = data['cell_id']
                    field = data['field']
                    value = data['value']

                    # Load current config
                    config_path = Path(get_app_settings_path("glue_dispensing_application", "glue_cell_config"))

                    with open(config_path, 'r') as f:
                        config_data = json.load(f)

                    # Find and update the cell
                    cell_found = False
                    for cell_config in config_data.get("cells", []):
                        if cell_config["id"] == cell_id:
                            cell_config[field] = value
                            cell_found = True
                            print(f"Updated cell {cell_id} {field} to {value}")
                            break

                    if not cell_found:
                        return Response(
                            Constants.RESPONSE_STATUS_ERROR,
                            message=f"Cell {cell_id} not found"
                        ).to_dict()

                    # Save updated config
                    with open(config_path, 'w') as f:
                        json.dump(config_data, f, indent=2)

                    # Reload config in GlueCellsManager if needed
                    try:
                        cells_manager = get_service_factory().create_cells_manager()
                        if field == 'motor_address':
                            cell = cells_manager.getCellById(cell_id)
                            if cell:
                                cell.setMotorAddress(value)
                    except Exception as e:
                        print(f"Warning: Could not update GlueCellsManager: {e}")

                    return Response(
                        Constants.RESPONSE_STATUS_SUCCESS,
                        message=f"Cell {cell_id} {field} updated successfully"
                    ).to_dict()

                except Exception as e:
                    print(f"Error updating cell field: {e}")
                    import traceback
                    traceback.print_exc()
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=f"Error updating cell field: {e}"
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

    def handle_glue_types(self, parts, request, data=None):
        """
        Handle glue types management operations.

        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data

        Returns:
            dict: Response with glue types data or operation result
        """
        print(f"SettingsHandler: Handling glue types: {request} with data: {data}")

        try:
            if request == glue_endpoints.GLUE_TYPES_GET:
                # Get all glue types
                success, message, glue_types = self.glue_types_handler.handle_get_glue_types(data)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS if success else Constants.RESPONSE_STATUS_ERROR,
                    message=message,
                    data={"glue_types": glue_types}
                ).to_dict()

            elif request == glue_endpoints.GLUE_TYPE_ADD_CUSTOM:
                # Add new glue type
                success, message, glue_data = self.glue_types_handler.handle_add_glue_type(data)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS if success else Constants.RESPONSE_STATUS_ERROR,
                    message=message,
                    data={"glue": glue_data} if glue_data else None
                ).to_dict()

            elif request == glue_endpoints.GLUE_TYPES_SET:
                # Update existing glue type
                success, message = self.glue_types_handler.handle_update_glue_type(data)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS if success else Constants.RESPONSE_STATUS_ERROR,
                    message=message
                ).to_dict()

            elif request == glue_endpoints.GLUE_TYPE_REMOVE_CUSTOM:
                # Remove glue type
                success, message = self.glue_types_handler.handle_remove_glue_type(data)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS if success else Constants.RESPONSE_STATUS_ERROR,
                    message=message
                ).to_dict()

            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message=f"Unknown glue types request: {request}"
                ).to_dict()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"SettingsHandler: Error handling glue types: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error handling glue types: {e}"
            ).to_dict()

    def handle_cell_hardware_config(self, parts, request, data=None):
        """
        Handle cell hardware configuration operations.

        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data

        Returns:
            dict: Response with cell hardware config data or operation result
        """
        print(f"SettingsHandler: Handling cell hardware config: {request} with data: {data}")

        try:
            if request == glue_endpoints.CELL_HARDWARE_CONFIG_GET:
                # Get complete hardware configuration
                success, message, config = self.cell_hardware_handler.handle_get_config(data)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS if success else Constants.RESPONSE_STATUS_ERROR,
                    message=message,
                    data=config
                ).to_dict()

            elif request == glue_endpoints.CELL_HARDWARE_MOTOR_ADDRESS_GET:
                # Get motor address for specific cell
                success, message, response = self.cell_hardware_handler.handle_get_motor_address(data)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS if success else Constants.RESPONSE_STATUS_ERROR,
                    message=message,
                    data=response
                ).to_dict()

            elif request == glue_endpoints.CELL_HARDWARE_CONFIG_SET:
                # Update hardware configuration
                success, message = self.cell_hardware_handler.handle_set_config(data)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS if success else Constants.RESPONSE_STATUS_ERROR,
                    message=message
                ).to_dict()

            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message=f"Unknown cell hardware config request: {request}"
                ).to_dict()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"SettingsHandler: Error handling cell hardware config: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error handling cell hardware config: {e}"
            ).to_dict()

    def handle_modbus_settings(self, parts, request, data=None):
        """
        Handle Modbus configuration requests.

        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data

        Returns:
            dict: Response with Modbus configuration or operation result
        """
        try:
            from pathlib import Path
            from core.application.ApplicationStorageResolver import get_app_settings_path
            from core.database.settings.ModbusSettingsRepository import ModbusSettingsRepository

            print(f"handle_modbus_settings: Handling request: {request} with data: {data}")

            # Get application-specific config path and create repository
            config_path = Path(get_app_settings_path("glue_dispensing_application", "modbus_config"))
            modbus_repo = ModbusSettingsRepository(file_path=str(config_path))

            if request == modbus_endpoints.MODBUS_CONFIG_GET:
                # Load and return Modbus configuration
                try:
                    config = modbus_repo.load()
                    return Response(
                        Constants.RESPONSE_STATUS_SUCCESS,
                        data=config.to_dict()
                    ).to_dict()

                except Exception as e:
                    print(f"Error loading Modbus config: {e}")
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=f"Error loading Modbus configuration: {e}"
                    ).to_dict()

            elif request == modbus_endpoints.MODBUS_CONFIG_UPDATE:
                # Update Modbus configuration field
                if not data or 'field' not in data or 'value' not in data:
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message="Missing required fields: field and value"
                    ).to_dict()

                try:
                    field = data['field']
                    value = data['value']

                    modbus_repo.update_field(field, value)

                    print(f"Updated Modbus config: {field} = {value}")

                    return Response(
                        Constants.RESPONSE_STATUS_SUCCESS,
                        message=f"Modbus {field} updated successfully"
                    ).to_dict()

                except Exception as e:
                    print(f"Error updating Modbus config: {e}")
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=f"Error updating Modbus configuration: {e}"
                    ).to_dict()

            elif request == modbus_endpoints.MODBUS_TEST_CONNECTION:
                # Test Modbus connection
                try:
                    config = modbus_repo.load()

                    # Try to create a test connection
                    from modules.modbusCommunication.ModbusClient import ModbusClient
                    import minimalmodbus

                    parity_map = {
                        'N': minimalmodbus.serial.PARITY_NONE,
                        'E': minimalmodbus.serial.PARITY_EVEN,
                        'O': minimalmodbus.serial.PARITY_ODD,
                        'M': minimalmodbus.serial.PARITY_MARK,
                        'S': minimalmodbus.serial.PARITY_SPACE
                    }

                    test_client = ModbusClient(
                        slave=config.slave_address,
                        port=config.port,
                        baudrate=config.baudrate,
                        bytesize=config.bytesize,
                        stopbits=config.stopbits,
                        timeout=config.timeout,
                        parity=parity_map.get(config.parity, minimalmodbus.serial.PARITY_NONE),
                        max_retries=config.max_retries
                    )

                    # Close the test connection
                    if hasattr(test_client, 'client') and hasattr(test_client.client, 'serial'):
                        test_client.client.serial.close()

                    return Response(
                        Constants.RESPONSE_STATUS_SUCCESS,
                        message=f"Successfully connected to Modbus slave at {config.port}"
                    ).to_dict()

                except Exception as e:
                    print(f"Modbus connection test failed: {e}")
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=f"Connection test failed: {str(e)}"
                    ).to_dict()

            elif request == modbus_endpoints.MODBUS_GET_AVAILABLE_PORT:
                # Get available Modbus port
                try:
                    import platform
                    from modules.shared.utils.linuxUtils import get_modbus_port

                    SUDO_PASS = "plp"

                    if platform.system() == "Windows":
                        port = "COM5"
                    else:
                        port = get_modbus_port(sudo_password=SUDO_PASS)
                        if not port or port.strip() == "":
                            return Response(
                                Constants.RESPONSE_STATUS_ERROR,
                                message="No Modbus port detected. Please ensure the device is connected."
                            ).to_dict()

                    return Response(
                        Constants.RESPONSE_STATUS_SUCCESS,
                        data={"port": port},
                        message=f"Detected Modbus port: {port}"
                    ).to_dict()

                except Exception as e:
                    print(f"Error detecting Modbus port: {e}")
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=f"Error detecting port: {str(e)}"
                    ).to_dict()

            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message=f"Unknown Modbus request: {request}"
                ).to_dict()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"SettingsHandler: Error handling Modbus settings: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error handling Modbus settings: {e}"
            ).to_dict()
