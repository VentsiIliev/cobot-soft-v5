"""
Shared cell configuration models for glue monitor system.

These models can be safely imported by both backend and UI layers.
All models are immutable (frozen=True) to prevent accidental mutations.
"""
from dataclasses import dataclass
from typing import List, Optional
from modules.shared.tools.glue_monitor_system.glue_type import GlueType


@dataclass(frozen=True)
class CalibrationConfig:
    """Calibration configuration for a cell - all fields required."""
    zero_offset: float
    scale_factor: float
    temperature_compensation: bool


@dataclass(frozen=True)
class MeasurementConfig:
    """Measurement configuration for a cell - all fields required."""
    sampling_rate: int
    filter_cutoff: float
    averaging_samples: int
    min_weight_threshold: float
    max_weight_threshold: float


@dataclass(frozen=True)
class CellConfig:
    """Individual cell configuration - all fields required."""
    id: int
    type: GlueType
    url: str
    capacity: float
    fetch_timeout: int
    calibration: CalibrationConfig
    measurement: MeasurementConfig


@dataclass(frozen=True)
class GlueCellsConfig:
    """Collection of glue cell configurations."""
    cells: List[CellConfig]
    
    def get_cell_by_id(self, cell_id: int) -> Optional[CellConfig]:
        """Get a cell configuration by its ID."""
        return next((cell for cell in self.cells if cell.id == cell_id), None)
    
    def get_all_cell_ids(self) -> List[int]:
        """Get list of all cell IDs."""
        return [cell.id for cell in self.cells]
    
    def get_cells_by_type(self, glue_type: GlueType) -> List[CellConfig]:
        """Get all cells of a specific glue type."""
        return [cell for cell in self.cells if cell.type == glue_type]
    
    @property
    def cell_count(self) -> int:
        """Get total number of cells."""
        return len(self.cells)