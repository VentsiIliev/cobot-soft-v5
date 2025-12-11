import pytest
from unittest.mock import Mock

from communication_layer.api_gateway.DomesticRequestSender import DomesticRequestSender
from communication_layer.api_gateway.interfaces.request_handler_interface import IRequestHandler
from communication_layer.api.v1.Request import Request


@pytest.fixture
def mock_handler():
    return Mock(spec=IRequestHandler)


@pytest.fixture
def sender(mock_handler):
    return DomesticRequestSender(mock_handler)


def test_send_request_with_string(sender, mock_handler):
    mock_handler.handleRequest.return_value = "ok"

    result = sender.send_request("MY_CMD", data={"x": 1})

    mock_handler.handleRequest.assert_called_once_with("MY_CMD", {"x": 1})
    assert result == "ok"


def test_send_request_with_Request_object(sender, mock_handler):
    req = Mock(spec=Request)
    req.to_dict.return_value = {"converted": True}

    mock_handler.handleRequest.return_value = "ok"

    result = sender.send_request(req)

    req.to_dict.assert_called_once()
    mock_handler.handleRequest.assert_called_once_with({"converted": True})
    assert result == "ok"


def test_constructor_sets_handler(mock_handler):
    sender = DomesticRequestSender(mock_handler)
    assert sender.request_handler is mock_handler
    assert sender.requestHandler is mock_handler
