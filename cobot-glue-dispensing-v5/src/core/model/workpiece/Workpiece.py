"""
Description:
    This module defines the data model for a workpieces used in the glue dispensing system.
    It includes a field enumeration for standardized keys and abstract/base class definitions
    for workpieces data structures.

    These abstractions help manage serialization, validation, and structural consistency
    across various components of the application.
"""

from enum import Enum
from abc import ABC, abstractmethod




class AbstractWorkpiece(ABC):
    """
    Abstract base class for workpieces objects.

    Enforces implementation of equality logic and provides a validation
    mechanism for mandatory fields.
    """
    def __init__(self, workpieceId:int, contour):
        """
               Initializes an abstract workpieces with a required ID.

               Args:
                   workpieceId (int): Unique identifier for the workpieces.
                   contour: Geometric representation of the workpieces boundary.
               """
        if not workpieceId:
            raise ValueError("Workpiece ID must be provided")
        self.workpieceId = workpieceId

    @abstractmethod

    def __eq__(self, other):
        """
                Abstract method to compare two workpieces.
                Must be implemented by subclasses.
                """
        pass


class BaseWorkpiece(AbstractWorkpiece):
    """
        Base implementation of a workpieces.

        Only equality comparison is implemented here, based on the workpieces ID.
        """
    def __init__(self, workpieceId:int, contour):
        """
               Initializes a base workpieces.

               Args:
                   workpieceId (int): Unique identifier for the workpieces.
                   contour: Geometric boundary data for the workpieces.
               """
        super().__init__(workpieceId, contour)

    def __eq__(self, other):
        """
              Checks equality based on workpieces ID.

              Returns:
                  bool: True if IDs match, otherwise False.
              """
        return self.workpieceId == other.workpieceId

    @staticmethod
    @abstractmethod
    def from_dict(data: dict):
        """
            Abstract method to create a workpieces instance from a dictionary.

            Args:
                data (dict): Dictionary containing workpieces data.
            Returns:
                BaseWorkpiece: An instance of BaseWorkpiece or its subclass.
            """
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """
            Abstract method to convert the workpieces instance to a dictionary.

            Returns:
                dict: A dictionary representation of the workpieces.
            """
        pass