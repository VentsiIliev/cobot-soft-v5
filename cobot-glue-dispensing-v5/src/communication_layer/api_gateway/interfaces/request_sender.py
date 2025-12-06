from abc import ABC, abstractmethod

from communication_layer.api_gateway.interfaces.request_handler_interface import IRequestHandler


class RequestSender(ABC):
    """
    Abstract base class defining the interface for sending requests.

    Classes that inherit from RequestSender must implement the `sendRequest` method
    to handle the dispatching of a request to the appropriate target (e.g., hardware,
    service, shared).

    This abstraction is useful to decouple request logic from the specific implementation
    of how requests are transmitted or processed.

    Methods:
        sendRequest(request): Abstract method that must be implemented to handle
                              sending a request.
    """

    def __init__(self,request_handler: IRequestHandler):
        self.request_handler = request_handler

    @abstractmethod
    def send_request(self, request):
        """
              Sends a request to a specific target.

              Args:
                  request (Any): The request object to be sent. This can be a dictionary,
                                 a custom request class, or another data structure,
                                 depending on the implementation.

              Returns:
                  Any: The result of the request execution, typically a response object
                       or data structure.
              """
        pass