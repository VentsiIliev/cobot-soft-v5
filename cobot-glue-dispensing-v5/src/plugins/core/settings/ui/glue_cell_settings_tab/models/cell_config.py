"""
Dataclass models for glue cell configuration.

These dataclasses provide type-safe representations of glue cell settings,
following the centralized data access pattern where UI components are "dumb"
and all business logic lives in SettingsAppWidget.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ConnectionSettings:
    """Connection and hardware settings for a glue cell"""
    glue_type: str
    motor_address: int
    capacity: int
    url: str
    fetch_timeout: int
    mode: str = "production"  # "production" or "test"

    @property
    def ip_address(self) -> str:
        """Extract IP address from URL"""
        try:
            if "://" in self.url:
                url_part = self.url.split("://")[1]
                if "/" in url_part:
                    return url_part.split("/")[0]
                return url_part
            return "Invalid URL"
        except Exception:
            return "Error parsing URL"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API communication"""
        return {
            "type": self.glue_type,
            "motor_address": self.motor_address,
            "capacity": self.capacity,
            "url": self.url,
            "fetch_timeout": self.fetch_timeout
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionSettings':
        """Create from dictionary (API response)"""
        return cls(
            glue_type=data.get('type', ''),
            motor_address=data.get('motor_address', 0),
            capacity=int(data.get('capacity', 1000)),
            url=data.get('url', ''),
            fetch_timeout=data.get('fetch_timeout', 5),
            mode=data.get('mode', 'production')
        )


@dataclass
class CalibrationSettings:
    """Calibration parameters for a glue cell"""
    zero_offset: float
    scale_factor: float
    temperature_compensation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API communication"""
        return {
            "zero_offset": self.zero_offset,
            "scale_factor": self.scale_factor,
            "temperature_compensation": self.temperature_compensation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationSettings':
        """Create from dictionary (API response)"""
        return cls(
            zero_offset=float(data.get('zero_offset', 0.0)),
            scale_factor=float(data.get('scale_factor', 1.0)),
            temperature_compensation=data.get('temperature_compensation', False)
        )


@dataclass
class MeasurementSettings:
    """Measurement and filtering settings"""
    sampling_rate: int
    filter_cutoff: float
    averaging_samples: int
    min_weight_threshold: float
    max_weight_threshold: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API communication"""
        return {
            "sampling_rate": self.sampling_rate,
            "filter_cutoff": self.filter_cutoff,
            "averaging_samples": self.averaging_samples,
            "min_weight_threshold": self.min_weight_threshold,
            "max_weight_threshold": self.max_weight_threshold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeasurementSettings':
        """Create from dictionary (API response)"""
        return cls(
            sampling_rate=int(data.get('sampling_rate', 10)),
            filter_cutoff=float(data.get('filter_cutoff', 5.0)),
            averaging_samples=int(data.get('averaging_samples', 5)),
            min_weight_threshold=float(data.get('min_weight_threshold', 0.1)),
            max_weight_threshold=float(data.get('max_weight_threshold', 1000.0))
        )


@dataclass
class CellConfig:
    """Complete configuration for a glue cell"""
    cell_id: int
    connection: ConnectionSettings
    calibration: CalibrationSettings
    measurement: MeasurementSettings

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API communication"""
        return {
            "id": self.cell_id,
            "type": self.connection.glue_type,
            "motor_address": self.connection.motor_address,
            "capacity": self.connection.capacity,
            "url": self.connection.url,
            "fetch_timeout": self.connection.fetch_timeout,
            "calibration": self.calibration.to_dict(),
            "measurement": self.measurement.to_dict()
        }

    @classmethod
    def from_dto(cls, cell_dto: Dict[str, Any]) -> 'CellConfig':
        """
        Create from DTO format (API response).

        Expected format:
        {
            'id': 1,
            'type': 'TypeA',
            'motor_address': 0,
            'capacity': 10000,
            'url': 'http://192.168.222.143/weight1',
            'fetch_timeout': 5,
            'calibration': {'zero_offset': 0.0, 'scale_factor': 1.0, ...},
            'measurement': {'sampling_rate': 10, 'filter_cutoff': 5.0, ...}
        }
        """
        # Build connection settings from top-level fields
        connection = ConnectionSettings(
            glue_type=cell_dto.get('type', ''),
            motor_address=cell_dto.get('motor_address', 0),
            capacity=int(cell_dto.get('capacity', 1000)),
            url=cell_dto.get('url', ''),
            fetch_timeout=cell_dto.get('fetch_timeout', 5),
            mode=cell_dto.get('mode', 'production')
        )

        # Parse nested calibration and measurement
        calibration = CalibrationSettings.from_dict(cell_dto.get('calibration', {}))
        measurement = MeasurementSettings.from_dict(cell_dto.get('measurement', {}))

        return cls(
            cell_id=cell_dto['id'],
            connection=connection,
            calibration=calibration,
            measurement=measurement
        )

    def update_field(self, section: str, field: str, value: Any) -> None:
        """
        Update a specific field (mutates in place).

        Args:
            section: "connection", "calibration", or "measurement"
            field: Field name within that section
            value: New value
        """
        if section == "connection":
            setattr(self.connection, field, value)
        elif section == "calibration":
            setattr(self.calibration, field, value)
        elif section == "measurement":
            setattr(self.measurement, field, value)
        else:
            raise ValueError(f"Unknown section: {section}")
