"""
Controller Services

Clean, explicit service layer for UI-to-backend communication.
No callbacks, no global state - just clean dependency injection!
"""

from .ControllerService import ControllerService
from .types.ServiceResult import ServiceResult

__all__ = ['ControllerService', 'ServiceResult']