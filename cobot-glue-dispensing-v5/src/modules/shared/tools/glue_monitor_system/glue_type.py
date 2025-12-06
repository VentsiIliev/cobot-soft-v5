from enum import Enum


class GlueType(Enum):
    TypeA = "Type A"
    TypeB = "Type B"
    TypeC = "Type C"
    TypeD = "Type D"

    def __str__(self):
        """
        Return the string representation of the glue type.

        Returns:
            str: The human-readable glue type value (e.g., "Type A").
        """
        return self.value