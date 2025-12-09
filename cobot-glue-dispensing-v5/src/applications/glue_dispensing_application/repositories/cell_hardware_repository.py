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
            file_path: Path to cell_hardware_config.json file
        """
        self.file_path = Path(file_path)
        self._ensure_file_exists()
    def _ensure_file_exists(self):
        """Create file with default configuration if it doesn't exist."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_default_config()
    def _save_default_config(self):
        """Save default hardware configuration."""
        default_config = {
            "version": "1.0",
            "description": "Physical mapping between cell IDs and motor modbus addresses",
            "cell_motor_mapping": {
                "1": 0,
                "2": 2,
                "3": 4,
                "4": 6
            },
            "notes": "This configuration can be edited via UI. Cell ID -> Motor Modbus Address mapping."
        }
        self._save_config(default_config)
    def _save_config(self, config: Dict):
        """Save configuration to file."""
        with open(self.file_path, 'w') as f:
            json.dump(config, f, indent=2)
    def load_config(self) -> Dict:
        """
        Load hardware configuration from file.
        Returns:
            Dictionary containing full configuration
        """
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading cell hardware config: {e}, using defaults")
            self._save_default_config()
            return self.load_config()
    def get_cell_motor_mapping(self) -> Dict[int, int]:
        """
        Get cell-to-motor address mapping.
        Returns:
            Dictionary mapping cell IDs (int) to motor addresses (int)
        """
        config = self.load_config()
        raw_mapping = config.get("cell_motor_mapping", {})
        # Convert string keys to integers
        return {int(k): v for k, v in raw_mapping.items()}
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
        Save updated cell-to-motor mapping.
        Args:
            mapping: Dictionary mapping cell IDs to motor addresses
        Returns:
            True if successful
        """
        try:
            config = self.load_config()
            # Convert integer keys to strings for JSON
            config["cell_motor_mapping"] = {str(k): v for k, v in mapping.items()}
            self._save_config(config)
            return True
        except Exception as e:
            print(f"Error saving cell hardware config: {e}")
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
