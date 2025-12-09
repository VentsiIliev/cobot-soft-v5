"""
Cell Hardware Configuration Handler
Handles API requests for cell hardware configuration operations.
"""
from typing import Tuple, Dict, Any
from applications.glue_dispensing_application.services.cell_hardware_service import CellHardwareService
from applications.glue_dispensing_application.repositories.cell_hardware_repository import CellHardwareRepository
from core.application.ApplicationStorageResolver import get_app_settings_path
class CellHardwareHandler:
    """
    Handler for cell hardware configuration API requests.
    Translates API requests into service calls and formats responses.
    """
    def __init__(self):
        """Initialize handler with service instance."""
        # Get file path using ApplicationStorageResolver
        file_path = get_app_settings_path("glue_dispensing_application", "cell_hardware_config.json")
        repository = CellHardwareRepository(file_path)
        self.service = CellHardwareService(repository)
        self.repository = repository
    def handle_get_config(self, data: Dict[str, Any] = None) -> Tuple[bool, str, Dict]:
        """
        Get complete cell hardware configuration.
        Args:
            data: Request data (not used for GET operation)
        Returns:
            Tuple of (success: bool, message: str, config: Dict)
        """
        mapping = self.service.get_all_mapping()
        response = {
            "cell_motor_mapping": mapping,
            "cell_ids": list(mapping.keys()),
            "motor_addresses": list(mapping.values())
        }
        return True, f"Retrieved hardware config for {len(mapping)} cell(s)", response
    def handle_get_motor_address(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict]:
        """
        Get motor address for a specific cell.
        Args:
            data: Dictionary containing:
                - cell_id (int): Cell ID (required)
        Returns:
            Tuple of (success: bool, message: str, response: Dict)
        """
        cell_id = data.get("cell_id")
        if cell_id is None:
            return False, "cell_id is required", {}
        try:
            cell_id = int(cell_id)
        except (ValueError, TypeError):
            return False, f"Invalid cell_id: {cell_id}", {}
        success, message, motor_address = self.service.get_motor_address(cell_id)
        response = {
            "cell_id": cell_id,
            "motor_address": motor_address
        }
        return success, message, response
    def handle_set_config(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update complete cell hardware configuration.
        Args:
            data: Dictionary containing:
                - cell_motor_mapping (Dict[str|int, int]): Complete mapping (required)
        Returns:
            Tuple of (success: bool, message: str)
        """
        raw_mapping = data.get("cell_motor_mapping")
        if raw_mapping is None:
            return False, "cell_motor_mapping is required"
        # Convert string keys to integers
        try:
            mapping = {int(k): int(v) for k, v in raw_mapping.items()}
        except (ValueError, TypeError, AttributeError) as e:
            return False, f"Invalid mapping format: {e}"
        # Validate before saving
        is_valid, validation_msg = self.service.validate_mapping(mapping)
        if not is_valid:
            return False, f"Invalid mapping: {validation_msg}"
        # Update via service
        return self.service.update_mapping(mapping)
    def handle_update_cell_motor(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update motor address for a single cell.
        Args:
            data: Dictionary containing:
                - cell_id (int): Cell ID (required)
                - motor_address (int): New motor address (required)
        Returns:
            Tuple of (success: bool, message: str)
        """
        cell_id = data.get("cell_id")
        motor_address = data.get("motor_address")
        if cell_id is None:
            return False, "cell_id is required"
        if motor_address is None:
            return False, "motor_address is required"
        try:
            cell_id = int(cell_id)
            motor_address = int(motor_address)
        except (ValueError, TypeError):
            return False, "cell_id and motor_address must be integers"
        return self.service.update_cell_motor_address(cell_id, motor_address)
