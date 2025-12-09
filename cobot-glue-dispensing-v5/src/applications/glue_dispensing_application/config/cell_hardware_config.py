"""
Cell Hardware Configuration
Provides access to cell-to-motor hardware mapping via the handler / service layer.
This class acts as a convenience wrapper for accessing hardware configuration.
NOTE: This configuration is loaded via the service layer and persisted in application storage.
The configuration can be edited via UI (future feature).
"""
from typing import Dict, Optional
class CellHardwareConfig:
    """
    Cell hardware configuration accessor.
    Provides convenient methods to access cell-to-motor mapping via the service layer.
    Data is loaded from the service and cached for performance.
    """
    # Cache for hardware mapping to avoid repeated service calls
    _cached_mapping: Optional[Dict[int, int]] = None
    @classmethod
    def _load_config_from_service(cls) -> Dict[int, int]:
        """
        Load hardware configuration from the service layer.
        Returns:
            Dictionary mapping cell IDs to motor addresses
        """
        try:
            from applications.glue_dispensing_application.handlers.cell_hardware_handler import CellHardwareHandler
            handler = CellHardwareHandler()
            success, message, config = handler.handle_get_config()
            if success and config:
                mapping = config.get("cell_motor_mapping", {})
                if mapping:
                    cls._cached_mapping = mapping
                    return cls._cached_mapping
        except Exception as e:
            print(f"Error loading cell hardware config from service: {e}")
        # Fallback to default mapping if service fails
        return {1: 0, 2: 2, 3: 4, 4: 6}
    @classmethod
    def _get_mapping(cls) -> Dict[int, int]:
        """Get hardware mapping (from cache or service)."""
        if cls._cached_mapping is None:
            cls._cached_mapping = cls._load_config_from_service()
        return cls._cached_mapping
    @classmethod
    def reload_config(cls):
        """Force reload configuration from service."""
        cls._cached_mapping = None
        return cls._get_mapping()
    @classmethod
    def get_motor_address(cls, cell_id: int) -> int:
        """
        Get a motor modbus address for a cell.
        Args:
            cell_id: Physical cell ID (1-4)
        Returns:
            Motor modbus address
        Raises:
            ValueError: If cell ID is not configured
        """
        mapping = cls._get_mapping()
        if cell_id not in mapping:
            raise ValueError(f"Unknown cell ID: {cell_id}. Valid IDs: {list(mapping.keys())}")
        return mapping[cell_id]
    @classmethod
    def get_all_cell_ids(cls) -> list[int]:
        """
        Get all configured cell IDs.
        Returns:
            List of cell IDs
        """
        mapping = cls._get_mapping()
        return list(mapping.keys())
    @classmethod
    def get_cell_count(cls) -> int:
        """
        Get total number of configured cells.
        Returns:
            Number of cells
        """
        mapping = cls._get_mapping()
        return len(mapping)
    @classmethod
    def is_valid_cell_id(cls, cell_id: int) -> bool:
        """
        Check if a cell ID is valid.
        Args:
            cell_id: Cell ID to check
        Returns:
            True if valid, False otherwise
        """
        mapping = cls._get_mapping()
        return cell_id in mapping
    @classmethod
    def save_mapping(cls, mapping: Dict[int, int]) -> bool:
        """
        Save hardware mapping via the service layer.
        Args:
            mapping: New cell-to-motor mapping
        Returns:
            True if successful
        """
        try:
            from applications.glue_dispensing_application.handlers.cell_hardware_handler import CellHardwareHandler
            handler = CellHardwareHandler()
            request_data = {"cell_motor_mapping": mapping}
            success, message = handler.handle_set_config(request_data)
            if success:
                cls._cached_mapping = mapping  # Update cache
                return True
        except Exception as e:
            print(f"Error saving cell hardware config: {e}")
        return False
