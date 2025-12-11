from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QMetaObject, pyqtSlot

from communication_layer.api.v1.topics import SystemTopics
from modules.shared.MessageBroker import MessageBroker

from frontend.widgets.MaterialButton import MaterialButton
from frontend.core.utils.localization import TranslationKeys, TranslatableWidget
from core.base_robot_application import ApplicationState


class ControlButtonsWidget(TranslatableWidget):
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()

    BUTTON_CONFIG = {
        ApplicationState.IDLE: {
            "start": True, "stop": False, "pause": False, "pause_text": TranslationKeys.Dashboard.PAUSE
        },
        ApplicationState.STARTED: {
            "start": False, "stop": True, "pause": True, "pause_text": TranslationKeys.Dashboard.PAUSE
        },
        ApplicationState.PAUSED: {
            "start": False, "stop": True, "pause": True, "pause_text": "Resume"
        },
        ApplicationState.INITIALIZING: {
            "start": False, "stop": False, "pause": False, "pause_text": TranslationKeys.Dashboard.PAUSE
        },
        ApplicationState.CALIBRATING: {
            "start": False, "stop": False, "pause": False, "pause_text": TranslationKeys.Dashboard.PAUSE
        },
        ApplicationState.STOPPED: {
            "start": False, "stop": False, "pause": False, "pause_text": TranslationKeys.Dashboard.PAUSE
        },
        ApplicationState.ERROR: {
            "start": False, "stop": True, "pause": False, "pause_text": TranslationKeys.Dashboard.PAUSE
        },
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, auto_retranslate=False)

        self.app_state = None
        self.is_paused = False
        self.broker = MessageBroker()

        self.init_ui()
        self.connect_signals()
        self.init_translations()

        print(f"🎛️ ControlButtonsWidget: Subscribing to {SystemTopics.APPLICATION_STATE}")
        self.broker.subscribe(SystemTopics.APPLICATION_STATE, self.on_system_status_update)
        print("🎛️ ControlButtonsWidget: Subscription completed")

    # ----------------- UI Setup ----------------- #
    def _create_frame_with_layout(self, min_height=120) -> tuple[QFrame, QHBoxLayout]:
        frame = QFrame()
        frame.setStyleSheet("QFrame {border: none; background-color: transparent;}")
        frame.setMinimumHeight(min_height)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)
        return frame, layout

    def _create_button(self, font_size=20, enabled=False) -> MaterialButton:
        btn = MaterialButton("", font_size=font_size)
        btn.setEnabled(enabled)
        return btn

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_frame, top_layout = self._create_frame_with_layout()
        bottom_frame, bottom_layout = self._create_frame_with_layout()

        self.start_btn = self._create_button()
        self.stop_btn = self._create_button()
        self.pause_btn = self._create_button()

        top_layout.addWidget(self.start_btn)
        top_layout.addWidget(self.stop_btn)
        bottom_layout.addWidget(self.pause_btn)

        main_layout.addWidget(top_frame)
        main_layout.addWidget(bottom_frame)

    # ----------------- Signals ----------------- #
    def connect_signals(self) -> None:
        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.pause_btn.clicked.connect(self.pause_clicked.emit)

    # ----------------- Button State Management ----------------- #
    def enable_start_button(self, enabled=True) -> None:
        self.start_btn.setEnabled(enabled)

    def enable_stop_button(self, enabled=True) -> None:
        self.stop_btn.setEnabled(enabled)

    def enable_pause_button(self, enabled=True) -> None:
        self.pause_btn.setEnabled(enabled)

    def on_system_status_update(self, state_data) -> None:
        """Handle system state updates."""
        try:
            if not (self.start_btn and self.stop_btn and self.pause_btn):
                return

            # Convert message to ApplicationState
            if isinstance(state_data, dict) and "state" in state_data:
                try:
                    new_state = ApplicationState(state_data["state"])
                except ValueError:
                    print(f"Unknown application state: {state_data['state']}")
                    return
            else:
                new_state = state_data

            if self.app_state == new_state:
                return

            self.app_state = new_state
            QMetaObject.invokeMethod(self, "_update_button_states_safe", Qt.ConnectionType.QueuedConnection)
        except RuntimeError:
            pass

    @pyqtSlot()
    def _update_button_states_safe(self) -> None:
        try:
            if not (self.start_btn and self.stop_btn and self.pause_btn):
                return
            self.update_button_states()
        except RuntimeError:
            pass

    def update_button_states(self) -> None:
        if not self.app_state:
            return

        config = self.BUTTON_CONFIG.get(self.app_state)
        if not config:
            return

        self.start_btn.setEnabled(config["start"])
        self.stop_btn.setEnabled(config["stop"])
        self.pause_btn.setEnabled(config["pause"])
        self.pause_btn.setText(self.tr(config["pause_text"]))
        self.is_paused = self.app_state == ApplicationState.PAUSED

    # ----------------- Translation ----------------- #
    def retranslate(self) -> None:
        self.start_btn.setText(self.tr(TranslationKeys.Dashboard.START))
        self.stop_btn.setText(self.tr(TranslationKeys.Dashboard.STOP))
        self.pause_btn.setText(self.tr(TranslationKeys.Dashboard.PAUSE))

    # ----------------- Cleanup ----------------- #
    def clean_up(self) -> None:
        self.broker.unsubscribe(SystemTopics.APPLICATION_STATE, self.on_system_status_update)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ControlButtonsWidget()
    window.show()
    sys.exit(app.exec())
