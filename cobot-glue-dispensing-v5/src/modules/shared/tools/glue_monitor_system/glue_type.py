import warnings
from enum import Enum

from typing_extensions import deprecated


@deprecated
class GlueType(Enum):
    """
    DEPRECATED: This enum is deprecated and will be removed in a future version.

    Use dynamic glue types from GlueTypesService instead:
    - Get types: GlueTypesHandler.handle_get_glue_types()
    - Validate: GlueTypesService.exists(name)

    Built-in types (TypeA-D) are now stored as regular custom types in glue_types.json.
    Migration to string-based types is in progress.
    """

    TypeA = "Type A"
    TypeB = "Type B"
    TypeC = "Type C"
    TypeD = "Type D"

    def __init__(self, value):
        warnings.warn(
            f"GlueType enum is deprecated. Use string '{value}' directly instead. "
            "This enum will be removed in v6.0.",
            DeprecationWarning,
            stacklevel=2
        )

    def __str__(self):
        """
        Return the string representation of the glue type.

        Returns:
            str: The human-readable glue type value (e.g., "Type A").
        """
        return self.value