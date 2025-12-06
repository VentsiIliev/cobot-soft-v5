from communication_layer.api_gateway.interfaces.request_handler_interface import IRequestHandler
from communication_layer.api_gateway.interfaces.request_sender import RequestSender
from communication_layer.api.v1.Request import Request


class DomesticRequestSender(RequestSender):
    def __init__(self, request_handler: IRequestHandler):
        super().__init__(request_handler)
        self.requestHandler = request_handler

    def send_request(self, request: str,data=None):

        if not isinstance(request, Request):
            return self.requestHandler.handleRequest(request,data)
        else:
            return self.requestHandler.handleRequest(request.to_dict())


