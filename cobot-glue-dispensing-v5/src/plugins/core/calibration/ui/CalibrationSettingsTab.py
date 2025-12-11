import cv2
import numpy as np
import os
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QScroller
from PyQt6.QtWidgets import (QSizePolicy, QScrollArea, QTextEdit, QProgressBar)

from modules.utils import PathResolver
from communication_layer.api.v1.topics import VisionTopics, RobotTopics
from frontend.widgets.ClickableLabel import ClickableLabel
from frontend.widgets.MaterialButton import MaterialButton
from modules.shared.MessageBroker import MessageBroker
from frontend.widgets.robotManualControl.RobotJogWidget import RobotJogWidget
from frontend.widgets.Drawer import Drawer

from frontend.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox



from PyQt6.QtWidgets import QHBoxLayout

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QGroupBox, QTabWidget, QPushButton
from PyQt6.QtCore import Qt

from plugins.core.calibration.ui.utils import convert_camera_coordinates_to_image_coordinates
from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout

# Work area points file paths (for fallback only)
PICKUP_AREA_POINTS_PATH = PathResolver.get_calibration_result_path('pickupAreaPoints.npy')
SPRAY_AREA_POINTS_PATH = PathResolver.get_calibration_result_path('sprayAreaPoints.npy')
WORK_AREA_POINTS_PATH = PathResolver.get_calibration_result_path('workAreaPoints.npy')

class ClickableRow(QWidget):
    def __init__(self, index, label_text, x_spin, y_spin, callback):
        super().__init__()
        self.index = index
        self.callback = callback

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # small margins
        layout.setHorizontalSpacing(2)
        layout.setVerticalSpacing(0)

        self.label = QLabel(label_text)
        self.label.setFixedWidth(100)  # optional, keeps labels aligned

        layout.addWidget(self.label, 0, 0)
        layout.addWidget(x_spin, 0, 1)
        layout.addWidget(y_spin, 0, 2)

        self.setLayout(layout)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback(self.index)


class CalibrationServiceTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    # Robot movement signals
    jogRequested = QtCore.pyqtSignal(str, str, str, float)
    update_camera_feed_signal = QtCore.pyqtSignal()
    move_to_pickup_requested = QtCore.pyqtSignal()
    move_to_calibration_requested = QtCore.pyqtSignal()
    save_point_requested = QtCore.pyqtSignal()

    # Image capture signals
    capture_image_requested = QtCore.pyqtSignal()
    save_images_requested = QtCore.pyqtSignal()

    # Calibration process signals
    calibrate_camera_requested = QtCore.pyqtSignal()
    detect_markers_requested = QtCore.pyqtSignal()
    compute_homography_requested = QtCore.pyqtSignal()
    auto_calibrate_requested = QtCore.pyqtSignal()
    test_calibration_requested = QtCore.pyqtSignal()
    save_work_area_requested = QtCore.pyqtSignal(object)  # Changed from list to object to support dict

    # Debug and testing signals
    show_debug_view_requested = QtCore.pyqtSignal(bool)

    def __init__(self, parent_widget=None, calibration_service=None, controller_service=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")

        self.parent_widget = parent_widget
        self.calibration_service = calibration_service
        self.controller_service = controller_service
        self.debug_mode_active = False
        self.calibration_in_progress = False

        # Store the original image for overlay drawing
        self.original_image = None
        self.image_scale_factor = 1.0
        self.image_to_label_scale = 1.0  # Scale factor from image coords to label coords

        # Initialize robot calibration settings early
        self.robot_settings_fields = {}  # Store references to input fields

        # Create main content with new layout
        self.create_main_content()

        self.updateFrequency = 30  # in milliseconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_camera_feed_signal.emit())
        self.timer.start(self.updateFrequency)

        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

        self.selected_corner_index = None

        broker = MessageBroker()
        broker.subscribe(VisionTopics.CALIBRATION_FEEDBACK, self.addLog)
        broker.subscribe(VisionTopics.CALIBRATION_IMAGE_CAPTURED, self.addLog)
        broker.subscribe(RobotTopics.ROBOT_CALIBRATION_LOG, self.addLog)
        broker.subscribe(RobotTopics.ROBOT_CALIBRATION_START, self.onRobotCalibrationStart)
        broker.subscribe(RobotTopics.ROBOT_CALIBRATION_STOP, self.onRobotCalibrationStop)

        # Load saved work area points for both pickup and spray areas
        self.load_all_saved_work_areas()

        self.log_que = []  # Message queue for logs
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.flush_log_queue)
        self.log_timer.start(100)  # Flush every 100ms

    def onRbotCalibrationImage(self,image):
        self.update_camera_preview_from_cv2(image,True,zoom_factor=5,show_work_area=False)

    def onRobotCalibrationStart(self,message):
        # Pause the camera feed timer
        self.timer.stop()
        print("Camera feed timer paused for robot calibration")
        
        broker = MessageBroker()
        broker.subscribe(RobotTopics.ROBOT_CALIBRATION_IMAGE, self.onRbotCalibrationImage)

    def onRobotCalibrationStop(self,message):
        broker = MessageBroker()
        broker.unsubscribe(RobotTopics.ROBOT_CALIBRATION_IMAGE, self.onRbotCalibrationImage)
        
        # Resume the camera feed timer
        self.timer.start(self.updateFrequency)
        print("Camera feed timer resumed after robot calibration")

    def addLog(self, message):
        """Add a log message to the output area (thread-safe via queue)"""

        # If msg is a list, join its elements
        if isinstance(message, list):
            message = "\n".join(str(m) for m in message)


        if hasattr(self, 'log_que'):
            self.log_que.append(message)

    def flush_log_queue(self):
        """Flush messages from the log queue to the log output (main thread only)"""
        if not self.log_que:
            return
        if hasattr(self, 'log_output'):
            while self.log_que:
                msg = self.log_que.pop(0)
                self.log_output.append(msg)
            self.log_output.ensureCursorVisible()

    def update_camera_preview_from_cv2(self, cv2_image, zoom_in=False,zoom_factor=1.5,show_work_area=True):
        # print("Update image received for preview")
        if hasattr(self, 'calibration_preview_label'):
            # Store the original image
            self.original_image = cv2_image.copy()

            # --- ZOOM IN toward the center if flag is True ---
            if zoom_in:
                zoom_factor = zoom_factor  # >1 means zooming in (increase to zoom more)
                h, w = cv2_image.shape[:2]
                new_w = int(w / zoom_factor)
                new_h = int(h / zoom_factor)

                # Compute top-left corner to crop around center
                x1 = (w - new_w) // 2
                y1 = (h - new_h) // 2
                x2 = x1 + new_w
                y2 = y1 + new_h

                # Crop and resize back to original size
                cropped = cv2_image[y1:y2, x1:x2]
                cv2_image = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

            # --- Continue with your original code ---
            if show_work_area:
                overlay_image = self.draw_work_area_overlay(cv2_image)
            else:
                overlay_image = cv2_image  # use raw image

            rgb_image = overlay_image[:, :, ::-1] if len(overlay_image.shape) == 3 else overlay_image
            height, width = rgb_image.shape[:2]
            bytes_per_line = 3 * width if len(rgb_image.shape) == 3 else width

            img_bytes = rgb_image.tobytes()

            if len(rgb_image.shape) == 3:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            self.update_calibration_preview(pixmap)

            # Update corner positions for drag detection
            self.update_corner_positions_for_dragging()

    def draw_work_area_overlay(self, cv2_image):
        """Draw work area corners and lines on the camera image"""
        if cv2_image is None:
            return cv2_image

        overlay_image = cv2_image.copy()

        # Get corner coordinates for current work area (these are now in camera coordinates)
        camera_corners = []
        for i in range(1, 5):
            x_spin = self.corner_fields[self.current_work_area].get(f"corner{i}_x")
            y_spin = self.corner_fields[self.current_work_area].get(f"corner{i}_y")
            if x_spin and y_spin:
                x = x_spin.value()
                y = y_spin.value()
                camera_corners.append((x, y))

        # Convert camera coordinates to actual image coordinates for drawing
        if len(camera_corners) == 4:
            corners = convert_camera_coordinates_to_image_coordinates(self.original_image,camera_corners)
        else:
            corners = []

        if len(corners) == 4:
            # Define colors
            line_color = (0, 255, 0)  # Green for lines
            corner_color = (255, 0, 0)  # Red for corners
            selected_corner_color = (0, 0, 255)  # Blue for selected corner
            fill_color = (0, 255, 0, 50)  # Semi-transparent green for fill

            # Draw filled work area (semi-transparent)
            points = np.array(corners, np.int32)

            # Create overlay for transparency
            overlay = overlay_image.copy()
            cv2.fillPoly(overlay, [points], (0, 255, 0))
            cv2.addWeighted(overlay_image, 0.8, overlay, 0.2, 0, overlay_image)

            # Draw lines connecting corners
            line_thickness = 2
            for i in range(4):
                start_point = corners[i]
                end_point = corners[(i + 1) % 4]  # Connect to next corner (wrap around)
                cv2.line(overlay_image, start_point, end_point, line_color, line_thickness)

        return overlay_image

    def update_corner_positions_for_dragging(self):
        """Update corner positions in label coordinates for drag detection"""
        if not hasattr(self, 'calibration_preview_label') or self.original_image is None:
            return

        # Get corner coordinates in camera space for current work area
        camera_corners = []
        for i in range(1, 5):
            x_spin = self.corner_fields[self.current_work_area].get(f"corner{i}_x")
            y_spin = self.corner_fields[self.current_work_area].get(f"corner{i}_y")
            if x_spin and y_spin:
                x = x_spin.value()
                y = y_spin.value()
                camera_corners.append((x, y))

        if len(camera_corners) == 4:
            # Convert camera coordinates to image coordinates first
            image_corners = convert_camera_coordinates_to_image_coordinates(self.original_image,camera_corners)

            # Calculate the scale factor from image to label coordinates
            label_size = self.calibration_preview_label.size()
            img_height, img_width = self.original_image.shape[:2]

            # Calculate scaling to fit image in label while maintaining aspect ratio
            scale_x = label_size.width() / img_width
            scale_y = label_size.height() / img_height
            scale = min(scale_x, scale_y)  # Use smaller scale to maintain aspect ratio

            self.image_to_label_scale = 1.0 / scale  # Store inverse for easy conversion

            # Update corner positions in the clickable label
            self.calibration_preview_label.update_corner_positions(image_corners, self.image_to_label_scale)

    def update_work_area_visualization(self):
        """Update the work area visualization when corner values change"""
        if self.original_image is not None:
            self.update_camera_preview_from_cv2(self.original_image)

    def update_camera_feed(self, frame):
        try:
            if frame is not None:
                self.update_camera_preview_from_cv2(frame)
            else:
                return
        except Exception as e:
            print(f"Exception occurred: {e}")
        finally:
            pass

    def create_calibration_preview_section(self):
        """Create the calibration preview section with preview and controls"""
        preview_widget = QWidget()
        preview_widget.setFixedWidth(500)
        preview_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
        """)

        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.setSpacing(15)

        # Calibration preview area
        self.calibration_preview_label = ClickableLabel("Calibration Preview")
        self.calibration_preview_label.clicked.connect(self.on_preview_clicked)
        self.calibration_preview_label.corner_dragged.connect(self.on_corner_dragged)
        self.calibration_preview_label.set_parent_widget(self)

        self.calibration_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.calibration_preview_label.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: white;
                font-size: 16px;
                border: 1px solid #666;
                border-radius: 4px;
            }
        """)
        self.calibration_preview_label.setMinimumSize(460, 259)
        self.calibration_preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.calibration_preview_label.setScaledContents(False)
        preview_layout.addWidget(self.calibration_preview_label)

        # Progress bar for calibration
        self.calibration_progress = QProgressBar()
        self.calibration_progress.setVisible(False)
        self.calibration_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
        """)
        preview_layout.addWidget(self.calibration_progress)

        # Control buttons grid - UPDATED SECTION
        button_grid = QGridLayout()
        button_grid.setSpacing(10)

        # Row 0: Robot movement buttons
        self.move_to_pickup_button = MaterialButton("Move to Pickup")
        self.move_to_calibration_button = MaterialButton("Move to Calibration")

        movement_buttons = [self.move_to_pickup_button, self.move_to_calibration_button]
        for i, btn in enumerate(movement_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 0, i)

        # Row 1: Image capture buttons
        # self.save_images_button = MaterialButton("Save Images")


        self.save_workarea_button = MaterialButton("Save Work Area")
        self.save_workarea_button.setMinimumHeight(40)
        button_grid.addWidget(self.save_workarea_button, 1, 0, 1, 2)

        self.capture_image_button = MaterialButton("Capture Image")
        self.capture_image_button.setMinimumHeight(40)
        button_grid.addWidget(self.capture_image_button, 2, 0, 1, 2)

        # Row 2: Calibration process buttons
        # self.calibrate_camera_button = MaterialButton("Calibrate Camera")
        # self.detect_markers_button = MaterialButton("Detect Markers")

        # calibration_buttons = [self.detect_markers_button]
        # for i, btn in enumerate(calibration_buttons):
        #     btn.setMinimumHeight(40)
        #     button_grid.addWidget(btn, 2, i)

        # Row 3: Compute homography (spans both columns)

        self.calibrate_camera_button = MaterialButton("Calibrate Camera")
        self.calibrate_camera_button.setMinimumHeight(40)
        button_grid.addWidget(self.calibrate_camera_button, 3, 0, 1, 2)

        self.compute_homography_button = MaterialButton("Calibrate Robot")
        self.compute_homography_button.setMinimumHeight(40)
        button_grid.addWidget(self.compute_homography_button, 4, 0, 1, 2)  # Span 2 columns

        self.auto_calibrate = MaterialButton("Camera and Robot Calibration")
        self.auto_calibrate.setMinimumHeight(40)
        button_grid.addWidget(self.auto_calibrate, 5, 0, 1, 2)  # Span 2 columns

        self.test_calibration_button = MaterialButton("Test Calibration")
        self.test_calibration_button.setMinimumHeight(40)
        button_grid.addWidget(self.test_calibration_button, 6, 0, 1, 2)  # Span 2 columns


        preview_layout.addLayout(button_grid)

        # Log output area
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(150)
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Logs")
        preview_layout.addWidget(self.log_output)

        preview_layout.addStretch()

        self.connect_default_callbacks()

        for btn in movement_buttons + [self.compute_homography_button,
                                       self.auto_calibrate]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        return preview_widget

    def on_corner_dragged(self, corner_index, label_x, label_y):
        """Handle corner dragging"""
        print(f"Corner {corner_index} dragged to label coordinates: ({label_x}, {label_y})")

        if self.original_image is not None:
            # Convert label coordinates to image coordinates
            image_x = int(label_x * self.image_to_label_scale)
            image_y = int(label_y * self.image_to_label_scale)

            # Ensure coordinates are within image bounds
            img_height, img_width = self.original_image.shape[:2]
            image_x = max(0, min(image_x, img_width - 1))
            image_y = max(0, min(image_y, img_height - 1))

            # Convert image coordinates to camera coordinates (1280x720)
            camera_width = 1280
            camera_height = 720

            camera_x = int((image_x / img_width) * camera_width)
            camera_y = int((image_y / img_height) * camera_height)

            # Ensure coordinates are within camera bounds
            camera_x = max(0, min(camera_x, camera_width - 1))
            camera_y = max(0, min(camera_y, camera_height - 1))
        else:
            camera_x, camera_y = label_x, label_y

        # Update the corresponding spinboxes for current work area
        corner_x_spin = self.corner_fields[self.current_work_area][f"corner{corner_index}_x"]
        corner_y_spin = self.corner_fields[self.current_work_area][f"corner{corner_index}_y"]

        # Temporarily disconnect signals to avoid recursive updates
        corner_x_spin.valueChanged.disconnect()
        corner_y_spin.valueChanged.disconnect()

        corner_x_spin.setValue(camera_x)
        corner_y_spin.setValue(camera_y)

        # Reconnect signals
        corner_x_spin.valueChanged.connect(self.update_work_area_visualization)
        corner_y_spin.valueChanged.connect(self.update_work_area_visualization)

        print(f"Corner {corner_index} updated to camera coordinates: ({camera_x}, {camera_y})")

        # Update the visualization
        self.update_work_area_visualization()

    def on_preview_clicked(self, x, y):
        print(f"Camera preview clicked at: ({x}, {y})")
        if self.selected_corner_index is not None:
            # Convert label click coordinates to camera coordinates (1280x720)
            label_size = self.calibration_preview_label.size()
            if self.original_image is not None:
                img_height, img_width = self.original_image.shape[:2]

                # Calculate scaling factor from label to image
                scale_x = img_width / label_size.width()
                scale_y = img_height / label_size.height()
                scale = min(scale_x, scale_y)

                # Convert to image coordinates
                image_x = int(x * scale)
                image_y = int(y * scale)

                # Convert image coordinates to camera coordinates (1280x720)
                camera_width = 1280
                camera_height = 720

                camera_x = int((image_x / img_width) * camera_width)
                camera_y = int((image_y / img_height) * camera_height)

                # Ensure coordinates are within camera bounds
                camera_x = max(0, min(camera_x, camera_width - 1))
                camera_y = max(0, min(camera_y, camera_height - 1))
            else:
                camera_x, camera_y = x, y

            corner_x_spin = self.corner_fields[self.current_work_area][f"corner{self.selected_corner_index}_x"]
            corner_y_spin = self.corner_fields[self.current_work_area][f"corner{self.selected_corner_index}_y"]

            corner_x_spin.setValue(camera_x)
            corner_y_spin.setValue(camera_y)
            print(f"Corner {self.selected_corner_index} updated to camera coordinates ({camera_x}, {camera_y})")

            # Update the visualization
            self.update_work_area_visualization()

    def update_calibration_preview(self, pixmap):
        """Update the calibration preview with a new frame, maintaining aspect ratio"""
        if hasattr(self, 'calibration_preview_label'):
            label_size = self.calibration_preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.calibration_preview_label.setPixmap(scaled_pixmap)
            self.calibration_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.calibration_preview_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

    def clear_log(self):
        """Clear the log output"""
        if hasattr(self, 'log_output'):
            self.log_output.clear()

    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def update_layout_for_screen_size(self):
        """Update layout based on current screen size"""
        self.clear_layout()
        self.create_main_content()

    def clear_layout(self):
        """Clear all widgets from the layout"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def create_main_content(self):
        """Create the main content with camera preview on left, settings on right, and robot jog as a right-side drawer"""
        # Create a main container widget
        main_widget = QWidget()
        
        # --- Horizontal layout for preview and settings (no jog widget in main layout) ---
        main_horizontal_layout = QHBoxLayout(main_widget)
        main_horizontal_layout.setSpacing(2)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # --- Left: Camera Preview ---
        preview_widget = self.create_calibration_preview_section()

        # --- Right: Settings scroll area (now takes much more space) ---
        settings_scroll_area = QScrollArea()
        settings_scroll_area.setWidgetResizable(True)
        settings_scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        settings_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        settings_scroll_area.setMinimumWidth(400)  # Increased minimum width since jog is now in drawer

        QScroller.grabGesture(settings_scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        settings_content_widget = QWidget()
        settings_content_layout = QVBoxLayout(settings_content_widget)
        settings_content_layout.setSpacing(2)
        settings_content_layout.setContentsMargins(0, 0, 0, 0)

        # Add all the settings groups to the right section
        self.add_settings_to_layout(settings_content_layout)

        settings_scroll_area.setWidget(settings_content_widget)

        # Add to horizontal layout - more space for settings since no jog widget
        main_horizontal_layout.addWidget(preview_widget, 1)  # Left - stretch factor 1
        main_horizontal_layout.addWidget(settings_scroll_area, 3)  # Right - stretch factor 3 (much more space)

        # --- Create Robot Jog Drawer (slides in from right) ---
        self.robotManualControlWidget = RobotJogWidget()
        self.robotManualControlWidget.jogRequested.connect(lambda command, axis, direction, value:
                                                           self.jogRequested.emit(command, axis, direction, value))
        self.robotManualControlWidget.save_point_requested.connect(lambda: self.save_point_requested.emit())
        
        # Set proper size policies for the robot jog widget
        self.robotManualControlWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create the jog drawer widget
        self.jog_drawer = Drawer(main_widget, animation_duration=250, side="right")
        self.jog_drawer.setFixedWidth(420)  # Set drawer width - slightly wider
        
        # Style the drawer
        self.jog_drawer.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-left: 2px solid #dee2e6;
            }
        """)
        
        # Layout for the drawer content with minimal margins to maximize space
        jog_drawer_layout = QVBoxLayout(self.jog_drawer)
        jog_drawer_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins
        jog_drawer_layout.setSpacing(5)  # Minimal spacing
        
        # Add a compact header label  
        drawer_header = QLabel("Robot Jog Controls")
        drawer_header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                padding: 5px 0;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        drawer_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        drawer_header.setFixedHeight(25)  # Smaller header to save space
        jog_drawer_layout.addWidget(drawer_header)
        
        # Add the robot jog widget - let it take ALL the remaining space
        # Remove any size constraints and ensure it fills the drawer
        self.robotManualControlWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Remove any maximum height constraints that might be set
        self.robotManualControlWidget.setMaximumHeight(16777215)  # Remove height constraint
        jog_drawer_layout.addWidget(self.robotManualControlWidget, 1)  # Stretch factor 1 = take all remaining space
        
        # Ensure the drawer itself takes full height
        self.jog_drawer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # Initially position the drawer off-screen (right side)
        self.jog_drawer.resize_to_parent_height()
        
        # Connect to parent widget resize to update drawer height
        if hasattr(main_widget, 'resizeEvent'):
            original_resize_event = main_widget.resizeEvent
        else:
            original_resize_event = None
            
        def on_main_widget_resize(event):
            if original_resize_event:
                original_resize_event(event)
            # Update drawer height when parent resizes
            if hasattr(self, 'jog_drawer'):
                self.jog_drawer.resize_to_parent_height()
                # Also reposition floating button
                if hasattr(self, 'floating_toggle_button'):
                    self.position_floating_button(main_widget)
        
        main_widget.resizeEvent = on_main_widget_resize

        # --- Create floating toggle button for the drawer ---
        self.floating_toggle_button = QPushButton("◀")  # Left arrow when closed
        self.floating_toggle_button.setParent(main_widget)
        self.floating_toggle_button.setFixedSize(40, 80)
        self.floating_toggle_button.setToolTip("Toggle Robot Controls")
        self.floating_toggle_button.clicked.connect(self.toggle_jog_drawer)
        
        # Style the floating button
        self.floating_toggle_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(108, 117, 125, 0.9);
                border: none;
                color: white;
                border-radius: 8px 0px 0px 8px;
                font-size: 18px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(90, 98, 104, 0.95);
            }
            QPushButton:pressed {
                background-color: rgba(84, 91, 98, 1.0);
            }
        """)
        
        # Position the button on the right edge (initially)
        self.position_floating_button(main_widget)

        # Set minimum width for the entire main widget
        main_widget.setMinimumWidth(800)

        self.addWidget(main_widget)

    def add_settings_to_layout(self, parent_layout):
        """Add all settings groups to the layout using a tabbed widget"""
        # Create main settings tab widget
        self.main_settings_tabs = QTabWidget()
        self.main_settings_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #cccccc;
                border-radius: 8px;
                background-color: #ffffff;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-radius: 4px 4px 0px 0px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 500;
                color: #495057;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #212529;
                font-weight: 600;
                border-bottom: 2px solid #007bff;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
                color: #212529;
            }
        """)

        # Create work area corners tab
        work_area_widget = QWidget()
        work_area_layout = QVBoxLayout(work_area_widget)
        work_area_layout.setContentsMargins(10, 15, 10, 10)
        work_area_layout.setSpacing(10)
        
        work_area_group = self.create_work_area_group()
        work_area_layout.addWidget(work_area_group)
        work_area_layout.addStretch()  # Add stretch to push content to top
        
        self.main_settings_tabs.addTab(work_area_widget, "Work Areas")

        # Add the tabbed widget to the parent layout
        parent_layout.addWidget(self.main_settings_tabs)

    def connect_default_callbacks(self):
        """Connect default button callbacks"""
        # Robot movement controls
        self.move_to_pickup_button.clicked.connect(lambda: self.move_to_pickup_requested.emit())
        self.move_to_calibration_button.clicked.connect(lambda: self.move_to_calibration_requested.emit())

        # Image capture controls
        self.capture_image_button.clicked.connect(lambda: self.capture_image_requested.emit())
        # self.save_images_button.clicked.connect(lambda: self.save_images_requested.emit())

        # Calibration process controls
        self.calibrate_camera_button.clicked.connect(lambda: self.calibrate_camera_requested.emit())
        # self.detect_markers_button.clicked.connect(lambda: self.detect_markers_requested.emit())
        self.compute_homography_button.clicked.connect(lambda: self.compute_homography_requested.emit())
        self.auto_calibrate.clicked.connect(lambda: self.auto_calibrate_requested.emit())
        self.test_calibration_button.clicked.connect(lambda: self.test_calibration_requested.emit())
        self.save_workarea_button.clicked.connect(lambda: self.onSaveWorkAreaRequested())

    def onSaveWorkAreaRequested(self):
        """Handle save work area request for current active area"""
        corners = []
        for i in range(1, 5):
            x_spin = self.corner_fields[self.current_work_area].get(f"corner{i}_x")
            y_spin = self.corner_fields[self.current_work_area].get(f"corner{i}_y")
            if x_spin and y_spin:
                x = float(x_spin.value())
                y = float(y_spin.value())
                corners.append([x, y])

        if len(corners) != 4:
            print(f"Error: Not enough corners defined to save {self.current_work_area} work area.")
            return

        # Convert corners from label coordinates to actual image coordinates
        scaled_corners = self.convert_corners_to_image_coordinates(corners)

        # Include area type in the saved data
        area_data = {
            'area_type': self.current_work_area,
            'corners': scaled_corners
        }

        print(f"Original label coordinates: {corners}")
        print(f"Scaled image coordinates: {scaled_corners}")
        print("Saving work area data:", area_data)

        self.save_work_area_requested.emit(area_data)

    def convert_corners_to_image_coordinates(self, camera_corners):
        """No conversion needed - corners are already in camera coordinates (1280x720)"""
        # The input corners are already in camera resolution coordinates
        # Just ensure they're within bounds and convert to the expected format
        camera_width = 1280
        camera_height = 720

        print(f"Using camera coordinates directly: {camera_corners}")

        # Convert coordinates and ensure they're within bounds
        scaled_corners = []
        for x, y in camera_corners:
            # Ensure coordinates are within camera bounds
            scaled_x = max(0, min(float(x), camera_width - 1))
            scaled_y = max(0, min(float(y), camera_height - 1))

            scaled_corners.append([scaled_x, scaled_y])

        return scaled_corners

    def create_work_area_group(self):
        group_box = QGroupBox("Work Area Corners")

        # Create main layout for the group
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Initialize corner fields structure for both areas
        self.corner_fields = {
            'pickup': {},
            'spray': {}
        }
        self.corner_rows = {
            'pickup': {},
            'spray': {}
        }
        self.current_work_area = 'pickup'  # Track which area is active

        # Create tab widget
        self.work_area_tabs = QTabWidget()
        self.work_area_tabs.currentChanged.connect(self.on_work_area_tab_changed)

        # Create pickup area tab
        pickup_tab = self.create_corner_tab('pickup')
        self.work_area_tabs.addTab(pickup_tab, "Pickup Area")

        # Create spray area tab
        spray_tab = self.create_corner_tab('spray')
        self.work_area_tabs.addTab(spray_tab, "Spray Area")

        main_layout.addWidget(self.work_area_tabs)
        group_box.setLayout(main_layout)
        return group_box

    def create_corner_tab(self, area_type):
        """Create a tab for corner settings for specific area type (pickup or spray)"""
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        for i in range(1, 5):
            x_spin = FocusDoubleSpinBox()
            x_spin.setRange(0, 10000)
            x_spin.setDecimals(2)

            y_spin = FocusDoubleSpinBox()
            y_spin.setRange(0, 10000)
            y_spin.setDecimals(2)

            x_spin.setFixedWidth(60)
            y_spin.setFixedWidth(60)

            # Connect value change signals to update visualization
            x_spin.valueChanged.connect(self.update_work_area_visualization)
            y_spin.valueChanged.connect(self.update_work_area_visualization)

            row_widget = ClickableRow(i, f"Corner {i}:", x_spin, y_spin, self.set_selected_corner)
            row_widget.setFixedHeight(30)

            layout.addWidget(row_widget)

            self.corner_fields[area_type][f"corner{i}_x"] = x_spin
            self.corner_fields[area_type][f"corner{i}_y"] = y_spin
            self.corner_rows[area_type][i] = row_widget

        tab_widget.setLayout(layout)
        return tab_widget

    def set_selected_corner(self, index):
        # Clear all highlights for current work area
        for i, row in self.corner_rows[self.current_work_area].items():
            row.setStyleSheet("")
        # Highlight selected corner
        self.corner_rows[self.current_work_area][index].setStyleSheet("background-color: lightblue;")
        self.selected_corner_index = index
        print(f"Selected corner {index} in {self.current_work_area} area")

        # Update visualization to show selected corner
        self.update_work_area_visualization()

    def on_work_area_tab_changed(self, index):
        """Handle work area tab change"""
        area_types = ['pickup', 'spray']
        if 0 <= index < len(area_types):
            self.current_work_area = area_types[index]
            print(f"Switched to {self.current_work_area} area")
            # Clear selection when switching tabs
            self.selected_corner_index = None
            # Load saved points for the new area
            self.load_saved_work_area_points(self.current_work_area)
            # Update visualization for new area
            self.update_work_area_visualization()

    def load_saved_work_area_points(self, area_type):
        """Load saved work area points for the specified area type using controller service"""
        try:
            if area_type not in ['pickup', 'spray']:
                print(f"Invalid area type: {area_type}")
                return

            if self.controller_service and hasattr(self.controller_service, 'camera'):
                # Use the controller service to get work area points
                result = self.controller_service.camera.get_work_area_points(area_type)
                
                if result and result.data:
                    points = result.data
                    if len(points) == 4:  # Ensure we have 4 corner points
                        self.populate_corner_fields(area_type, points)
                        print(f"Loaded saved {area_type} area points: {points}")
                    else:
                        print(f"Invalid number of points in {area_type} area: {len(points)}")
                else:
                    print(f"No saved {area_type} area points found or service error")
            else:
                # Fallback to old method if controller_service is not available
                print("Controller service not available, falling back to direct file access")
                self._load_work_area_points_fallback(area_type)
                
        except Exception as e:
            print(f"Error loading {area_type} area points: {str(e)}")
            # Fallback to old method on error
            self._load_work_area_points_fallback(area_type)
    
    def _load_work_area_points_fallback(self, area_type):
        """Fallback method using direct file access (original implementation)"""
        try:
            if area_type == 'pickup':
                file_path = PICKUP_AREA_POINTS_PATH
            elif area_type == 'spray':
                file_path = SPRAY_AREA_POINTS_PATH
            else:
                return

            if os.path.exists(file_path):
                points = np.load(file_path)
                if len(points) == 4:  # Ensure we have 4 corner points
                    self.populate_corner_fields(area_type, points)
                    print(f"Loaded saved {area_type} area points (fallback): {points.tolist()}")
                else:
                    print(f"Invalid number of points in {area_type} area file: {len(points)}")
            else:
                print(f"No saved {area_type} area points found in {file_path}")
        except Exception as e:
            print(f"Error loading {area_type} area points (fallback): {str(e)}")

    def populate_corner_fields(self, area_type, points):
        """Populate the corner input fields with loaded points"""
        try:
            # Display image coordinates directly (camera resolution 1280x720)
            for i in range(4):
                if i < len(points):
                    x, y = points[i]
                    x_spin = self.corner_fields[area_type].get(f"corner{i+1}_x")
                    y_spin = self.corner_fields[area_type].get(f"corner{i+1}_y")

                    if x_spin and y_spin:
                        # Temporarily disconnect signals to avoid triggering updates during loading
                        x_spin.valueChanged.disconnect()
                        y_spin.valueChanged.disconnect()

                        x_spin.setValue(float(x))
                        y_spin.setValue(float(y))

                        # Reconnect signals
                        x_spin.valueChanged.connect(self.update_work_area_visualization)
                        y_spin.valueChanged.connect(self.update_work_area_visualization)

            # After loading all corners, update the visualization
            if area_type == self.current_work_area:
                self.update_work_area_visualization()
        except Exception as e:
            print(f"Error populating corner fields for {area_type}: {str(e)}")

    def convert_corners_to_label_coordinates(self, image_corners):
        """Convert corner coordinates from camera resolution (1280x720) to label scale"""
        # Use actual camera resolution, not the scaled display image
        camera_width = 1280
        camera_height = 720

        label_size = self.calibration_preview_label.size()

        # Calculate scaling factors from actual camera resolution
        scale_x = camera_width / label_size.width()
        scale_y = camera_height / label_size.height()

        # Use the smaller scale to maintain aspect ratio (consistent with display logic)
        scale = min(scale_x, scale_y)

        print(f"Converting camera coordinates to label coordinates using scale: {scale:.2f}")

        # Convert coordinates
        label_corners = []
        for x, y in image_corners:
            label_x = x / scale
            label_y = y / scale

            # Ensure coordinates are within label bounds
            label_x = max(0, min(label_x, label_size.width() - 1))
            label_y = max(0, min(label_y, label_size.height() - 1))

            label_corners.append([float(label_x), float(label_y)])

        return label_corners

    def load_all_saved_work_areas(self):
        """Load saved work area points for both pickup and spray areas on initialization"""
        print("Loading all saved work area points...")

        # Load pickup area points
        self.load_saved_work_area_points('pickup')

        # Load spray area points
        self.load_saved_work_area_points('spray')

        # Load current area (pickup by default)
        self.load_saved_work_area_points(self.current_work_area)


    def position_floating_button(self, parent_widget):
        """Position the floating button on the right edge of the widget"""
        if hasattr(self, 'floating_toggle_button'):
            parent_size = parent_widget.size()
            button_size = self.floating_toggle_button.size()
            
            # Position on the right edge, vertically centered
            x = parent_size.width() - button_size.width()
            y = (parent_size.height() - button_size.height()) // 2
            
            self.floating_toggle_button.move(x, y)
            self.floating_toggle_button.raise_()  # Keep on top
    
    def toggle_jog_drawer(self):
        """Toggle the robot jog drawer between expanded and collapsed states"""
        if hasattr(self, 'jog_drawer'):
            # Toggle the drawer and update floating button based on state
            self.jog_drawer.toggle()
            
            # Update floating button text and style based on drawer state
            if hasattr(self, 'floating_toggle_button'):
                if self.jog_drawer.is_open:
                    self.floating_toggle_button.setText("▶")  # Right arrow when open (to close)
                    self.floating_toggle_button.setStyleSheet("""
                        QPushButton {
                            background-color: rgba(40, 167, 69, 0.9);
                            border: none;
                            color: white;
                            border-radius: 8px 0px 0px 8px;
                            font-size: 18px;
                            font-weight: bold;
                            margin: 0px;
                            padding: 0px;
                        }
                        QPushButton:hover {
                            background-color: rgba(33, 136, 56, 0.95);
                        }
                        QPushButton:pressed {
                            background-color: rgba(30, 126, 52, 1.0);
                        }
                    """)
                    # Reposition button to account for open drawer
                    if hasattr(self, 'position_floating_button'):
                        parent_widget = self.floating_toggle_button.parent()
                        parent_size = parent_widget.size()
                        button_size = self.floating_toggle_button.size()
                        drawer_width = self.jog_drawer.width() if hasattr(self, 'jog_drawer') else 420
                        
                        x = parent_size.width() - button_size.width() - drawer_width
                        y = (parent_size.height() - button_size.height()) // 2
                        self.floating_toggle_button.move(x, y)
                else:
                    self.floating_toggle_button.setText("◀")  # Left arrow when closed (to open)
                    self.floating_toggle_button.setStyleSheet("""
                        QPushButton {
                            background-color: rgba(108, 117, 125, 0.9);
                            border: none;
                            color: white;
                            border-radius: 8px 0px 0px 8px;
                            font-size: 18px;
                            font-weight: bold;
                            margin: 0px;
                            padding: 0px;
                        }
                        QPushButton:hover {
                            background-color: rgba(90, 98, 104, 0.95);
                        }
                        QPushButton:pressed {
                            background-color: rgba(84, 91, 98, 1.0);
                        }
                    """)
                    # Reposition button to the right edge when drawer is closed
                    if hasattr(self, 'position_floating_button'):
                        self.position_floating_button(self.floating_toggle_button.parent())


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget

    app = QApplication(sys.argv)
    main_widget = QWidget()
    layout = CalibrationServiceTabLayout(main_widget)
    main_widget.setLayout(layout)
    main_widget.show()
    sys.exit(app.exec())

