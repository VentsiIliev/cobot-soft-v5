"""
Cell Hardware Configuration Service
Business logic for managing cell-to-motor hardware mapping.
"""
from typing import Dict, List, Tuple, Optional
from applications.glue_dispensing_application.repositories.cell_hardware_repository import CellHardwareRepository
class CellHardwareService:
    """
    Service for cell hardware configuration operations.
    Provides business logic layer between API handlers and repository.
    """
    def __init__(self, repository: CellHardwareRepository):
        """
        Initialize service with repository.
        Args:
            repository: CellHardwareRepository instance
        """
        self.repository = repository
    def get_all_mapping(self) -> Dict[int, int]:
        """
        Get complete cell-to-motor mapping.
        Returns:
            Dictionary mapping cell IDs to motor addresses
        """
        return self.repository.get_cell_motor_mapping()
    def get_motor_address(self, cell_id: int) -> Tuple[bool, str, Optional[int]]:
        """
        Get motor address for a specific cell.
        Args:
            cell_id: Cell ID
        Returns:
            Tuple of (success, message, motor_address)
        """
        motor_address = self.repository.get_motor_address(cell_id)
        if motor_address is not None:
            return True, f"Motor address for cell {cell_id}: {motor_address}", motor_address
        else:
            return False, f"Cell {cell_id} not configured", None
    def get_all_cell_ids(self) -> List[int]:
        """
        Get list of all configured cell IDs.
        Returns:
            List of cell IDs
        """
        mapping = self.get_all_mapping()
        return list(mapping.keys())
    def update_mapping(self, mapping: Dict[int, int]) -> Tuple[bool, str]:
        """
        Update complete cell-to-motor mapping.
        Args:
            mapping: New mapping dictionary
        Returns:
            Tuple of (success, message)
        """
        # Validate mapping
        if not mapping:
            return False, "Mapping cannot be empty"
        # Validate all values are non-negative integers
        for cell_id, motor_addr in mapping.items():
            if not isinstance(cell_id, int) or cell_id < 1:
                return False, f"Invalid cell ID: {cell_id}"
            if not isinstance(motor_addr, int) or motor_addr < 0:
                return False, f"Invalid motor address: {motor_addr}"
        # Save to repository
        success = self.repository.save_cell_motor_mapping(mapping)
        if success:
            return True, f"Updated hardware mapping for {len(mapping)} cell(s)"
        else:
            return False, "Failed to save hardware mapping"
    def update_cell_motor_address(self, cell_id: int, motor_address: int) -> Tuple[bool, str]:
        """
        Update motor address for a single cell.
        Args:
            cell_id: Cell ID
            motor_address: New motor modbus address
        Returns:
            Tuple of (success, message)
        """
        # Validate inputs
        if not isinstance(cell_id, int) or cell_id < 1:
            return False, f"Invalid cell ID: {cell_id}"
        if not isinstance(motor_address, int) or motor_address < 0:
            return False, f"Invalid motor address: {motor_address}"
        # Update repository
        success = self.repository.update_motor_address(cell_id, motor_address)
        if success:
            return True, f"Updated cell {cell_id} motor address to {motor_address}"
        else:
            return False, f"Failed to update cell {cell_id} motor address"
    def validate_mapping(self, mapping: Dict[int, int]) -> Tuple[bool, str]:
        """
        Validate a hardware mapping configuration.
        Args:
            mapping: Mapping to validate
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not mapping:
            return False, "Mapping cannot be empty"
        # Check for duplicate motor addresses
        motor_addresses = list(mapping.values())
        if len(motor_addresses) != len(set(motor_addresses)):
            return False, "Duplicate motor addresses detected"
        # Validate cell IDs and motor addresses
        for cell_id, motor_addr in mapping.items():
            if not isinstance(cell_id, int) or cell_id < 1:
                return False, f"Invalid cell ID: {cell_id}"
            if not isinstance(motor_addr, int) or motor_addr < 0:
                return False, f"Invalid motor address for cell {cell_id}: {motor_addr}"
        return True, "Mapping is valid"
