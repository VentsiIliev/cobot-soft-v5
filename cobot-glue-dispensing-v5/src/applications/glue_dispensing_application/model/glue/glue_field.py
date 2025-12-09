"""
Glue Field Enumeration

Standardized field names for glue type data structures.
Follows the pattern established by GlueWorkpieceField.
"""

from enum import Enum


class GlueField(Enum):
    """
    Enum representing standardized keys for glue type fields.

    Used for consistency in API communication and data structures.
    """
    ID = "id"
    NAME = "name"
    DESCRIPTION = "description"

    def get_as_label(self) -> str:
        """
        Returns a user-friendly label version of the enum name.
        Example: GLUE_TYPE → "Glue type"
        """
        return self.name.capitalize().replace("_", " ")

    def lower(self) -> str:
        """
        Returns the enum value in lowercase.
        Useful for JSON key consistency.
        """
        return self.value.lower()
