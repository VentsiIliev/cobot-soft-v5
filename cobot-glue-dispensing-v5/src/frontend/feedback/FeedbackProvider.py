import sys

from PyQt6.QtWidgets import QApplication


from frontend.core.utils.localization.container import get_app_translator
from frontend.feedback.FeedbackWindow import FeedbackWindow, INFO_MESSAGE

from frontend.core.utils.IconLoader import PLACE_CHESSBOARD_ICON
from modules.shared.localization.enums.Message import Message


class FeedbackProvider:
    def __init__(self):
        pass


    @staticmethod
    def showPlaceCalibrationPattern():
        feedbackWindow = FeedbackWindow(PLACE_CHESSBOARD_ICON,INFO_MESSAGE)
        feedbackWindow.show_feedback()

    @staticmethod
    def showMessage(message):
        # check if message is simple string
        if type(message) is str:
            feedbackWindow = FeedbackWindow(message = message, message_type =INFO_MESSAGE)
            feedbackWindow.show_feedback()
        else:
            if not isinstance(message,Message):
                raise TypeError("message must be of type str or Message Enum")
            # translate the message and display it
            translator = get_app_translator()
            translator.tr(message.value)
            # pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    FeedbackProvider.showPlaceCalibrationPattern()
    FeedbackProvider.showMessage("This is an information message.")
    sys.exit(app.exec_())