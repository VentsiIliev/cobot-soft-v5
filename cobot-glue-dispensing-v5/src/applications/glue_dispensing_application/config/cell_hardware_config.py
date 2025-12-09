"""
Cell Hardware Configuration
Defines the PHYSICAL mapping between cell IDs and hardware addresses.
This is the ONLY place where hardware addresses are defined.
NOTE: In the future, this will be made configurable from the UI.
For now, it's hardcoded based on physical hardware setup.
"""
class CellHardwareConfig:
    """
    Immutable hardware configuration for glue cells.
    Maps physical cell IDs to their corresponding Modbus motor addresses.
    TODO: Make this configurable from UI instead of hardcoded.
    """
    # Physical cell to motor address mapping
    # TODO: Extract to settings/configuration file for UI editing
    CELL_MOTOR_MAPPING = {
        1: 0,  # Cell 1 → Motor at Modbus address 0
        2: 2,  # Cell 2 → Motor at Modbus address 2
        3: 4,  # Cell 3 → Motor at Modbus address 4
        4: 6,  # Cell 4 → Motor at Modbus address 6
    }
    @classmethod
    def get_motor_address(cls, cell_id: int) -> int:
        """
        Get motor modbus address for a cell.
        Args:
            cell_id: Physical cell ID (1-4)
        Returns:
            Motor modbus address
        Raises:
            ValueError: If cell ID is not configured
        """
        if cell_id not in cls.CELL_MOTOR_MAPPING:
            raise ValueError(f"Unknown cell ID: {cell_id}. Valid IDs: {list(cls.CELL_MOTOR_MAPPING.keys())}")
        return cls.CELL_MOTOR_MAPPING[cell_id]
    @classmethod
    def get_all_cell_ids(cls) -> list[int]:
        """
        Get all configured cell IDs.
        Returns:
            List of cell IDs
        """
        return list(cls.CELL_MOTOR_MAPPING.keys())
    @classmethod
    def get_cell_count(cls) -> int:
        """
        Get total number of configured cells.
        Returns:
            Number of cells
        """
        return len(cls.CELL_MOTOR_MAPPING)
    @classmethod
    def is_valid_cell_id(cls, cell_id: int) -> bool:
        """
        Check if a cell ID is valid.
        Args:
            cell_id: Cell ID to check
        Returns:
            True if valid, False otherwise
        """
        return cell_id in cls.CELL_MOTOR_MAPPING
