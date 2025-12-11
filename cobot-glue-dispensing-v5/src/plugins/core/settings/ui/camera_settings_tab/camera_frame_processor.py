import cv2
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtGui import QImage, QPixmap


class CameraFrameProcessor(QThread):
    """
    Worker thread for processing camera frames.
    Offloads expensive image operations from main GUI thread.
    """
    # Signal emits the processed QPixmap ready for display
    frame_processed = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        self.frame_queue = []
        self.is_running = True
        self.mutex = QtCore.QMutex()
        self.wait_condition = QtCore.QWaitCondition()
        self.target_size = None  # Will be set from main thread

    def set_target_size(self, width, height):
        """Set the target size for scaled output"""
        with QtCore.QMutexLocker(self.mutex):
            self.target_size = (width, height)

    def add_frame(self, cv2_image):
        """Add a frame to the processing queue (called from main thread)"""
        with QtCore.QMutexLocker(self.mutex):
            # Keep only the latest frame to avoid queue buildup
            self.frame_queue = [cv2_image]
            self.wait_condition.wakeOne()

    def run(self):
        """Main worker thread loop - processes frames in background"""
        while self.is_running:
            # Wait for a frame to be available
            self.mutex.lock()
            if not self.frame_queue:
                self.wait_condition.wait(self.mutex)

            if not self.frame_queue or not self.is_running:
                self.mutex.unlock()
                continue

            # Get the frame
            cv2_image = self.frame_queue.pop(0)
            target_size = self.target_size
            self.mutex.unlock()

            try:
                # EXPENSIVE OPERATIONS - now running in background thread!
                # 1. BGR to RGB conversion
                if len(cv2_image.shape) == 3:
                    rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
                else:
                    rgb_image = cv2_image

                height, width = rgb_image.shape[:2]
                bytes_per_line = 3 * width if len(rgb_image.shape) == 3 else width

                # 2. Create QImage
                if len(rgb_image.shape) == 3:
                    q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                else:
                    q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

                # 3. Create QPixmap
                pixmap = QPixmap.fromImage(q_image.copy())  # Copy to detach from numpy array

                # 4. Scale to target size (most expensive operation!)
                if target_size:
                    from PyQt6.QtCore import QSize
                    scaled_pixmap = pixmap.scaled(
                        QSize(target_size[0], target_size[1]),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                else:
                    scaled_pixmap = pixmap

                # Emit the processed pixmap to main thread
                self.frame_processed.emit(scaled_pixmap)

            except Exception as e:
                print(f"[CameraFrameProcessor] Error processing frame: {e}")
                import traceback
                traceback.print_exc()

    def stop(self):
        """Stop the worker thread gracefully"""
        with QtCore.QMutexLocker(self.mutex):
            self.is_running = False
            self.wait_condition.wakeOne()
