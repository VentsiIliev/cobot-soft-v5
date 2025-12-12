"""
Validation helpers for glue cell settings.

These are pure functions with no business logic - actual validation decisions
happen in SettingsAppWidget which has access to all cell configs.
"""

from typing import Tuple


def parse_ip_from_url(url: str) -> str:
    """
    Extract IP address from URL.

    Args:
        url: URL string (e.g., "http://192.168.222.143/weight1")

    Returns:
        Extracted IP address or error message
    """
    try:
        if "://" in url:
            url_part = url.split("://")[1]
            if "/" in url_part:
                return url_part.split("/")[0]
            return url_part
        return "Invalid URL"
    except Exception:
        return "Error parsing URL"


def parse_glue_cell_key(key: str) -> Tuple[int, str]:
    """
    Parse legacy glue cell setting key into cell_id and field name.

    Args:
        key: Legacy key format (e.g., "load_cell_1_zero_offset")

    Returns:
        Tuple of (cell_id, field_name)

    Raises:
        ValueError: If key format is invalid
    """
    if not key.startswith("load_cell_"):
        raise ValueError(f"Invalid key format: {key}")

    parts = key.replace("load_cell_", "").split("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid key format: {key}")

    try:
        cell_id = int(parts[0])
        field_name = parts[1]
        return cell_id, field_name
    except ValueError as e:
        raise ValueError(f"Invalid cell ID in key: {key}") from e


def get_field_section_mapping() -> dict:
    """
    Get mapping of field names to their sections.

    Returns:
        Dict mapping field names to section names
    """
    return {
        # Connection fields
        "glue_type": "connection",
        "motor_address": "connection",
        "capacity": "connection",
        "url": "connection",
        "fetch_timeout": "connection",

        # Calibration fields
        "zero_offset": "calibration",
        "scale_factor": "calibration",
        "temperature_compensation": "calibration",

        # Measurement fields
        "sampling_rate": "measurement",
        "filter_cutoff": "measurement",
        "averaging_samples": "measurement",
        "min_weight_threshold": "measurement",
        "max_weight_threshold": "measurement",
    }


def is_valid_motor_address(address: int) -> bool:
    """
    Check if motor address is in valid range.

    Args:
        address: Motor address to validate

    Returns:
        True if valid (0-10, even numbers only)
    """
    return address in [0, 2, 4, 6, 8, 10]


def format_weight_display(weight: float | None, is_connected: bool = True) -> str:
    """
    Format weight for display.

    Args:
        weight: Weight value or None
        is_connected: Whether cell is connected

    Returns:
        Formatted string for display
    """
    if weight is None or not is_connected:
        return "-- g"
    return f"{weight:.2f} g"
