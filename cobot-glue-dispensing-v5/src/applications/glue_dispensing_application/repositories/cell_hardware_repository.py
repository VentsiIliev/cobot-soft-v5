"""
Cell Hardware Configuration Repository
Handles persistence of cell-to-motor hardware mapping configuration.
"""
import json
from pathlib import Path
from typing import Dict, Optional
class CellHardwareRepository:
    """
    Repository for cell hardware configuration.
    Stores and retrieves the mapping between cell IDs and motor modbus addresses.
    """
    def __init__(self, file_path: str):
        """
        Initialize repository with file path.
        Args:
            file_path: Path to glue_cell_config.json file
        """
        self.file_path = Path(file_path)
        self._ensure_file_exists()
    def _ensure_file_exists(self):
        """Ensure file exists - glue_cell_config.json should already exist."""
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"glue_cell_config.json not found at {self.file_path}. "
                f"This file should exist and contain the main glue cell configuration."
            )
    def load_config(self) -> Dict:
        """
        Load glue cell configuration from file.
        Returns:
            Dictionary containing full glue cell configuration
        """
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Error loading glue cell config from {self.file_path}: {e}")
    def get_cell_motor_mapping(self) -> Dict[int, int]:
        """
        Get cell-to-motor address mapping from cells array.
        Returns:
            Dictionary mapping cell IDs (int) to motor addresses (int)
        """
        config = self.load_config()
        mapping = {}

        # Extract motor_address from each cell in the cells array
        for cell in config.get('cells', []):
            cell_id = cell.get('id')
            motor_address = cell.get('motor_address')

            if cell_id is not None and motor_address is not None:
                mapping[cell_id] = motor_address

        return mapping
    def get_motor_address(self, cell_id: int) -> Optional[int]:
        """
        Get motor address for a specific cell.
        Args:
            cell_id: Cell ID
        Returns:
            Motor modbus address or None if not found
        """
        mapping = self.get_cell_motor_mapping()
        return mapping.get(cell_id)
    def save_cell_motor_mapping(self, mapping: Dict[int, int]) -> bool:
        """
        Save updated cell-to-motor mapping by updating motor_address in cells array.
        Args:
            mapping: Dictionary mapping cell IDs to motor addresses
        Returns:
            True if successful
        """
        try:
            config = self.load_config()

            # Update motor_address for each cell in the cells array
            for cell in config.get('cells', []):
                cell_id = cell.get('id')
                if cell_id in mapping:
                    cell['motor_address'] = mapping[cell_id]

            # Save updated config
            with open(self.file_path, 'w') as f:
                json.dump(config, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving cell motor mapping: {e}")
            return False
    def update_motor_address(self, cell_id: int, motor_address: int) -> bool:
        """
        Update motor address for a specific cell.
        Args:
            cell_id: Cell ID
            motor_address: New motor modbus address
        Returns:
            True if successful
        """
        mapping = self.get_cell_motor_mapping()
        mapping[cell_id] = motor_address
        return self.save_cell_motor_mapping(mapping)
