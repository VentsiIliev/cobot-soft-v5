import pytest
from unittest.mock import MagicMock

from PyQt6.QtWidgets import QApplication

from plugins.core.settings.ui.SettingsAppWidget import SettingsAppWidget
from plugins.core.settings.ui.SettingsContent import SettingsContent


@pytest.fixture(scope='module')
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class DummyServiceResult:
    def __init__(self, success=True, message="ok", data=None):
        self.success = success
        self.message = message
        self.data = data or {}


class DummyControllerService:
    def __init__(self):
        # settings and robot will be created as MagicMock-like objects
        self.settings = MagicMock()
        self.robot = MagicMock()


class DummyController:
    def __init__(self):
        self.requestSender = MagicMock()
        # provide basic handle used by some code paths
        self.handled = []

    def handle(self, _req, *args, **kwargs):
        self.handled.append(_req)
        return {"status": "success", "message": "handled"}


def test_settings_update_triggers_service(qt_app):
    controller = DummyController()
    cs = DummyControllerService()

    # Make update_setting return a success-like object
    cs.settings.update_setting.return_value = DummyServiceResult(success=True, message="saved")

    widget = SettingsAppWidget(parent=None, controller=controller, controller_service=cs)
    widget.setup_ui()

    # Ensure content_widget exists
    assert hasattr(widget, 'content_widget')
    content = widget.content_widget
    assert isinstance(content, SettingsContent)

    # Emit a setting_changed signal and verify controller_service.settings.update_setting called
    content.setting_changed.emit('some_key', 'value', 'SomeClass')

    cs.settings.update_setting.assert_called()
    called_args = cs.settings.update_setting.call_args[0]
    assert called_args[0] == 'some_key'
    assert called_args[1] == 'value'


def test_jog_signals_forwarded_to_robot(qt_app):
    controller = DummyController()
    cs = DummyControllerService()

    # Robot service methods: jog_robot and save_calibration_point
    cs.robot.jog_robot.return_value = DummyServiceResult(success=True)
    cs.robot.save_calibration_point.return_value = DummyServiceResult(success=True)

    widget = SettingsAppWidget(parent=None, controller=controller, controller_service=cs)
    widget.setup_ui()

    content = widget.content_widget
    assert isinstance(content, SettingsContent)

    # Simulate a jog request from the internal jog widget
    # The jogRequested signature: (cmd, axis, direction, value)
    content.jogRequested.emit('JOG_ROBOT', 'X', 'Plus', 5.0)

    # robot.jog_robot should be called with axis, direction, value
    cs.robot.jog_robot.assert_called()
    args = cs.robot.jog_robot.call_args[0]
    assert args[0] in ('X', 'x', 'x') or args[0].lower() == 'x'
    assert args[2] in ('Plus', 'Minus', '+', '-') or args[2] in ('Plus', 'Minus')

    # Simulate save calibration point
    content.jog_save_point_requested.emit()
    cs.robot.save_calibration_point.assert_called()


def test_jog_start_stop_logging(qt_app, capsys):
    controller = DummyController()
    cs = DummyControllerService()

    widget = SettingsAppWidget(parent=None, controller=controller, controller_service=cs)
    widget.setup_ui()

    content = widget.content_widget

    # Emit start/stop and capture stdout logs
    content.jogStarted.emit('x_plus')
    content.jogStopped.emit('x_plus')

    # There's no direct return, but ensure no exceptions and captured output contains expected substrings
    captured = capsys.readouterr()
    assert 'Jog started' in captured.out
    assert 'Jog stopped' in captured.out

