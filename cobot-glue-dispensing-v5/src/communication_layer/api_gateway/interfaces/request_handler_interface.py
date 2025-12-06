from abc import ABC, abstractmethod


class IRequestHandler(ABC):
    """Interface for request handlers in the API gateway."""

    @abstractmethod
    def handleRequest(self, request: str, data: dict = None) -> dict:
        """Handle a request and return a response dictionary."""
        pass

    @abstractmethod
    def _parseRequest(self, request: str) -> list:
        """Parse request path into parts."""
        pass
