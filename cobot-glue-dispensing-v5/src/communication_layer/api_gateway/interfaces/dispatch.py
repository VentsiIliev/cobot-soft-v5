from abc import ABC, abstractmethod

class IDispatcher(ABC):
    """Interface for all API dispatchers."""

    @abstractmethod
    def dispatch(self, parts: list, request: str, data: dict = None) -> dict:
        """Handle a request and return a response dict."""
        pass
