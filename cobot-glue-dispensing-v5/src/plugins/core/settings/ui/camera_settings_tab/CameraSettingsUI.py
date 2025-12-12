"""
Main camera settings UI widget - DUMB component.

This widget provides camera configuration interface with preview functionality.
All business logic and controller_service calls are handled by SettingsAppWidget.

DUMB component - only emits signals and displays data, no business logic.
"""

import cv2
import numpy as np
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QScroller, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea

from communication_layer.api.v1.topics import VisionTopics
from core.model.settings.CameraSettings import CameraSettings
from core.model.settings.enums.CameraSettingKey import CameraSettingKey
from frontend.core.utils.localization import TranslationKeys, get_app_translator
from frontend.widgets.ToastWidget import ToastWidget
from modules.shared.MessageBroker import MessageBroker
from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout
from plugins.core.settings.ui.camera_settings_tab.utils import (
    CameraFrameProcessor,
    PreviewClickHandler,
    handle_brightness_area_point_selection,
    _apply_brightness_overlay_to_pixmap,
    create_camera_preview_section
)
from plugins.core.settings.ui.camera_settings_tab.groups import (
    CoreSettingsGroup,
    ContourSettingsGroup,
    PreprocessingSettingsGroup,
    CalibrationSettingsGroup,
    BrightnessSettingsGroup,
    ArucoSettingsGroup
)
from plugins.core.settings.ui.camera_settings_tab.translate import translate


class CameraSettingsUI(BaseSettingsTabLayout, QVBoxLayout):
    """
    Main camera settings UI - DUMB component.

    Provides:
    - Camera preview with real-time feed
    - Settings configuration (core, contour, preprocessing, calibration, brightness, ArUco)
    - Brightness area selection
    - Threshold preview

    All signals propagate to SettingsAppWidget for business logic handling.
    NO controller_service usage here - pure presentation.
    """

    # Unified signal for backward compatibility
    value_changed_signal = pyqtSignal(str, object, str)  # key, value, className

    # Action signals (emitted to SettingsAppWidget for handling)
    update_camera_feed_signal = QtCore.pyqtSignal()
    star_camera_requested = QtCore.pyqtSignal()
    stop_camera_requested = QtCore.pyqtSignal()
    capture_image_requested = QtCore.pyqtSignal()
    raw_mode_requested = QtCore.pyqtSignal(bool)
    show_processed_image_requested = QtCore.pyqtSignal()
    start_calibration_requested = QtCore.pyqtSignal()
    save_calibration_requested = QtCore.pyqtSignal()
    load_calibration_requested = QtCore.pyqtSignal()
    test_contour_detection_requested = QtCore.pyqtSignal()
    test_aruco_detection_requested = QtCore.pyqtSignal()
    save_settings_requested = QtCore.pyqtSignal()
    load_settings_requested = QtCore.pyqtSignal()
    reset_settings_requested = QtCore.pyqtSignal()

    def __init__(self, parent_widget, camera_settings: CameraSettings = None):
        """
        Initialize CameraSettingsUI.

        Args:
            parent_widget: Parent widget
            camera_settings: Camera settings model (loaded by SettingsAppWidget)
        """
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)

        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")

        self.raw_mode_active = False
        self.parent_widget = parent_widget
        self.camera_settings = camera_settings or CameraSettings()
        self.translator = get_app_translator()
        self.translator.language_changed.connect(lambda: translate(self))

        # Brightness area selection state
        self.brightness_area_selection_mode = False
        self.brightness_area_points = []
        self.brightness_area_overlay = None
        self.brightness_area_max_points = 4

        # Frame caches
        self.latest_frame_cache = None
        self.latest_threshold_cache = None

        # Preview click handlers (set when labels are created)
        self.camera_preview_handler = None
        self.threshold_preview_handler = None

        # Background frame processor for performance
        self.frame_processor = CameraFrameProcessor()
        self.frame_processor.frame_processed.connect(self._on_frame_processed)
        self.frame_processor.start()
        print("[CameraSettingsUI] Started background frame processor thread")

        # Create main content
        self.create_main_content()

        # Connect widget signals to unified emission pattern
        self._connect_widget_signals()

        # Performance optimization: 10 FPS instead of 33 FPS
        self.updateFrequency = 100
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._process_latest_cached_frame)
        self.timer_active = False
        print("[CameraSettingsUI] Timer created but not started (performance optimization)")

        # Connect parent resize if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

        # Subscribe to vision system messages
        broker = MessageBroker()
        broker.subscribe(topic=VisionTopics.SERVICE_STATE, callback=self.onVisionSystemStateUpdate)
        broker.subscribe(topic=VisionTopics.THRESHOLD_IMAGE, callback=self.update_threshold_preview_from_cv2)
        broker.subscribe(topic=VisionTopics.LATEST_IMAGE, callback=self._on_vision_frame_received)

    def _on_frame_processed(self, pixmap):
        """
        Slot called when background thread finishes processing a frame.
        Runs on the main GUI thread - just updates the pixmap.
        """
        if hasattr(self, 'camera_preview_label') and self.camera_preview_label:
            try:
                # Check if overlay is needed
                needs_overlay = False
                if not self.brightness_area_selection_mode:
                    points = self.camera_settings.get_brightness_area_points()
                    if points and len(points) == 4:
                        needs_overlay = True
                elif self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
                    needs_overlay = True

                if needs_overlay:
                    self.camera_preview_label._original_pixmap = pixmap
                    final_pixmap = _apply_brightness_overlay_to_pixmap(self, pixmap)
                else:
                    final_pixmap = pixmap

                self.camera_preview_label.setPixmap(final_pixmap)
                self.camera_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            except RuntimeError:
                pass  # Widget was deleted

    def _on_vision_frame_received(self, frame):
        """
        Callback from VisionService via MessageBroker.
        Cache the frame for the timer to pick up.
        """
        if self.timer_active:
            if isinstance(frame, dict):
                actual_frame = frame.get("image")
            else:
                actual_frame = frame
            self.latest_frame_cache = actual_frame

    def _process_latest_cached_frame(self):
        """
        Timer callback - sends cached frame to worker thread (non-blocking).
        """
        if self.latest_frame_cache is not None:
            self.frame_processor.add_frame(self.latest_frame_cache)

    def start_camera_updates(self):
        """Start the camera feed timer - call when tab becomes visible"""
        if hasattr(self, 'timer') and self.timer and not self.timer_active:
            print("[CameraSettingsUI] Starting camera feed timer")
            self.timer.start(self.updateFrequency)
            self.timer_active = True

    def stop_camera_updates(self):
        """Stop the camera feed timer - call when tab is hidden"""
        if hasattr(self, 'timer') and self.timer and self.timer_active:
            print("[CameraSettingsUI] Stopping camera feed timer")
            self.timer.stop()
            self.timer_active = False

    def onVisionSystemStateUpdate(self, message):
        """Update camera status based on vision system state"""
        state = message.get("state")
        if not hasattr(self, 'current_camera_state'):
            self.current_camera_state = None

        if self.current_camera_state == state:
            return

        self.current_camera_state = state

        if hasattr(self, 'camera_status_label') and self.camera_status_label is not None:
            self.camera_status_label.setText(
                f"{self.translator.get(TranslationKeys.CameraSettings.CAMERA_STATUS)}: {state}"
            )

            if state == "idle":
                self.camera_status_label.setStyleSheet("color: green; font-weight: bold;")
            elif state == "initializing":
                self.camera_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")
            else:
                self.camera_status_label.setStyleSheet("color: red; font-weight: bold;")

    def update_camera_feed(self, frame):
        """Update camera feed with new frame"""
        print(f"[CameraSettingsUI] update_camera_feed called")
        try:
            if frame is not None:
                self.frame_processor.add_frame(frame)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def update_threshold_preview_from_cv2(self, cv2_threshold_image):
        """Update threshold preview with CV2 image"""
        try:
            if len(cv2_threshold_image.shape) == 3:
                rgb_image = cv2_threshold_image[:, :, ::-1]  # BGR to RGB
                height, width = rgb_image.shape[:2]
                bytes_per_line = 3 * width
                q_image = QImage(rgb_image.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                height, width = cv2_threshold_image.shape[:2]
                bytes_per_line = width
                q_image = QImage(cv2_threshold_image.tobytes(), width, height, bytes_per_line,
                                QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            self.latest_threshold_cache = pixmap

        except RuntimeError as e:
            import traceback
            traceback.print_exc()
            print(f"Widget deleted during threshold preview update: {e}")

    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def clean_up(self):
        """Clean up resources"""
        print("[CameraSettingsUI] Starting cleanup")

        # Stop timer
        if hasattr(self, 'timer') and self.timer:
            print("[CameraSettingsUI] Stopping camera feed timer")
            self.timer.stop()
            self.timer = None

        # Stop frame processor thread
        if hasattr(self, 'frame_processor') and self.frame_processor:
            print("[CameraSettingsUI] Stopping frame processor thread")
            self.frame_processor.stop()
            self.frame_processor.wait(2000)
            print("[CameraSettingsUI] Frame processor thread stopped")

        # Unsubscribe from message broker
        try:
            broker = MessageBroker()
            broker.unsubscribe(VisionTopics.SERVICE_STATE, self.onVisionSystemStateUpdate)
            broker.unsubscribe(VisionTopics.THRESHOLD_IMAGE, self.update_threshold_preview_from_cv2)
            broker.unsubscribe(VisionTopics.LATEST_IMAGE, self._on_vision_frame_received)
            print("[CameraSettingsUI] Message broker subscriptions cleaned up")
        except Exception as e:
            print(f"[CameraSettingsUI] Warning: Error cleaning up message broker: {e}")

        print("[CameraSettingsUI] Cleanup completed")

    def create_main_content(self):
        """Create the main content with settings and preview"""
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # Settings scroll area (left side)
        settings_scroll_area = QScrollArea()
        settings_scroll_area.setWidgetResizable(True)
        settings_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        QScroller.grabGesture(settings_scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        settings_content_widget = QWidget()
        settings_content_layout = QVBoxLayout(settings_content_widget)
        settings_content_layout.setSpacing(20)
        settings_content_layout.setContentsMargins(0, 0, 0, 0)

        self.add_settings_to_layout(settings_content_layout)
        settings_content_layout.addStretch()

        settings_scroll_area.setWidget(settings_content_widget)

        # Camera preview section (right side)
        preview_widget = create_camera_preview_section(self)

        # Add both sections to main layout
        main_horizontal_layout.addWidget(preview_widget, 2)
        main_horizontal_layout.addWidget(settings_scroll_area, 1)

        main_widget = QWidget()
        main_widget.setLayout(main_horizontal_layout)
        self.addWidget(main_widget)

    def add_settings_to_layout(self, parent_layout):
        """Add all settings groups to the layout"""
        # First row
        first_row = QHBoxLayout()
        first_row.setSpacing(15)
        self.core_group = CoreSettingsGroup(self.camera_settings)
        self.contour_group = ContourSettingsGroup(self.camera_settings)
        first_row.addWidget(self.core_group)
        first_row.addWidget(self.contour_group)
        parent_layout.addLayout(first_row)

        # Second row
        second_row = QHBoxLayout()
        second_row.setSpacing(15)
        self.preprocessing_group = PreprocessingSettingsGroup(self.camera_settings)
        self.calibration_group = CalibrationSettingsGroup(self.camera_settings)
        second_row.addWidget(self.preprocessing_group)
        second_row.addWidget(self.calibration_group)
        parent_layout.addLayout(second_row)

        # Third row
        third_row = QHBoxLayout()
        third_row.setSpacing(15)
        self.brightness_group = BrightnessSettingsGroup(self.camera_settings, self)
        self.aruco_group = ArucoSettingsGroup(self.camera_settings)
        third_row.addWidget(self.brightness_group)
        third_row.addWidget(self.aruco_group)
        parent_layout.addLayout(third_row)

        translate(self)

    def _get_camera_frame_for_preview(self):
        """Callback for CameraFeed to get the latest camera frame (numpy array in RGB format) with overlays"""
        if self.latest_frame_cache is None:
            return None

        try:
            # Convert camera frame to RGB format expected by CameraFeed
            import cv2
            frame = self.latest_frame_cache

            # Handle different frame formats
            if len(frame.shape) == 3:
                # Color image - assume BGR and convert to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif len(frame.shape) == 2:
                # Grayscale - convert to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            else:
                print(f"Unsupported camera frame format: shape {frame.shape}")
                return None

            # Verify the result is a valid numpy array
            if not isinstance(rgb_frame, np.ndarray) or rgb_frame.size == 0:
                print(f"Color conversion failed: result is {type(rgb_frame)}")
                return None

            # CRITICAL FIX: Apply brightness area overlay before returning
            # Check if we need to draw brightness area overlay
            needs_overlay = False
            if not self.brightness_area_selection_mode:
                points = self.camera_settings.get_brightness_area_points()
                if points and len(points) == 4:
                    needs_overlay = True
            elif self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
                needs_overlay = True

            if needs_overlay:
                # Draw brightness area overlay on the numpy array
                rgb_frame = self._draw_brightness_overlay_on_frame(rgb_frame)

            return rgb_frame

        except Exception as e:
            print(f"Error converting camera frame: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _draw_brightness_overlay_on_frame(self, rgb_frame):
        """Draw brightness area overlay directly on numpy frame"""
        try:
            # Get original camera resolution
            original_width = self.camera_settings.get_camera_width()
            original_height = self.camera_settings.get_camera_height()

            # Get current frame dimensions
            frame_height, frame_width = rgb_frame.shape[:2]

            # Draw saved brightness area (if exists and not in selection mode)
            if not self.brightness_area_selection_mode:
                points = self.camera_settings.get_brightness_area_points()
                if points and len(points) == 4:
                    # Scale points from original camera coordinates to current frame coordinates
                    scaled_points = []
                    for p in points:
                        x = int((p[0] / original_width) * frame_width)
                        y = int((p[1] / original_height) * frame_height)
                        scaled_points.append((x, y))

                    # Draw polygon on the frame
                    scaled_points_array = np.array(scaled_points, dtype=np.int32)
                    cv2.polylines(rgb_frame, [scaled_points_array], isClosed=True,
                                 color=(0, 255, 0), thickness=2)  # Green color in RGB

            # Draw selection points if in selection mode
            if self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
                for i, point in enumerate(self.brightness_area_points):
                    # Scale from original camera coordinates to current frame coordinates
                    x = int((point[0] / original_width) * frame_width)
                    y = int((point[1] / original_height) * frame_height)

                    # Draw point circle
                    cv2.circle(rgb_frame, (x, y), 5, (255, 0, 0), -1)  # Red filled circle

                    # Draw point number
                    cv2.putText(rgb_frame, f"{i + 1}", (x - 5, y - 15),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # Draw lines between points
                if len(self.brightness_area_points) >= 2:
                    scaled_points = []
                    for point in self.brightness_area_points:
                        x = int((point[0] / original_width) * frame_width)
                        y = int((point[1] / original_height) * frame_height)
                        scaled_points.append((x, y))

                    # Draw lines
                    for i in range(len(scaled_points) - 1):
                        cv2.line(rgb_frame, scaled_points[i], scaled_points[i + 1],
                                (255, 255, 0), 2)  # Yellow lines

                    # Close the rectangle if we have 4 points
                    if len(scaled_points) == 4:
                        cv2.line(rgb_frame, scaled_points[3], scaled_points[0],
                                (255, 255, 0), 2)

            return rgb_frame

        except Exception as e:
            print(f"Error drawing brightness overlay: {e}")
            import traceback
            traceback.print_exc()
            return rgb_frame

    def _get_threshold_frame_for_preview(self):
        """Callback for CameraFeed to get the latest threshold frame (QPixmap)"""
        return self.latest_threshold_cache if self.latest_threshold_cache is not None else None

    def _on_camera_preview_clicked(self, event):
        """Handle mouse click on the camera preview feed"""
        # Get click position from the graphics view
        pos = event.pos()
        self.on_preview_clicked(pos.x(), pos.y())

    def _on_threshold_preview_clicked(self, event):
        """Handle mouse-click on the threshold preview feed"""
        # Get click position from the graphics view
        pos = event.pos()
        self.on_threshold_preview_clicked(pos.x(), pos.y())

    def on_preview_clicked(self, x, y):
        """Handle camera preview clicks"""
        try:
            if not self.camera_preview_handler:
                print("Camera preview handler not initialized")
                return

            original_width = self.camera_settings.get_camera_width()
            original_height = self.camera_settings.get_camera_height()

            result = self.camera_preview_handler.handle_click(
                x, y,
                scale_to_resolution=(original_width, original_height)
            )

            if result is None:
                return

            pixmap_x, pixmap_y = result['pixmap_coords']
            r, g, b = result['color_rgb']
            scaled_x, scaled_y = result['scaled_coords']

            # Handle brightness area selection mode
            if self.brightness_area_selection_mode:
                handle_brightness_area_point_selection(self, scaled_x, scaled_y)
                return

            # Default: show pixel info
            arr = np.uint8([[[r, g, b]]])
            gray = int(cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)[0, 0])

            print(f"Preview Clicked on {x}:{y} - pixel (R,G,B) = ({r},{g},{b}) - Grayscale = {gray}")
            self.showToast(f"(R,G,B) = ({r},{g},{b}) ; Grayscale = {gray}")

        except Exception as e:
            print(f"Exception in on_preview_clicked: {e}")
            import traceback
            traceback.print_exc()

    def on_threshold_preview_clicked(self, x, y):
        """Handle threshold preview clicks"""
        try:
            if not self.threshold_preview_handler:
                print("Threshold preview handler not initialized")
                return

            result = self.threshold_preview_handler.handle_click(x, y)

            if result is None:
                return

            pixmap_x, pixmap_y = result['pixmap_coords']
            r, g, b = result['color_rgb']
            gray = r
            threshold_value = "255" if gray > 127 else "0"

            print(f"Threshold Preview Clicked on {x}:{y} - pixel value = {gray}, threshold = {threshold_value}")
            self.showToast(f"Threshold value: {threshold_value} (gray: {gray})")

        except Exception as e:
            print(f"Exception in on_threshold_preview_clicked: {e}")
            import traceback
            traceback.print_exc()

    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 5)
            toast.show()

    def _connect_widget_signals(self):
        """Connect all widget signals to unified value_changed_signal"""
        widget_mappings = [
            # Core settings (from core_group)
            (self.core_group.camera_index_input, CameraSettingKey.INDEX.value, 'valueChanged'),
            (self.core_group.width_input, CameraSettingKey.WIDTH.value, 'valueChanged'),
            (self.core_group.height_input, CameraSettingKey.HEIGHT.value, 'valueChanged'),
            (self.core_group.skip_frames_input, CameraSettingKey.SKIP_FRAMES.value, 'valueChanged'),
            (self.core_group.capture_pos_offset_input, CameraSettingKey.CAPTURE_POS_OFFSET.value, 'valueChanged'),

            # Contour detection (from contour_group)
            (self.contour_group.contour_detection_toggle, CameraSettingKey.CONTOUR_DETECTION.value, 'toggled'),
            (self.contour_group.draw_contours_toggle, CameraSettingKey.DRAW_CONTOURS.value, 'toggled'),
            (self.contour_group.threshold_input, CameraSettingKey.THRESHOLD.value, 'valueChanged'),
            (self.contour_group.threshold_pickup_area_input, CameraSettingKey.THRESHOLD_PICKUP_AREA.value, 'valueChanged'),
            (self.contour_group.epsilon_input, CameraSettingKey.EPSILON.value, 'valueChanged'),
            (self.contour_group.min_contour_area_input, CameraSettingKey.MIN_CONTOUR_AREA.value, 'valueChanged'),
            (self.contour_group.max_contour_area_input, CameraSettingKey.MAX_CONTOUR_AREA.value, 'valueChanged'),

            # Preprocessing (from preprocessing_group)
            (self.preprocessing_group.gaussian_blur_toggle, CameraSettingKey.GAUSSIAN_BLUR.value, 'toggled'),
            (self.preprocessing_group.blur_kernel_input, CameraSettingKey.BLUR_KERNEL_SIZE.value, 'valueChanged'),
            (self.preprocessing_group.threshold_type_combo, CameraSettingKey.THRESHOLD_TYPE.value, 'currentTextChanged'),
            (self.preprocessing_group.dilate_enabled_toggle, CameraSettingKey.DILATE_ENABLED.value, 'toggled'),
            (self.preprocessing_group.dilate_kernel_input, CameraSettingKey.DILATE_KERNEL_SIZE.value, 'valueChanged'),
            (self.preprocessing_group.dilate_iterations_input, CameraSettingKey.DILATE_ITERATIONS.value, 'valueChanged'),
            (self.preprocessing_group.erode_enabled_toggle, CameraSettingKey.ERODE_ENABLED.value, 'toggled'),
            (self.preprocessing_group.erode_kernel_input, CameraSettingKey.ERODE_KERNEL_SIZE.value, 'valueChanged'),
            (self.preprocessing_group.erode_iterations_input, CameraSettingKey.ERODE_ITERATIONS.value, 'valueChanged'),

            # Calibration (from calibration_group)
            (self.calibration_group.chessboard_width_input, CameraSettingKey.CHESSBOARD_WIDTH.value, 'valueChanged'),
            (self.calibration_group.chessboard_height_input, CameraSettingKey.CHESSBOARD_HEIGHT.value, 'valueChanged'),
            (self.calibration_group.square_size_input, CameraSettingKey.SQUARE_SIZE_MM.value, 'valueChanged'),
            (self.calibration_group.calib_skip_frames_input, CameraSettingKey.CALIBRATION_SKIP_FRAMES.value, 'valueChanged'),

            # Brightness control (from brightness_group)
            (self.brightness_group.brightness_auto_toggle, CameraSettingKey.BRIGHTNESS_AUTO.value, 'toggled'),
            (self.brightness_group.kp_input, CameraSettingKey.BRIGHTNESS_KP.value, 'valueChanged'),
            (self.brightness_group.ki_input, CameraSettingKey.BRIGHTNESS_KI.value, 'valueChanged'),
            (self.brightness_group.kd_input, CameraSettingKey.BRIGHTNESS_KD.value, 'valueChanged'),
            (self.brightness_group.target_brightness_input, CameraSettingKey.TARGET_BRIGHTNESS.value, 'valueChanged'),

            # ArUco detection (from aruco_group)
            (self.aruco_group.aruco_enabled_toggle, CameraSettingKey.ARUCO_ENABLED.value, 'toggled'),
            (self.aruco_group.aruco_dictionary_combo, CameraSettingKey.ARUCO_DICTIONARY.value, 'currentTextChanged'),
            (self.aruco_group.aruco_flip_toggle, CameraSettingKey.ARUCO_FLIP_IMAGE.value, 'toggled'),
        ]

        for widget, setting_key, signal_name in widget_mappings:
            if hasattr(widget, signal_name):
                signal = getattr(widget, signal_name)
                signal.connect(
                    lambda value, key=setting_key: self._emit_setting_change(key, value)
                )

    def _emit_setting_change(self, key: str, value):
        """Emit unified value_changed_signal"""
        self.value_changed_signal.emit(key, value, self.className)

    def connect_default_callbacks(self):
        """Connect action button signals"""
        self.capture_image_button.clicked.connect(lambda: self.capture_image_requested.emit())
        self.show_raw_button.toggled.connect(self.toggle_raw_mode)
        self.start_calibration_button.clicked.connect(lambda: self.start_calibration_requested.emit())
        self.save_calibration_button.clicked.connect(lambda: self.save_calibration_requested.emit())
        self.load_calibration_button.clicked.connect(lambda: self.load_calibration_requested.emit())
        self.test_contour_button.clicked.connect(lambda: self.test_contour_detection_requested.emit())
        self.test_aruco_button.clicked.connect(lambda: self.test_aruco_detection_requested.emit())
        self.save_settings_button.clicked.connect(lambda: self.save_settings_requested.emit())
        self.load_settings_button.clicked.connect(lambda: self.load_settings_requested.emit())
        self.reset_settings_button.clicked.connect(lambda: self.reset_settings_requested.emit())

    def toggle_raw_mode(self, checked):
        """Toggle raw mode on/off"""
        self.raw_mode_active = checked

        if checked:
            self.show_raw_button.setText(self.translator.get(TranslationKeys.CameraSettings.EXIT_RAW_MODE))
            self.show_raw_button.setStyleSheet("QPushButton { background-color: #ff6b6b; }")
        else:
            self.show_raw_button.setText(self.translator.get(TranslationKeys.CameraSettings.RAW_MODE))
            self.show_raw_button.setStyleSheet("")

        self.raw_mode_requested.emit(self.raw_mode_active)

    def updateValues(self, camera_settings: CameraSettings):
        """Update UI with camera settings values"""
        print(f"[CameraSettingsUI] updateValues called")

        # Update internal camera_settings
        self.camera_settings = camera_settings

        # Collect all widgets (now accessing through group objects)
        widgets = [
            # Core group
            self.core_group.camera_index_input, self.core_group.width_input, self.core_group.height_input,
            self.core_group.skip_frames_input, self.core_group.capture_pos_offset_input,
            # Contour group
            self.contour_group.contour_detection_toggle, self.contour_group.draw_contours_toggle,
            self.contour_group.threshold_input, self.contour_group.threshold_pickup_area_input,
            self.contour_group.epsilon_input, self.contour_group.min_contour_area_input,
            self.contour_group.max_contour_area_input,
            # Preprocessing group
            self.preprocessing_group.gaussian_blur_toggle,
            self.preprocessing_group.blur_kernel_input, self.preprocessing_group.threshold_type_combo,
            self.preprocessing_group.dilate_enabled_toggle, self.preprocessing_group.dilate_kernel_input,
            self.preprocessing_group.dilate_iterations_input, self.preprocessing_group.erode_enabled_toggle,
            self.preprocessing_group.erode_kernel_input, self.preprocessing_group.erode_iterations_input,
            # Calibration group
            self.calibration_group.chessboard_width_input, self.calibration_group.chessboard_height_input,
            self.calibration_group.square_size_input, self.calibration_group.calib_skip_frames_input,
            # Brightness group
            self.brightness_group.brightness_auto_toggle, self.brightness_group.kp_input, self.brightness_group.ki_input,
            self.brightness_group.kd_input, self.brightness_group.target_brightness_input,
            # ArUco group
            self.aruco_group.aruco_enabled_toggle, self.aruco_group.aruco_dictionary_combo,
            self.aruco_group.aruco_flip_toggle
        ]

        # Block signals to prevent triggering save operations
        for widget in widgets:
            widget.blockSignals(True)

        try:
            # Core settings
            self.core_group.camera_index_input.setValue(camera_settings.get_camera_index())
            self.core_group.width_input.setValue(camera_settings.get_camera_width())
            self.core_group.height_input.setValue(camera_settings.get_camera_height())
            self.core_group.skip_frames_input.setValue(camera_settings.get_skip_frames())
            self.core_group.capture_pos_offset_input.setValue(camera_settings.get_capture_pos_offset())

            # Contour detection
            self.contour_group.contour_detection_toggle.setChecked(camera_settings.get_contour_detection())
            self.contour_group.draw_contours_toggle.setChecked(camera_settings.get_draw_contours())
            self.contour_group.threshold_input.setValue(camera_settings.get_threshold())
            self.contour_group.threshold_pickup_area_input.setValue(camera_settings.get_threshold_pickup_area())
            self.contour_group.epsilon_input.setValue(camera_settings.get_epsilon())
            self.contour_group.min_contour_area_input.setValue(camera_settings.get_min_contour_area())
            self.contour_group.max_contour_area_input.setValue(camera_settings.get_max_contour_area())

            # Preprocessing
            self.preprocessing_group.gaussian_blur_toggle.setChecked(camera_settings.get_gaussian_blur())
            self.preprocessing_group.blur_kernel_input.setValue(camera_settings.get_blur_kernel_size())
            self.preprocessing_group.threshold_type_combo.setCurrentText(camera_settings.get_threshold_type())
            self.preprocessing_group.dilate_enabled_toggle.setChecked(camera_settings.get_dilate_enabled())
            self.preprocessing_group.dilate_kernel_input.setValue(camera_settings.get_dilate_kernel_size())
            self.preprocessing_group.dilate_iterations_input.setValue(camera_settings.get_dilate_iterations())
            self.preprocessing_group.erode_enabled_toggle.setChecked(camera_settings.get_erode_enabled())
            self.preprocessing_group.erode_kernel_input.setValue(camera_settings.get_erode_kernel_size())
            self.preprocessing_group.erode_iterations_input.setValue(camera_settings.get_erode_iterations())

            # Calibration
            self.calibration_group.chessboard_width_input.setValue(camera_settings.get_chessboard_width())
            self.calibration_group.chessboard_height_input.setValue(camera_settings.get_chessboard_height())
            self.calibration_group.square_size_input.setValue(camera_settings.get_square_size_mm())
            self.calibration_group.calib_skip_frames_input.setValue(camera_settings.get_calibration_skip_frames())

            # Brightness control
            self.brightness_group.brightness_auto_toggle.setChecked(camera_settings.get_brightness_auto())
            self.brightness_group.kp_input.setValue(camera_settings.get_brightness_kp())
            self.brightness_group.ki_input.setValue(camera_settings.get_brightness_ki())
            self.brightness_group.kd_input.setValue(camera_settings.get_brightness_kd())
            self.brightness_group.target_brightness_input.setValue(camera_settings.get_target_brightness())

            # ArUco detection
            self.aruco_group.aruco_enabled_toggle.setChecked(camera_settings.get_aruco_enabled())
            self.aruco_group.aruco_dictionary_combo.setCurrentText(camera_settings.get_aruco_dictionary())
            self.aruco_group.aruco_flip_toggle.setChecked(camera_settings.get_aruco_flip_image())

        finally:
            # Always unblock signals
            for widget in widgets:
                widget.blockSignals(False)

        # Update toggle widget visuals
        toggle_widgets = [
            self.contour_group.contour_detection_toggle, self.contour_group.draw_contours_toggle,
            self.preprocessing_group.gaussian_blur_toggle, self.preprocessing_group.dilate_enabled_toggle,
            self.preprocessing_group.erode_enabled_toggle, self.brightness_group.brightness_auto_toggle,
            self.aruco_group.aruco_enabled_toggle, self.aruco_group.aruco_flip_toggle
        ]
        for toggle in toggle_widgets:
            if hasattr(toggle, 'update_pos_color'):
                toggle.update_pos_color(toggle.isChecked())

        print("Camera settings updated from CameraSettings object.")