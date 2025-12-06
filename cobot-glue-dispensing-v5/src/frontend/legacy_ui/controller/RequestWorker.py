from PyQt6.QtCore import QObject, pyqtSignal
from communication_layer.api.v1.Response import Response
class RequestWorker(QObject):
    finished = pyqtSignal(object, object)  # request, response
    error = pyqtSignal(object, object)     # request, error

    def __init__(self, requestSender, request):
        super().__init__()
        self.requestSender = requestSender
        self.request = request

    def run(self):
        try:
            response_dict = self.requestSender.send_request(self.request)
            response = Response.from_dict(response_dict)
            self.finished.emit(self.request, response)
        except Exception as e:
            self.error.emit(self.request, e)
