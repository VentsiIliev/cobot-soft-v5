from abc import ABC, abstractmethod

from core.application.interfaces.application_settings_interface import ApplicationSettingsRegistry
from core.controllers.IController import IController


class BaseSettingsController(IController, ABC):
    """
    Abstract base class for SettingsController.
    """

    def __init__(self,settings_service,settings_registry:ApplicationSettingsRegistry):
        super().__init__()
        self.settings_service = settings_service
        self.settings_registry = settings_registry

    @abstractmethod
    def handle(self, request, parts, data=None):
        """
        Abstract method to handle settings requests.

        Args:
            request (str): Full request string
            parts (list): Split request path parts
            data (dict, optional): Settings data for POST/set requests

        Returns:
            dict: Response dictionary
        """
        pass