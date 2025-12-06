import time

from PyQt6.QtCore import pyqtSignal, QObject, pyqtSlot


class RefreshGeneratorWorker(QObject):
    """
    Worker thread to refresh generator state without blocking UI.
    """
    finished = pyqtSignal(object)  # emits generator_state object

    def __init__(self, glueSprayService):
        super().__init__()
        self.glueSprayService = glueSprayService

    def run(self):
        generator_state = None
        try:
            # Call service to get generator state
            generator_state = self.glueSprayService.getGeneratorState()
        except Exception as e:
            print(f"Error refreshing generator state: {e}")

        # Emit the result (actual or dummy state)
        self.finished.emit(generator_state)



class GeneratorWorker(QObject):
    finished = pyqtSignal(object, bool)  # emits (generator_state object, result bool)

    def __init__(self, glueSprayService, state):
        super().__init__()
        self.glueSprayService = glueSprayService
        self.state = state

    @pyqtSlot()
    def run(self):
        generator_state = None
        result = False
        try:
            # Turn generator on/off depending on self.state
            if self.state:
                result = self.glueSprayService.generatorOn()
            else:
                result = self.glueSprayService.generatorOff()

            # Wait for hardware to respond - increased delay for reliable state reading
            time.sleep(0.5)  # 500ms delay to allow hardware state change
            generator_state = self.glueSprayService.getGeneratorState()
            print(f"Generator State After Toggle {generator_state}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Don't raise - emit None state to allow UI to handle error
            generator_state = None

        # Emit the GeneratorState object
        self.finished.emit(generator_state, result)