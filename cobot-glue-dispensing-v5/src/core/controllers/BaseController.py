import inspect
import traceback
from abc import abstractmethod

from core.controllers.IController import IController


class BaseController(IController):

    def __init__(self):
        self._handlers = {}


    def register_handler(self, endpoint, handler):
        print(f"Registering handler for endpoint: {endpoint}")
        self._handlers[endpoint] = handler

    @abstractmethod
    def _initialize_handlers(self):
        """
        Subclasses MUST implement this method to register their endpoint handlers.
        """
        pass

    def handle(self, request, parts=None, data=None):
        handler = self._handlers.get(request)
        if handler is None and hasattr(self, "_dynamic_handler_resolver"):
            handler = self._dynamic_handler_resolver(request)

        if handler is None:
            raise ValueError(f"[BaseController]: No handler registered for: {request}")

        try:
            sig = inspect.signature(handler)
            # Check if the handler has a 'data' parameter
            if len(sig.parameters) == 0:
                return handler()  # no arguments expected
            else:
                return handler(data)  # pass data (can be None)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"Error handling '{request}': {e}"}
