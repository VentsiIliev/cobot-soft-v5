"""
Centralized styling constants for glue cell settings UI.

This eliminates the duplicate CSS that was scattered across the old implementation.
"""

# Weight display styling constants
WEIGHT_STYLE_NORMAL = """
    QLabel {
        font-size: 18px;
        font-weight: bold;
        color: #2E8B57;
        background-color: #F0F8F0;
        border: 2px solid #90EE90;
        border-radius: 8px;
        padding: 10px;
        min-height: 30px;
    }
"""

WEIGHT_STYLE_LOW = """
    QLabel {
        font-size: 18px;
        font-weight: bold;
        color: #B22222;
        background-color: #FFE4E1;
        border: 2px solid #FF6B6B;
        border-radius: 8px;
        padding: 10px;
        min-height: 30px;
    }
"""

WEIGHT_STYLE_HIGH = """
    QLabel {
        font-size: 18px;
        font-weight: bold;
        color: #FF8C00;
        background-color: #FFF8DC;
        border: 2px solid #FFD700;
        border-radius: 8px;
        padding: 10px;
        min-height: 30px;
    }
"""

WEIGHT_STYLE_DISCONNECTED = """
    QLabel {
        font-size: 18px;
        font-weight: bold;
        color: #696969;
        background-color: #F5F5F5;
        border: 2px solid #D3D3D3;
        border-radius: 8px;
        padding: 10px;
        min-height: 30px;
    }
"""

# Mode label styles
MODE_STYLE_PRODUCTION = "QLabel { font-weight: bold; color: #2E8B57; }"
MODE_STYLE_TEST = "QLabel { font-weight: bold; color: #FF8C00; }"

# Status label styles
STATUS_STYLE_CONNECTED = "QLabel { color: green; font-weight: bold; }"
STATUS_STYLE_DISCONNECTED = "QLabel { color: red; font-weight: bold; }"
STATUS_STYLE_ERROR = "QLabel { color: orange; font-weight: bold; }"
STATUS_STYLE_UNKNOWN = "QLabel { color: gray; font-weight: bold; }"


def get_weight_style(weight: float, min_threshold: float, max_threshold: float, is_connected: bool = True) -> str:
    """
    Get appropriate weight display style based on thresholds and connection status.

    Args:
        weight: Current weight value
        min_threshold: Minimum acceptable weight
        max_threshold: Maximum acceptable weight
        is_connected: Whether the cell is connected

    Returns:
        CSS string for the weight label
    """
    if not is_connected:
        return WEIGHT_STYLE_DISCONNECTED

    if weight < min_threshold:
        return WEIGHT_STYLE_LOW
    elif weight > max_threshold:
        return WEIGHT_STYLE_HIGH
    else:
        return WEIGHT_STYLE_NORMAL


def get_status_style(status: str) -> str:
    """
    Get status label style based on connection status.

    Args:
        status: Status string ("connected", "disconnected", "error", etc.)

    Returns:
        CSS string for the status label
    """
    status_lower = status.lower()

    if status_lower in ["connected", "ready"]:
        return STATUS_STYLE_CONNECTED
    elif status_lower in ["disconnected", "offline"]:
        return STATUS_STYLE_DISCONNECTED
    elif status_lower == "error":
        return STATUS_STYLE_ERROR
    else:
        return STATUS_STYLE_UNKNOWN


def get_mode_style(mode: str) -> str:
    """
    Get mode label style.

    Args:
        mode: Mode string ("production" or "test")

    Returns:
        CSS string for the mode label
    """
    return MODE_STYLE_PRODUCTION if mode == "production" else MODE_STYLE_TEST
