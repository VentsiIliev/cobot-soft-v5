"""
ServiceResult Type

Clean return type for all service operations - no callbacks needed!
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ServiceResult:
    """
    Standard result type for all service operations.
    
    Attributes:
        success: Whether the operation succeeded
        message: Human-readable message (for success or error)
        data: Optional data returned by the operation
    
    Usage:
        result = service.some_operation()
        if result.success:
            print(f"Success: {result.message}")
            if result.data:
                process_data(result.data)
        else:
            print(f"Error: {result.message}")
    """
    success: bool
    message: str
    data: Optional[Any] = None
    
    @classmethod
    def success_result(cls, message: str, data: Any = None) -> 'ServiceResult':
        """Create a success result"""
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_result(cls, message: str) -> 'ServiceResult':
        """Create an error result"""
        return cls(success=False, message=message, data=None)
    
    def __bool__(self) -> bool:
        """Allow using result in boolean context: if result: ..."""
        return self.success