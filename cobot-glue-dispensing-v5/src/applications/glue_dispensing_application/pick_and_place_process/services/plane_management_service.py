from typing import Optional
from ..models import PlaneState, RowOverflowResult


class PlaneManagementService:
    """Service for managing placement plane state and operations."""
    
    def __init__(self, plane):
        self.plane = plane
        self._previous_tallest = 0.0
    
    def update_height_tracking(self, height: float) -> float:
        """
        Update the tallest contour for row spacing.
        
        Args:
            height: Height of current workpiece
            
        Returns:
            Previous tallest height
        """
        self._previous_tallest = self.plane.tallestContour
        if height > self.plane.tallestContour:
            self.plane.tallestContour = height
        return self._previous_tallest
    
    def handle_row_overflow(self, width: float, height: float, 
                          target_x: float, target_y: float) -> RowOverflowResult:
        """
        Handle row overflow logic and move to next row if needed.
        
        Args:
            width: Workpiece width
            height: Workpiece height  
            target_x: Current target X position
            target_y: Current target Y position
            
        Returns:
            RowOverflowResult with updated positions and status
        """
        if target_x + (width / 2) > self.plane.xMax:
            # Move to next row
            self.plane.rowCount += 1
            self.plane.xOffset = 0
            self.plane.yOffset += self.plane.tallestContour + 50
            new_target_x = self.plane.xMin + (width / 2)
            new_target_y = self.plane.yMax - self.plane.yOffset
            self.plane.tallestContour = height  # Reset for new row
            
            # Check vertical bounds
            if new_target_y - (height / 2) < self.plane.yMin:
                self.plane.isFull = True
                return RowOverflowResult(
                    new_target_x=new_target_x,
                    new_target_y=new_target_y,
                    overflow_occurred=True,
                    plane_full=True
                )
            
            return RowOverflowResult(
                new_target_x=new_target_x,
                new_target_y=new_target_y,
                overflow_occurred=True,
                plane_full=False
            )
        
        return RowOverflowResult(
            new_target_x=target_x,
            new_target_y=target_y,
            overflow_occurred=False,
            plane_full=False
        )
    
    def update_for_next_placement(self, width: float) -> None:
        """
        Update plane state for next workpiece placement.
        
        Args:
            width: Width of the placed workpiece
        """
        self.plane.xOffset += width + self.plane.spacing
    
    def is_plane_full(self) -> bool:
        """Check if plane is full."""
        return self.plane.isFull
    
    def get_plane_state(self) -> dict:
        """Get current plane state information."""
        return {
            'row_count': self.plane.rowCount,
            'x_offset': self.plane.xOffset,
            'y_offset': self.plane.yOffset,
            'tallest_contour': self.plane.tallestContour,
            'is_full': self.plane.isFull
        }