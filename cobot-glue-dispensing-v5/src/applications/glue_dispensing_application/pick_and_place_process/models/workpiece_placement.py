from dataclasses import dataclass
from typing import List, Optional, Tuple
from .robot_positions import PickupPositions, DropOffPositions


@dataclass
class WorkpieceDimensions:
    """Dimensions and bounding information for a workpiece."""
    width: float
    height: float
    bbox_center: Tuple[float, float]
    min_rect: Tuple  # OpenCV minAreaRect result


@dataclass
class PlacementTarget:
    """Target position for workpiece placement."""
    x: float
    y: float
    
    
@dataclass
class WorkpiecePlacement:
    """Complete placement information for a workpiece."""
    dimensions: WorkpieceDimensions
    target_position: PlacementTarget
    pickup_positions: PickupPositions
    drop_off_positions: DropOffPositions
    pickup_height: float
    contour: Optional[List]  # Placed contour
    translation: Tuple[float, float]  # Translation applied to contour


@dataclass
class PlacementResult:
    """Result of a workpiece placement operation."""
    success: bool
    placement: Optional[WorkpiecePlacement]
    plane_full: bool
    message: str