"""
Dataclass models for glue cell monitoring state.

These dataclasses represent runtime state for real-time monitoring displays.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CellStatus(Enum):
    """Status of a glue cell"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    READY = "ready"
    UNKNOWN = "unknown"

    @property
    def color(self) -> str:
        """Get color for this status"""
        status_colors = {
            CellStatus.CONNECTED: "green",
            CellStatus.READY: "green",
            CellStatus.DISCONNECTED: "red",
            CellStatus.ERROR: "orange",
            CellStatus.UNKNOWN: "gray"
        }
        return status_colors.get(self, "gray")


@dataclass
class MonitoringState:
    """Real-time monitoring state for a glue cell"""
    cell_id: int
    current_weight: Optional[float] = None
    status: CellStatus = CellStatus.UNKNOWN
    last_update_timestamp: Optional[float] = None

    @property
    def is_connected(self) -> bool:
        """Check if cell is connected and operational"""
        return self.status in [CellStatus.CONNECTED, CellStatus.READY]

    @property
    def weight_display(self) -> str:
        """Get formatted weight for display"""
        if self.current_weight is None or not self.is_connected:
            return "-- g"
        return f"{self.current_weight:.2f} g"
