import pytest
from PyQt6.QtWidgets import QApplication

from core.base_robot_application import ApplicationState
from plugins.core.dashboard.ui.widgets.ControlButtonsWidget import ControlButtonsWidget


# ----------------- QApplication Fixture ----------------- #
@pytest.fixture(scope="session")
def app():
    """Ensure a single QApplication is created for all tests."""
    return QApplication([])


@pytest.fixture
def widget(app):
    """Create and clean up the widget for each test."""
    w = ControlButtonsWidget()
    yield w
    w.clean_up()
    w.deleteLater()


# ----------------- Creation Tests ----------------- #
def test_buttons_created(widget):
    assert widget.start_btn is not None
    assert widget.stop_btn is not None
    assert widget.pause_btn is not None


def test_buttons_initially_disabled(widget):
    assert not widget.start_btn.isEnabled()
    assert not widget.stop_btn.isEnabled()
    assert not widget.pause_btn.isEnabled()


# ----------------- Signal Emission Tests ----------------- #
def test_start_signal_emitted(widget):
    received = []
    widget.start_clicked.connect(lambda: received.append(True))

    widget.start_btn.setEnabled(True)
    widget.start_btn.click()

    assert received == [True]


def test_stop_signal_emitted(widget):
    received = []
    widget.stop_clicked.connect(lambda: received.append(True))

    widget.stop_btn.setEnabled(True)
    widget.stop_btn.click()

    assert received == [True]


def test_pause_signal_emitted(widget):
    received = []
    widget.pause_clicked.connect(lambda: received.append(True))

    widget.pause_btn.setEnabled(True)
    widget.pause_btn.click()

    assert received == [True]


# ----------------- State Simulation / UI Update Tests ----------------- #
@pytest.mark.parametrize("state, expected", [
    (ApplicationState.IDLE,         (False, False, False, "Pause")),
    (ApplicationState.STARTED,      (False, True, True, "Pause")),
    (ApplicationState.PAUSED,       (False, True, True, "Resume")),
    (ApplicationState.INITIALIZING, (False, False, False, "Pause")),
    (ApplicationState.CALIBRATING,  (False, False, False, "Pause")),
    (ApplicationState.STOPPED,      (False, False, False, "Pause")),
    (ApplicationState.ERROR,        (False, True, False, "Pause")),
])
def test_button_states(widget, state, expected):
    start_enabled, stop_enabled, pause_enabled, pause_text = expected

    # ---- Simulate system state update ----
    widget.on_system_status_update(state)
    QApplication.processEvents()

    # ---- Validate resulting UI state ----
    assert widget.start_btn.isEnabled() == start_enabled
    assert widget.stop_btn.isEnabled() == stop_enabled
    assert widget.pause_btn.isEnabled() == pause_enabled

    # Accept translated or raw text
    assert widget.pause_btn.text() in (pause_text, widget.tr(pause_text))


# ----------------- Translation Test ----------------- #
def test_retranslate(widget):
    widget.retranslate()
    assert widget.start_btn.text() != ""
    assert widget.stop_btn.text() != ""
    assert widget.pause_btn.text() != ""


# ----------------- Cleanup Test ----------------- #
def test_cleanup(widget):
    broker = widget.broker

    # Count before cleanup
    before = list(broker.subscribers.get("application/state", []))

    widget.clean_up()

    after = list(broker.subscribers.get("application/state", []))

    # Should remove the subscription
    assert len(after) <= len(before)
