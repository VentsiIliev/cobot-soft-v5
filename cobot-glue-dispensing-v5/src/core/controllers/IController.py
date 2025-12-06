# core/controllers/IController.py
import traceback

from abc import ABC, abstractmethod

class IController(ABC):

    @abstractmethod
    def handle(self, request, parts=None, data=None):
        pass


