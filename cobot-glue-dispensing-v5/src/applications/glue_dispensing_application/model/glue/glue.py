"""
Glue Type Data Model

Represents a glue type with name and description.
Implements JsonSerializable for consistent serialization patterns.
"""

from typing import Dict, Any
import uuid
from modules.shared.core.interfaces.JsonSerializable import JsonSerializable


class Glue(JsonSerializable):
    """
    Represents a glue type with unique ID, name, and description.

    Attributes:
        id (str): Unique identifier (UUID)
        name (str): Display name of the glue type
        description (str): Optional description
    """

    def __init__(self, name: str, description: str = "", glue_id: str = None):
        """
        Initialize a Glue instance.

        Args:
            name: Name of the glue type (required)
            description: Description of the glue type (optional)
            glue_id: Unique ID (auto-generated if not provided)
        """
        self.id = glue_id if glue_id else str(uuid.uuid4())
        self.name = name.strip()  # Auto-trim whitespace
        self.description = description.strip() if description else ""

    def to_json(self) -> Dict[str, Any]:
        """
        Convert to JSON-serializable dictionary.

        Returns:
            Dict containing id, name, and description
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> 'Glue':
        """
        Create Glue instance from dictionary.

        Args:
            data: Dictionary with id, name, and description

        Returns:
            Glue instance
        """
        return Glue(
            name=data.get("name", ""),
            description=data.get("description", ""),
            glue_id=data.get("id")
        )

    def __eq__(self, other):
        """Check equality based on ID."""
        if not isinstance(other, Glue):
            return False
        return self.id == other.id

    def __str__(self):
        return f"Glue(id={self.id}, name='{self.name}', description='{self.description}')"

    def __repr__(self):
        return self.__str__()
