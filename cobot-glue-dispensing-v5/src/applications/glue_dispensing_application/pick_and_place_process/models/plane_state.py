from dataclasses import dataclass


@dataclass 
class PlaneState:
    """Represents the current state of the placement plane."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    x_offset: float
    y_offset: float
    tallest_contour: float
    row_count: int
    spacing: float
    is_full: bool

    @classmethod
    def create_default(cls) -> 'PlaneState':
        """Create a plane state with default values."""
        return cls(
            x_min=0.0,
            x_max=1000.0,
            y_min=0.0,
            y_max=1000.0,
            x_offset=0.0,
            y_offset=0.0,
            tallest_contour=0.0,
            row_count=0,
            spacing=10.0,
            is_full=False
        )


@dataclass
class RowOverflowResult:
    """Result of row overflow check and handling."""
    new_target_x: float
    new_target_y: float
    overflow_occurred: bool
    plane_full: bool