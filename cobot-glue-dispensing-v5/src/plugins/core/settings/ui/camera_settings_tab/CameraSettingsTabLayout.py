from PyQt6 import QtCore
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QPen, QFont, QBrush
from PyQt6.QtWidgets import QScroller, QWidget
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QScrollArea)

from communication_layer.api.v1.topics import VisionTopics
from core.model.settings.CameraSettings import CameraSettings
from core.model.settings.enums.CameraSettingKey import CameraSettingKey
from frontend.widgets.ToastWidget import ToastWidget
from modules.shared.MessageBroker import MessageBroker
from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout
import cv2
from frontend.core.utils.localization import TranslationKeys, get_app_translator
from plugins.core.settings.ui.camera_settings_tab.camera_frame_processor import CameraFrameProcessor
from plugins.core.settings.ui.camera_settings_tab.settings_groups.create_aruco_settings_group import \
    create_aruco_settings_group
from plugins.core.settings.ui.camera_settings_tab.settings_groups.create_brightness_settings_group import \
    create_brightness_settings_group
from plugins.core.settings.ui.camera_settings_tab.settings_groups.create_calibration_settings_group import \
    create_calibration_settings_group
from plugins.core.settings.ui.camera_settings_tab.create_camera_preview_section import create_camera_preview_section
from plugins.core.settings.ui.camera_settings_tab.settings_groups.create_contour_settings_group import \
    create_contour_settings_group
from plugins.core.settings.ui.camera_settings_tab.settings_groups.create_core_settings_group import \
    create_core_settings_group
from plugins.core.settings.ui.camera_settings_tab.settings_groups.create_preprocessing_settings_group import \
    create_preprocessing_settings_group
from plugins.core.settings.ui.camera_settings_tab.translate import translate


class CameraSettingsTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    # Unified signal for all value changes - eliminates callback duplication
    value_changed_signal = pyqtSignal(str, object, str)  # key, value, component_type

    # Action signals
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

    def __init__(self, parent_widget, camera_settings: CameraSettings = None, update_camera_feed_callback=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")
        self.raw_mode_active = False
        self.parent_widget = parent_widget
        self.camera_settings = camera_settings or CameraSettings()
        self.translator = get_app_translator()
        self.translator.language_changed.connect(lambda :translate(self))
        self.update_camera_feed_callback = update_camera_feed_callback

        # Brightness area selection state
        self.brightness_area_selection_mode = False
        self.brightness_area_points = []  # Temporary storage during selection
        self.brightness_area_overlay = None  # Visual feedback overlay
        self.brightness_area_max_points = 4  # Number of points to collect

        # Initialize latest frame cache
        self.latest_frame_cache = None

        # PERFORMANCE OPTIMIZATION: Create background worker thread for image processing
        self.frame_processor = CameraFrameProcessor()
        self.frame_processor.frame_processed.connect(self._on_frame_processed)
        self.frame_processor.start()
        print("[CameraSettingsTabLayout] Started background frame processor thread")

        # Create main content with new layout
        self.create_main_content()

        # Connect all widget signals to unified emission pattern
        self._connect_widget_signals()

        # PERFORMANCE FIX: Reduce timer frequency and don't start by default
        # Only update camera preview when settings tab is actually visible
        self.updateFrequency = 100  # Changed from 30ms to 100ms (10 FPS instead of 33 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._process_latest_cached_frame)
        # Don't start timer by default - let it be controlled by visibility
        self.timer_active = False
        print("[CameraSettingsTabLayout] Timer created but not started (performance optimization)")

        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

        broker = MessageBroker()
        broker.subscribe(topic=VisionTopics.SERVICE_STATE,
                         callback=self.onVisionSystemStateUpdate)
        broker.subscribe(topic=VisionTopics.THRESHOLD_IMAGE,
                         callback=self.update_threshold_preview_from_cv2)
        broker.subscribe(topic=VisionTopics.LATEST_IMAGE,
                         callback=self._on_vision_frame_received)

    def _apply_brightness_overlay_to_pixmap(self, pixmap):
        """
        Apply brightness area overlay to the given pixmap and return the modified pixmap.

        Args:
            pixmap: The QPixmap to apply overlay to

        Returns:
            QPixmap with overlay applied, or original if no overlay needed
        """
        try:
            # Determine if we need to draw any overlays
            needs_overlay = False

            # Check if we need to draw saved brightness area (not in selection mode)
            if not self.brightness_area_selection_mode:
                points = self.camera_settings.get_brightness_area_points()
                if points and len(points) == 4:
                    needs_overlay = True

            # Check if we need to draw selection elements
            if self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
                needs_overlay = True

            # If no overlay needed, return original pixmap
            if not needs_overlay:
                return pixmap

            # Create a copy to draw on
            overlay_pixmap = pixmap.copy()

            from PyQt6.QtGui import QPainter

            painter = QPainter(overlay_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw saved brightness area (if exists and not in selection mode)
            if not self.brightness_area_selection_mode:
                self._draw_saved_brightness_area(painter)

            # Draw current selection points and area preview
            if self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
                self._draw_selection_points(painter)

                # Draw partial area preview if we have 2 or more points
                if len(self.brightness_area_points) >= 2:
                    self._draw_selection_preview(painter)

            painter.end()

            return overlay_pixmap

        except Exception as e:
            print(f"Exception in _apply_brightness_overlay_to_pixmap: {e}")
            import traceback
            traceback.print_exc()
            return pixmap  # Return original on error

    def _on_frame_processed(self, pixmap):
        """
        Slot called when background thread finishes processing a frame.
        Runs on main GUI thread - just updates the pixmap (fast operation).
        """
        if hasattr(self, 'camera_preview_label') and self.camera_preview_label:
            try:
                # PERFORMANCE: Only copy pixmap if we actually need overlays
                # Check if overlay is needed before doing expensive copy
                needs_overlay = False
                if not self.brightness_area_selection_mode:
                    points = self.camera_settings.get_brightness_area_points()
                    if points and len(points) == 4:
                        needs_overlay = True
                elif self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
                    needs_overlay = True

                if needs_overlay:
                    # Store original only when needed
                    self.camera_preview_label._original_pixmap = pixmap
                    # Apply brightness area overlay
                    final_pixmap = self._apply_brightness_overlay_to_pixmap(pixmap)
                else:
                    # No overlay needed - use pixmap directly (no copy!)
                    final_pixmap = pixmap

                # Fast operation - just set the already-scaled pixmap
                self.camera_preview_label.setPixmap(final_pixmap)
                self.camera_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            except RuntimeError:
                # Widget was deleted
                pass

    def _on_vision_frame_received(self, frame):
        """
        Callback from VisionService via MessageBroker (runs in VisionService thread).
        Cache the frame for the timer to pick up - avoids blocking main thread!
        """
        if self.timer_active:  # Only cache frames when timer is active
            # Handle both dict-wrapped frames and direct numpy arrays
            if isinstance(frame, dict):
                # Frame is wrapped in dict with "image" key (from MessagePublisher)
                actual_frame = frame.get("image")
            else:
                # Frame is direct numpy array (from VisionService)
                actual_frame = frame

            self.latest_frame_cache = actual_frame

    def _process_latest_cached_frame(self):
        """
        Timer callback - sends cached frame to worker thread (non-blocking).
        This runs on main thread but is super fast - just checks cache and delegates to worker.
        """
        if self.latest_frame_cache is not None:
            # Send to worker thread for processing (non-blocking)
            self.frame_processor.add_frame(self.latest_frame_cache)
            # Don't clear cache - let it be overwritten by newer frames

    def start_camera_updates(self):
        """Start the camera feed timer - call this when tab becomes visible"""
        if hasattr(self, 'timer') and self.timer and not self.timer_active:
            print("[CameraSettingsTabLayout] Starting camera feed timer")
            self.timer.start(self.updateFrequency)
            self.timer_active = True

    def stop_camera_updates(self):
        """Stop the camera feed timer - call this when tab is hidden or widget cleanup"""
        if hasattr(self, 'timer') and self.timer and self.timer_active:
            print("[CameraSettingsTabLayout] Stopping camera feed timer")
            self.timer.stop()
            self.timer_active = False

    """CAMERA PREVIEW METHODS"""

    def onVisionSystemStateUpdate(self, message):
        state = message.get("state")
        # Check if we need to initialize the current state
        if not hasattr(self, 'current_camera_state'):
            self.current_camera_state = None

        # Only update if state has changed
        if self.current_camera_state == state:
            return  # No change, skip update

        self.current_camera_state = state

        if hasattr(self, 'camera_status_label') and self.camera_status_label is not None:
            self.camera_status_label.setText(
                f"{self.translator.get(TranslationKeys.CameraSettings.CAMERA_STATUS)}: {state}")

            # Set label color based on state
            if state == "idle":
                self.camera_status_label.setStyleSheet("color: green; font-weight: bold;")
            elif state == "initializing":
                self.camera_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")  # Orange/yellow
            else:
                self.camera_status_label.setStyleSheet("color: red; font-weight: bold;")  # Default for other states
        else:
            print(f"Camera status update received but label not ready: {state}")

    def update_camera_feed(self, frame):
        print(f"[CameraSettingsTabLayout] update_camera_feed called")
        try:
            if frame is not None:
                # Send frame to background worker thread for processing
                self.frame_processor.add_frame(frame)
            else:
                return
        except Exception as e:
            import traceback
            traceback.print_exc()

    def update_camera_preview(self, pixmap):
        """Update the camera preview with a new frame, maintaining 16:9 aspect ratio"""
        if hasattr(self, 'camera_preview_label'):
            label_size = self.camera_preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.camera_preview_label.setPixmap(scaled_pixmap)
            self.camera_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_threshold_preview_from_cv2(self, cv2_threshold_image):
        """Update the threshold preview with a threshold image"""
        if not self._is_widget_valid('threshold_preview_label'):
            return

        try:
            # Convert to RGB if needed
            if len(cv2_threshold_image.shape) == 3:
                rgb_image = cv2_threshold_image[:, :, ::-1]  # BGR to RGB
                height, width = rgb_image.shape[:2]
                bytes_per_line = 3 * width
                q_image = QImage(rgb_image.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                # Grayscale threshold image
                height, width = cv2_threshold_image.shape[:2]
                bytes_per_line = width
                q_image = QImage(cv2_threshold_image.tobytes(), width, height, bytes_per_line,
                                 QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            self.update_threshold_preview(pixmap)
        except RuntimeError as e:
            import traceback
            traceback.print_exc()
            # Widget was deleted during execution
            print(f"Widget deleted during threshold preview update: {e}")
            self._cleanup_if_destroyed()

    def update_threshold_preview(self, pixmap):
        """Update the threshold preview with a new pixmap, maintaining aspect ratio"""
        if not self._is_widget_valid('threshold_preview_label'):
            return

        try:
            label_size = self.threshold_preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.threshold_preview_label.setPixmap(scaled_pixmap)
            self.threshold_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except RuntimeError as e:
            import traceback
            traceback.print_exc()
            # Widget was deleted during execution
            print(f"Widget deleted during threshold preview update: {e}")
            self._cleanup_if_destroyed()

    def update_camera_status(self, status, is_connected=False):
        """Update the camera status label"""
        if hasattr(self, 'camera_status_label'):
            color = "#4caf50" if is_connected else "#d32f2f"
            self.camera_status_label.setText(f"Camera Status: {status}")
            self.camera_status_label.setStyleSheet(f"font-weight: bold; color: {color};")

    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def update_layout_for_screen_size(self):
        """Update layout based on current screen size"""
        self.clear_layout()
        self.create_main_content()

    def _is_widget_valid(self, widget_name):
        """Check if a widget exists and is still valid (not deleted)"""
        if not hasattr(self, widget_name):
            return False
        widget = getattr(self, widget_name)
        try:
            # Try to access a basic property to see if widget is still valid
            _ = widget.isVisible()
            return True
        except RuntimeError:
            # Widget has been deleted
            return False

    def _cleanup_if_destroyed(self):
        """Clean up MessageBroker subscriptions if widget is destroyed"""
        try:
            broker = MessageBroker()
            broker.unsubscribe(VisionTopics.SERVICE_STATE, self.onVisionSystemStateUpdate)
            broker.unsubscribe(VisionTopics.THRESHOLD_IMAGE, self.update_threshold_preview_from_cv2)
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def clean_up(self):
        print("[CameraSettingsTabLayout] Starting cleanup")
        
        # CRITICAL FIX: Stop the timer to prevent continuous camera feed requests
        if hasattr(self, 'timer') and self.timer:
            print("[CameraSettingsTabLayout] Stopping camera feed timer")
            self.timer.stop()
            self.timer = None
        
        # Stop and cleanup the background worker thread
        if hasattr(self, 'frame_processor') and self.frame_processor:
            print("[CameraSettingsTabLayout] Stopping frame processor thread")
            self.frame_processor.stop()
            self.frame_processor.wait(2000)  # Wait up to 2 seconds for thread to finish
            print("[CameraSettingsTabLayout] Frame processor thread stopped")
        
        # Clean up message broker subscriptions
        try:
            broker = MessageBroker()
            broker.unsubscribe(VisionTopics.SERVICE_STATE, self.onVisionSystemStateUpdate)
            broker.unsubscribe(VisionTopics.THRESHOLD_IMAGE, self.update_threshold_preview_from_cv2)
            broker.unsubscribe(VisionTopics.LATEST_IMAGE, self._on_vision_frame_received)
            print("[CameraSettingsTabLayout] Message broker subscriptions cleaned up")
        except Exception as e:
            print(f"[CameraSettingsTabLayout] Warning: Error cleaning up message broker subscriptions: {e}")
        
        print("[CameraSettingsTabLayout] Cleanup completed")

    def clear_layout(self):
        """Clear all widgets from the layout"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def create_main_content(self):
        """Create the main content with settings on left and preview on right"""
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # Create settings scroll area (left side)
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

        # Create camera preview section (right side)
        preview_widget = create_camera_preview_section(self)

        # Add both sections to main horizontal layout
        main_horizontal_layout.addWidget(preview_widget, 2)
        main_horizontal_layout.addWidget(settings_scroll_area, 1)

        main_widget = QWidget()
        main_widget.setLayout(main_horizontal_layout)
        self.addWidget(main_widget)

    def add_settings_to_layout(self, parent_layout):
        """Add all settings groups to the layout in vertical arrangement"""
        # First row of settings
        first_row = QHBoxLayout()
        first_row.setSpacing(15)

        self.core_group = create_core_settings_group(self)
        self.contour_group = create_contour_settings_group(self)

        first_row.addWidget(self.core_group)
        first_row.addWidget(self.contour_group)

        parent_layout.addLayout(first_row)

        # Second row of settings
        second_row = QHBoxLayout()
        second_row.setSpacing(15)

        self.preprocessing_group = create_preprocessing_settings_group(self)
        self.calibration_group = create_calibration_settings_group(self)

        second_row.addWidget(self.preprocessing_group)
        second_row.addWidget(self.calibration_group)

        parent_layout.addLayout(second_row)

        # Third row of settings
        third_row = QHBoxLayout()
        third_row.setSpacing(15)

        self.brightness_group = create_brightness_settings_group(self)
        self.aruco_group = create_aruco_settings_group(self)

        third_row.addWidget(self.brightness_group)
        third_row.addWidget(self.aruco_group)

        parent_layout.addLayout(third_row)
        translate(self)

    def on_preview_clicked(self, x, y):
        try:
            label = getattr(self, "camera_preview_label", None)
            pixmap = label.pixmap() if label is not None else None
            if pixmap is None:
                print(f"Preview Clicked on {x}:{y} - no image available")
                return

            label_w = label.width()
            label_h = label.height()
            img_w = pixmap.width()
            img_h = pixmap.height()

            # Calculate top-left of the drawn pixmap inside the label (centered alignment)
            left = (label_w - img_w) // 2
            top = (label_h - img_h) // 2

            # Map click coordinates to pixmap coordinates
            ix = int(x - left)
            iy = int(y - top)

            if not (0 <= ix < img_w and 0 <= iy < img_h):
                print(f"Preview Clicked on {x}:{y} - outside image area")
                return

            # Scale coordinates from preview to original camera resolution
            # Get original camera resolution from settings
            original_width = self.camera_settings.get_camera_width()
            original_height = self.camera_settings.get_camera_height()
            
            # Scale the coordinates
            scaled_x = int((ix / img_w) * original_width)
            scaled_y = int((iy / img_h) * original_height)

            # Handle brightness area selection mode
            if self.brightness_area_selection_mode:
                self.handle_brightness_area_point_selection(scaled_x, scaled_y)
                return

            # Default behavior: show pixel info
            qimage = pixmap.toImage()
            color = qimage.pixelColor(ix, iy)
            r, g, b = color.red(), color.green(), color.blue()

            # Use OpenCV to convert the RGB pixel to grayscale
            import numpy as np
            arr = np.uint8([[[r, g, b]]])  # shape (1,1,3)
            gray = int(cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)[0, 0])

            # Print RGB and grayscale value
            print(f"Preview Clicked on {x}:{y} - pixel (R,G,B) = ({r},{g},{b}) - Grayscale = {gray}")

            self.showToast(f"(R,G,B) = ({r},{g},{b}) ; Grayscale = {gray}")
        except Exception as e:
            print(f"Exception in on_preview_clicked: {e}")

    def handle_brightness_area_point_selection(self, x, y):
        """Handle point selection for brightness area definition."""
        try:
            # Add the point to our temporary list
            self.brightness_area_points.append([x, y])
            point_num = len(self.brightness_area_points)
            
            self.showToast(f"Point {point_num}/4 selected: ({x}, {y})")
            
            # Check if we have collected all points
            if len(self.brightness_area_points) >= self.brightness_area_max_points:
                self.finish_brightness_area_selection()
            else:
                # Update visual feedback for partial selection
                self.update_brightness_area_overlay()
                
        except Exception as e:
            print(f"Exception in handle_brightness_area_point_selection: {e}")

    def finish_brightness_area_selection(self):
        """Complete brightness area selection and save points."""
        try:
            if len(self.brightness_area_points) == 4:
                # Save the points to camera settings
                from core.model.settings.enums.CameraSettingKey import CameraSettingKey
                self.camera_settings.set_brightness_area_points(self.brightness_area_points)
                
                # Emit value changed signals for each point to trigger settings save
                for i, point in enumerate(self.brightness_area_points):
                    key = [CameraSettingKey.BRIGHTNESS_AREA_P1.value, CameraSettingKey.BRIGHTNESS_AREA_P2.value,
                           CameraSettingKey.BRIGHTNESS_AREA_P3.value, CameraSettingKey.BRIGHTNESS_AREA_P4.value][i]
                    self.value_changed_signal.emit(key, point, self.className)
                
                self.showToast("Brightness area saved successfully!")
                
                # Update status display
                if hasattr(self, 'brightness_area_status_label'):
                    self.brightness_area_status_label.setText(self.get_brightness_area_status_text())
                
                # Exit selection mode
                self.toggle_brightness_area_selection_mode(False)
            else:
                self.showToast("Error: Need exactly 4 points for brightness area")
                
        except Exception as e:
            print(f"Exception in finish_brightness_area_selection: {e}")
            self.showToast(f"Error saving brightness area: {e}")

    def toggle_brightness_area_selection_mode(self, enable=None):
        """Toggle brightness area selection mode on/off."""
        try:
            if enable is None:
                enable = not self.brightness_area_selection_mode
                
            self.brightness_area_selection_mode = enable
            
            if enable:
                # Starting selection mode
                self.brightness_area_points = []
                self.showToast("Select 4 corner points for brightness area")
                self.update_brightness_area_overlay()
            else:
                # Exiting selection mode
                self.brightness_area_points = []
                self.update_brightness_area_overlay()
                
        except Exception as e:
            print(f"Exception in toggle_brightness_area_selection_mode: {e}")
            import traceback
            traceback.print_exc()

    def update_brightness_area_overlay(self):
        """Update visual overlay to show current brightness area and selection state."""
        try:
            if not hasattr(self, 'camera_preview_label'):
                return
            
            # Get the current pixmap from the camera preview
            original_pixmap = getattr(self.camera_preview_label, '_original_pixmap', None)
            if original_pixmap is None:
                # If no original pixmap stored, use current pixmap as base
                current_pixmap = self.camera_preview_label.pixmap()
                if current_pixmap is not None:
                    original_pixmap = current_pixmap.copy()
                else:
                    return
            
            # Determine if we need to draw any overlays
            needs_overlay = False
            
            # Check if we need to draw saved brightness area (not in selection mode)
            if not self.brightness_area_selection_mode:
                points = self.camera_settings.get_brightness_area_points()
                if points and len(points) == 4:
                    needs_overlay = True
            
            # Check if we need to draw selection elements
            if self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
                needs_overlay = True
            
            # If no overlay needed, just update with original pixmap
            if not needs_overlay:
                self.update_camera_preview(original_pixmap)
                return
            
            # Create a copy to draw on
            overlay_pixmap = original_pixmap.copy()
            
            from PyQt6.QtGui import QPainter, QPen, QBrush, QFont
            from PyQt6.QtCore import Qt
            
            painter = QPainter(overlay_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw saved brightness area (if exists and not in selection mode)
            if not self.brightness_area_selection_mode:
                self._draw_saved_brightness_area(painter)
            
            # Draw current selection points and area preview
            if self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
                self._draw_selection_points(painter)
                
                # Draw partial area preview if we have 2 or more points
                if len(self.brightness_area_points) >= 2:
                    self._draw_selection_preview(painter)
            
            painter.end()
            
            # Update the camera preview with the overlay using proper scaling
            self.update_camera_preview(overlay_pixmap)
            
        except Exception as e:
            print(f"Exception in update_brightness_area_overlay: {e}")

    def _draw_saved_brightness_area(self, painter):
        """Draw the currently saved brightness area."""
        try:
            points = self.camera_settings.get_brightness_area_points()
            if points and len(points) == 4:
                # Get scaling factors to convert from original image coordinates to preview coordinates
                original_width = self.camera_settings.get_camera_width()
                original_height = self.camera_settings.get_camera_height()
                
                # Get the current pixmap dimensions for scaling
                original_pixmap = getattr(self.camera_preview_label, '_original_pixmap', None)
                if original_pixmap is None:
                    print("No original pixmap available for coordinate scaling")
                    return
                    
                preview_width = original_pixmap.width()
                preview_height = original_pixmap.height()
                
                # Scale points from original camera coordinates to preview coordinates
                scaled_points = []
                for p in points:
                    preview_x = int((p[0] / original_width) * preview_width)
                    preview_y = int((p[1] / original_height) * preview_height)
                    scaled_points.append([preview_x, preview_y])
                
                # Set up drawing style for saved area
                pen = QPen(Qt.GlobalColor.green)
                pen.setWidth(2)
                pen.setStyle(Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                
                # Draw the rectangle connecting the 4 scaled points
                from PyQt6.QtCore import QPoint
                from PyQt6.QtGui import QPolygon
                
                qpoints = [QPoint(int(p[0]), int(p[1])) for p in scaled_points]
                polygon = QPolygon(qpoints)
                painter.drawPolygon(polygon)
                
                # Label it at the center of scaled points
                center_x = sum(p[0] for p in scaled_points) // 4
                center_y = sum(p[1] for p in scaled_points) // 4
                


        except Exception as e:
            print(f"Exception in _draw_saved_brightness_area: {e}")

    def _draw_selection_points(self, painter):
        """Draw the currently selected points during area selection."""
        try:
            # Set up drawing style for selection points
            pen = QPen(Qt.GlobalColor.red)
            pen.setWidth(3)
            painter.setPen(pen)
            brush = QBrush(Qt.GlobalColor.red)
            painter.setBrush(brush)
            
            # Draw each selected point
            for i, point in enumerate(self.brightness_area_points):
                x, y = point[0], point[1]
                
                # Draw point circle
                painter.drawEllipse(int(x-5), int(y-5), 10, 10)
                
                # Draw point number
                font = QFont()
                font.setPointSize(12)
                font.setBold(True)
                painter.setFont(font)
                
                # White text on red background
                painter.setPen(QPen(Qt.GlobalColor.white))
                painter.drawText(int(x-5), int(y-15), f"{i+1}")
                
        except Exception as e:
            print(f"Exception in _draw_selection_points: {e}")

    def _draw_selection_preview(self, painter):
        """Draw preview of area being selected."""
        try:
            if len(self.brightness_area_points) < 2:
                return
                
            # Set up drawing style for selection preview
            pen = QPen(Qt.GlobalColor.yellow)
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            
            # Draw lines between selected points
            for i in range(len(self.brightness_area_points) - 1):
                p1 = self.brightness_area_points[i]
                p2 = self.brightness_area_points[i + 1]
                painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
            
            # If we have 4 points, close the rectangle
            if len(self.brightness_area_points) == 4:
                p_last = self.brightness_area_points[-1]
                p_first = self.brightness_area_points[0]
                painter.drawLine(int(p_last[0]), int(p_last[1]), int(p_first[0]), int(p_first[1]))
                
        except Exception as e:
            print(f"Exception in _draw_selection_preview: {e}")

    def store_original_pixmap(self, pixmap):
        """Store the original pixmap before overlay modifications."""
        if hasattr(self, 'camera_preview_label'):
            self.camera_preview_label._original_pixmap = pixmap.copy()

    def refresh_brightness_area_display(self):
        """Refresh the brightness area display to show current saved settings."""
        try:
            print("=== Refreshing brightness area display ===")
            
            # Force reload the camera settings from the saved file to get latest values
            try:
                from core.application.ApplicationContext import get_core_settings_path
                import json
                from pathlib import Path
                
                # Load the actual saved settings from file
                camera_settings_path = get_core_settings_path("camera_settings.json")
                if Path(camera_settings_path).exists():
                    with open(camera_settings_path, 'r') as f:
                        saved_data = json.load(f)
                    
                    print(f"Loaded settings from file: {saved_data}")
                    
                    # Update our camera settings instance with the saved data
                    if saved_data:
                        self.camera_settings.updateSettings(saved_data)
                        print("Updated camera_settings instance with saved data")
                    
            except Exception as e:
                print(f"Error reloading camera settings: {e}")
            
            points = self.camera_settings.get_brightness_area_points()
            print(f"Current brightness area points from settings: {points}")
            
            # Update the status label to show current area
            if hasattr(self, 'brightness_area_status_label'):
                status_text = self.get_brightness_area_status_text()
                print(f"Setting status label to: {status_text}")
                self.brightness_area_status_label.setText(status_text)
            
            # Update the visual overlay to show current area
            self.update_brightness_area_overlay()
            
        except Exception as e:
            print(f"Exception in refresh_brightness_area_display: {e}")
            import traceback
            traceback.print_exc()

    def reset_brightness_area(self):
        """Reset brightness area to default values."""
        try:
            # Reset to default hardcoded values from brightness_manager.py
            default_points = [[940, 612], [1004, 614], [1004, 662], [940, 660]]
            self.camera_settings.set_brightness_area_points(default_points)
            
            # Emit value changed signals for each point to trigger settings save
            from core.model.settings.enums.CameraSettingKey import CameraSettingKey
            for i, point in enumerate(default_points):
                key = [CameraSettingKey.BRIGHTNESS_AREA_P1.value, CameraSettingKey.BRIGHTNESS_AREA_P2.value,
                       CameraSettingKey.BRIGHTNESS_AREA_P3.value, CameraSettingKey.BRIGHTNESS_AREA_P4.value][i]
                self.value_changed_signal.emit(key, point, self.className)
            
            # Update status display
            if hasattr(self, 'brightness_area_status_label'):
                self.brightness_area_status_label.setText(self.get_brightness_area_status_text())
            
            self.showToast("Brightness area reset to defaults")
            
        except Exception as e:
            print(f"Exception in reset_brightness_area: {e}")
            self.showToast(f"Error resetting area: {e}")

    def get_brightness_area_status_text(self):
        """Get status text showing current brightness area points."""
        try:
            points = self.camera_settings.get_brightness_area_points()
            if points and len(points) == 4:
                # Format points nicely
                point_strs = [f"({p[0]},{p[1]})" for p in points]
                status = f"Area: {' → '.join(point_strs)}"
                return status
            else:
                return "Area: Not defined"
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"get_brightness_area_status_text: Exception = {e}")
            return f"Area: Error ({e})"

    def on_threshold_preview_clicked(self, x, y):
        """Handle threshold preview clicks"""
        try:
            label = getattr(self, "threshold_preview_label", None)
            pixmap = label.pixmap() if label is not None else None
            if pixmap is None:
                print(f"Threshold Preview Clicked on {x}:{y} - no image available")
                return

            label_w = label.width()
            label_h = label.height()
            img_w = pixmap.width()
            img_h = pixmap.height()

            # Calculate top-left of the drawn pixmap inside the label (centered alignment)
            left = (label_w - img_w) // 2
            top = (label_h - img_h) // 2

            # Map click coordinates to pixmap coordinates
            ix = int(x - left)
            iy = int(y - top)

            if not (0 <= ix < img_w and 0 <= iy < img_h):
                print(f"Threshold Preview Clicked on {x}:{y} - outside image area")
                return

            qimage = pixmap.toImage()
            color = qimage.pixelColor(ix, iy)
            r, g, b = color.red(), color.green(), color.blue()

            # For threshold images, typically they are grayscale
            gray = r  # Since it's a threshold image, R=G=B
            threshold_value = "255" if gray > 127 else "0"

            print(f"Threshold Preview Clicked on {x}:{y} - pixel value = {gray}, threshold = {threshold_value}")
            self.showToast(f"Threshold value: {threshold_value} (gray: {gray})")
        except Exception as e:
            print(f"Exception in on_threshold_preview_clicked: {e}")

    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 5)
            toast.show()

    def _connect_widget_signals(self):
        """
        Connect all widget signals to the unified value_changed_signal.
        This eliminates callback duplication while maintaining the same interface.
        """
        widget_mappings = [
            # Core settings
            (self.camera_index_input, CameraSettingKey.INDEX.value, 'valueChanged'),
            (self.width_input, CameraSettingKey.WIDTH.value, 'valueChanged'),
            (self.height_input, CameraSettingKey.HEIGHT.value, 'valueChanged'),
            (self.skip_frames_input, CameraSettingKey.SKIP_FRAMES.value, 'valueChanged'),
            (self.capture_pos_offset_input, CameraSettingKey.CAPTURE_POS_OFFSET.value, 'valueChanged'),

            # Contour detection
            (self.contour_detection_toggle, CameraSettingKey.CONTOUR_DETECTION.value, 'toggled'),
            (self.draw_contours_toggle, CameraSettingKey.DRAW_CONTOURS.value, 'toggled'),
            (self.threshold_input, CameraSettingKey.THRESHOLD.value, 'valueChanged'),
            (self.threshold_pickup_area_input, CameraSettingKey.THRESHOLD_PICKUP_AREA.value, 'valueChanged'),
            (self.epsilon_input, CameraSettingKey.EPSILON.value, 'valueChanged'),
            (self.min_contour_area_input, CameraSettingKey.MIN_CONTOUR_AREA.value, 'valueChanged'),
            (self.max_contour_area_input, CameraSettingKey.MAX_CONTOUR_AREA.value, 'valueChanged'),

            # Preprocessing
            (self.gaussian_blur_toggle, CameraSettingKey.GAUSSIAN_BLUR.value, 'toggled'),
            (self.blur_kernel_input, CameraSettingKey.BLUR_KERNEL_SIZE.value, 'valueChanged'),
            (self.threshold_type_combo, CameraSettingKey.THRESHOLD_TYPE.value, 'currentTextChanged'),
            (self.dilate_enabled_toggle, CameraSettingKey.DILATE_ENABLED.value, 'toggled'),
            (self.dilate_kernel_input, CameraSettingKey.DILATE_KERNEL_SIZE.value, 'valueChanged'),
            (self.dilate_iterations_input, CameraSettingKey.DILATE_ITERATIONS.value, 'valueChanged'),
            (self.erode_enabled_toggle, CameraSettingKey.ERODE_ENABLED.value, 'toggled'),
            (self.erode_kernel_input, CameraSettingKey.ERODE_KERNEL_SIZE.value, 'valueChanged'),
            (self.erode_iterations_input, CameraSettingKey.ERODE_ITERATIONS.value, 'valueChanged'),

            # Calibration
            (self.chessboard_width_input, CameraSettingKey.CHESSBOARD_WIDTH.value, 'valueChanged'),
            (self.chessboard_height_input, CameraSettingKey.CHESSBOARD_HEIGHT.value, 'valueChanged'),
            (self.square_size_input, CameraSettingKey.SQUARE_SIZE_MM.value, 'valueChanged'),
            (self.calib_skip_frames_input, CameraSettingKey.CALIBRATION_SKIP_FRAMES.value, 'valueChanged'),

            # Brightness control
            (self.brightness_auto_toggle, CameraSettingKey.BRIGHTNESS_AUTO.value, 'toggled'),
            (self.kp_input, CameraSettingKey.BRIGHTNESS_KP.value, 'valueChanged'),
            (self.ki_input, CameraSettingKey.BRIGHTNESS_KI.value, 'valueChanged'),
            (self.kd_input, CameraSettingKey.BRIGHTNESS_KD.value, 'valueChanged'),
            (self.target_brightness_input, CameraSettingKey.TARGET_BRIGHTNESS.value, 'valueChanged'),

            # ArUco detection
            (self.aruco_enabled_toggle, CameraSettingKey.ARUCO_ENABLED.value, 'toggled'),
            (self.aruco_dictionary_combo, CameraSettingKey.ARUCO_DICTIONARY.value, 'currentTextChanged'),
            (self.aruco_flip_toggle, CameraSettingKey.ARUCO_FLIP_IMAGE.value, 'toggled'),
        ]

        for widget, setting_key, signal_name in widget_mappings:
            if hasattr(widget, signal_name):
                signal = getattr(widget, signal_name)
                signal.connect(
                    lambda value, key=setting_key: self._emit_setting_change(key, value)
                )

    def _emit_setting_change(self, key: str, value):
        """
        Emit the unified value_changed_signal with setting information.
        
        Args:
            key: The setting key
            value: The new value
        """
        self.value_changed_signal.emit(key, value, self.className)

    def connect_default_callbacks(self):
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
        """Updates input field values from camera settings object."""
        print(f"[CameraSettingsTabLayout] updateValues called")
        print(f"[CameraSettingsTabLayout] Updating widgets with settings: draw_contours={camera_settings.get_draw_contours()}, contour_detection={camera_settings.get_contour_detection()}")

        # CRITICAL: Update the internal camera_settings object FIRST
        self.camera_settings = camera_settings

        # Collect all widgets that need updating
        widgets = [
            self.camera_index_input, self.width_input, self.height_input,
            self.skip_frames_input, self.capture_pos_offset_input,
            self.contour_detection_toggle, self.draw_contours_toggle,
            self.threshold_input, self.threshold_pickup_area_input,
            self.epsilon_input, self.min_contour_area_input,
            self.max_contour_area_input, self.gaussian_blur_toggle,
            self.blur_kernel_input, self.threshold_type_combo,
            self.dilate_enabled_toggle, self.dilate_kernel_input,
            self.dilate_iterations_input, self.erode_enabled_toggle,
            self.erode_kernel_input, self.erode_iterations_input,
            self.chessboard_width_input, self.chessboard_height_input,
            self.square_size_input, self.calib_skip_frames_input,
            self.brightness_auto_toggle, self.kp_input, self.ki_input,
            self.kd_input, self.target_brightness_input,
            self.aruco_enabled_toggle, self.aruco_dictionary_combo,
            self.aruco_flip_toggle
        ]

        # Block signals on all widgets to prevent triggering save operations
        for widget in widgets:
            widget.blockSignals(True)

        try:
            # Core settings
            self.camera_index_input.setValue(camera_settings.get_camera_index())
            self.width_input.setValue(camera_settings.get_camera_width())
            self.height_input.setValue(camera_settings.get_camera_height())
            self.skip_frames_input.setValue(camera_settings.get_skip_frames())
            self.capture_pos_offset_input.setValue(camera_settings.get_capture_pos_offset())

            # Contour detection
            self.contour_detection_toggle.setChecked(camera_settings.get_contour_detection())
            self.draw_contours_toggle.setChecked(camera_settings.get_draw_contours())
            self.threshold_input.setValue(camera_settings.get_threshold())
            self.threshold_pickup_area_input.setValue(camera_settings.get_threshold_pickup_area())
            self.epsilon_input.setValue(camera_settings.get_epsilon())
            self.min_contour_area_input.setValue(camera_settings.get_min_contour_area())
            self.max_contour_area_input.setValue(camera_settings.get_max_contour_area())

            # Preprocessing
            self.gaussian_blur_toggle.setChecked(camera_settings.get_gaussian_blur())
            self.blur_kernel_input.setValue(camera_settings.get_blur_kernel_size())
            self.threshold_type_combo.setCurrentText(camera_settings.get_threshold_type())
            self.dilate_enabled_toggle.setChecked(camera_settings.get_dilate_enabled())
            self.dilate_kernel_input.setValue(camera_settings.get_dilate_kernel_size())
            self.dilate_iterations_input.setValue(camera_settings.get_dilate_iterations())
            self.erode_enabled_toggle.setChecked(camera_settings.get_erode_enabled())
            self.erode_kernel_input.setValue(camera_settings.get_erode_kernel_size())
            self.erode_iterations_input.setValue(camera_settings.get_erode_iterations())

            # Calibration
            self.chessboard_width_input.setValue(camera_settings.get_chessboard_width())
            self.chessboard_height_input.setValue(camera_settings.get_chessboard_height())
            self.square_size_input.setValue(camera_settings.get_square_size_mm())
            self.calib_skip_frames_input.setValue(camera_settings.get_calibration_skip_frames())

            # Brightness control
            self.brightness_auto_toggle.setChecked(camera_settings.get_brightness_auto())
            self.kp_input.setValue(camera_settings.get_brightness_kp())
            self.ki_input.setValue(camera_settings.get_brightness_ki())
            self.kd_input.setValue(camera_settings.get_brightness_kd())
            self.target_brightness_input.setValue(camera_settings.get_target_brightness())

            # ArUco detection
            self.aruco_enabled_toggle.setChecked(camera_settings.get_aruco_enabled())
            self.aruco_dictionary_combo.setCurrentText(camera_settings.get_aruco_dictionary())
            self.aruco_flip_toggle.setChecked(camera_settings.get_aruco_flip_image())

        finally:
            # Always unblock signals, even if an error occurs
            for widget in widgets:
                widget.blockSignals(False)

        # CRITICAL FIX: Update visual appearance of QToggle widgets
        # QToggle widgets use stateChanged signal to update their appearance,
        # but signals were blocked during setChecked() calls above.
        # So we must manually update their visual state.
        toggle_widgets = [
            self.contour_detection_toggle, self.draw_contours_toggle,
            self.gaussian_blur_toggle, self.dilate_enabled_toggle,
            self.erode_enabled_toggle, self.brightness_auto_toggle,
            self.aruco_enabled_toggle, self.aruco_flip_toggle
        ]
        for toggle in toggle_widgets:
            if hasattr(toggle, 'update_pos_color'):
                toggle.update_pos_color(toggle.isChecked())

        print("Camera settings updated from CameraSettings object.")



