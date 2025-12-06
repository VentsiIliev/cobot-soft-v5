"""
Non-singleton cells manager implementation with proper dependency injection.
Replaces the singleton-based GlueCellsManager with a cleaner architecture.
"""
import json
from pathlib import Path
from typing import List, Optional

from modules.shared.tools.glue_monitor_system.interfaces import IGlueCellsManager, IGlueCell
from modules.shared.tools.glue_monitor_system.config_validator import GlueMonitorConfig
from modules.shared.tools.glue_monitor_system.glue_type import GlueType
from modules.shared.tools.glue_monitor_system.config import log_if_enabled
from modules.utils.custom_logging import LoggingLevel


class CellsManager(IGlueCellsManager):
    """
    Non-singleton cells manager with proper dependency injection.
    Manages multiple glue cells without using the singleton anti-pattern.
    """
    
    def __init__(self, cells: List[IGlueCell], config: GlueMonitorConfig, config_path: Path):
        """
        Initialize cells manager with dependency injection.
        
        Args:
            cells: List of glue cell instances
            config: Validated configuration object
            config_path: Path to configuration file for persistence
        """
        self.log_tag = "CellsManager"
        self.config = config
        self.config_path = config_path
        self._cells: List[IGlueCell] = []
        self.set_cells(cells)
    
    def get_cell_by_id(self, cell_id: int) -> Optional[IGlueCell]:
        """Get a cell by its ID."""
        for cell in self._cells:
            if cell.id == cell_id:
                return cell
        return None
    
    def get_all_cells(self) -> List[IGlueCell]:
        """Get all managed cells."""
        return self._cells.copy()
    
    def set_cells(self, cells: List[IGlueCell]) -> None:
        """
        Set the list of glue cells with validation.
        
        Args:
            cells: List of glue cell instances
            
        Raises:
            TypeError: If any item is not a valid glue cell
            ValueError: If there are duplicate IDs
        """
        if not all(hasattr(cell, 'id') and hasattr(cell, 'glue_type') for cell in cells):
            raise TypeError(f"[{self.log_tag}] All items must implement IGlueCell interface")

        # Check for duplicate IDs
        ids = [cell.id for cell in cells]
        if len(ids) != len(set(ids)):
            raise ValueError(f"[{self.log_tag}] Duplicate cell IDs found: {ids}")

        self._cells = cells

    def update_glue_type_by_id(self, cell_id: int, glue_type: GlueType) -> bool:
        """
        Update glue type for a specific cell and persist changes.

        Args:
            cell_id: ID of the cell to update
            glue_type: New glue type (enum or string)

        Returns:
            True if successful, False if cell not found
        """
        # Normalize glue type
        if isinstance(glue_type, str):
            try:
                glue_type = GlueType[glue_type]
            except KeyError:
                valid_types = [t.name for t in GlueType]
                log_if_enabled(LoggingLevel.ERROR,
                              f"Invalid glue type '{glue_type}'. Must be one of: {valid_types}")
                return False
        elif not isinstance(glue_type, GlueType):
            log_if_enabled(LoggingLevel.ERROR,
                          f"Invalid glue type '{glue_type}'. Must be GlueType enum or string")
            return False

        log_if_enabled(LoggingLevel.INFO, f"🔄 UPDATING GLUE TYPE: Cell {cell_id} → {glue_type}")

        # Find and update cell
        cell = self.get_cell_by_id(cell_id)
        if cell is None:
            log_if_enabled(LoggingLevel.ERROR, f"❌ CELL NOT FOUND: Cell {cell_id} does not exist")
            return False

        log_if_enabled(LoggingLevel.DEBUG,
                      f"Setting cell {cell_id} glue type from {cell.glue_type} to {glue_type}")

        try:
            cell.set_glue_type(glue_type)
        except Exception as e:
            log_if_enabled(LoggingLevel.ERROR, f"Failed to set glue type: {e}")
            return False

        # Persist changes to configuration file
        try:
            self._persist_glue_type_change(cell_id, glue_type)
            return True
        except Exception as e:
            log_if_enabled(LoggingLevel.ERROR, f"Failed to persist glue type change: {e}")
            # Try to revert the in-memory change
            try:
                # We don't have the old value, so we need to reload config
                self._reload_cell_config(cell_id)
            except Exception:
                log_if_enabled(LoggingLevel.ERROR, "Failed to revert glue type change")
            return False

    def poll_glue_data_by_id(self, cell_id: int) -> tuple[Optional[float], Optional[float]]:
        """
        Get weight and percentage for a specific cell.

        Args:
            cell_id: ID of the cell to poll

        Returns:
            Tuple of (weight, percentage) or (None, None) if cell not found
        """
        cell = self.get_cell_by_id(cell_id)
        if cell is None:
            return None, None

        try:
            weight = cell.get_weight()
            percentage = cell.get_percentage()
            return weight, percentage
        except Exception as e:
            log_if_enabled(LoggingLevel.ERROR, f"Error polling cell {cell_id}: {e}")
            return None, None

    def _persist_glue_type_change(self, cell_id: int, glue_type: GlueType) -> None:
        """
        Persist glue type change to configuration file.

        Args:
            cell_id: ID of the cell that was updated
            glue_type: New glue type
        """
        # Load current config from file
        with self.config_path.open("r") as f:
            config_data = json.load(f)

        # Update the specific cell
        updated = False
        for cell_data in config_data["cells"]:
            if cell_data["id"] == cell_id:
                cell_data["type"] = glue_type.name
                updated = True
                break

        if not updated:
            raise ValueError(f"Cell {cell_id} not found in configuration file")

        # Write back to file
        with self.config_path.open("w") as f:
            json.dump(config_data, f, indent=2)

        log_if_enabled(LoggingLevel.DEBUG,
                      f"Persisted glue type change for cell {cell_id} to {glue_type.name}")

    def _reload_cell_config(self, cell_id: int) -> None:
        """
        Reload configuration for a specific cell from disk.

        Args:
            cell_id: ID of the cell to reload
        """
        # This is a simplified version - in a full implementation,
        # we might want to reload the entire configuration and recreate cells
        log_if_enabled(LoggingLevel.WARNING,
                      f"Cell {cell_id} config reload not fully implemented")

    def __str__(self) -> str:
        """
        Return string representation of the cells manager.

        Returns:
            String representation
        """
        cell_count = len(self._cells)
        cell_ids = [cell.id for cell in self._cells]
        return f"CellsManager(cells={cell_count}, ids={cell_ids})"

    def __repr__(self) -> str:
        """Return detailed representation."""
        return self.__str__()
