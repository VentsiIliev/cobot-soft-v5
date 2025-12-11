import json
from pathlib import Path

from PyQt6.QtCore import QPoint
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtGui import QPen, QBrush, QFont
from PyQt6.QtGui import QPolygon

from core.application.ApplicationContext import get_core_settings_path
from core.model.settings.enums.CameraSettingKey import CameraSettingKey


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


            qpoints = [QPoint(int(p[0]), int(p[1])) for p in scaled_points]
            polygon = QPolygon(qpoints)
            painter.drawPolygon(polygon)

            # Label it at the center of scaled points
            center_x = sum(p[0] for p in scaled_points) // 4
            center_y = sum(p[1] for p in scaled_points) // 4



    except Exception as e:
        print(f"Exception in _draw_saved_brightness_area: {e}")

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


        painter = QPainter(overlay_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw saved brightness area (if exists and not in selection mode)
        if not self.brightness_area_selection_mode:
            _draw_saved_brightness_area(self, painter)

        # Draw current selection points and area preview
        if self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
            _draw_selection_points(self, painter)

            # Draw partial area preview if we have 2 or more points
            if len(self.brightness_area_points) >= 2:
                _draw_selection_preview(self, painter)

        painter.end()

        # Update the camera preview with the overlay using proper scaling
        self.update_camera_preview(overlay_pixmap)

    except Exception as e:
        print(f"Exception in update_brightness_area_overlay: {e}")


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
            update_brightness_area_overlay(self)
        else:
            # Exiting selection mode
            self.brightness_area_points = []
            update_brightness_area_overlay(self)

    except Exception as e:
        print(f"Exception in toggle_brightness_area_selection_mode: {e}")
        import traceback
        traceback.print_exc()

def refresh_brightness_area_display(self):
    """Refresh the brightness area display to show current saved settings."""
    try:
        print("=== Refreshing brightness area display ===")

        # Force reload the camera settings from the saved file to get latest values
        try:


            # Load the actual saved settings from a file
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

        # Update the status label to show the current area
        if hasattr(self, 'brightness_area_status_label'):
            status_text = get_brightness_area_status_text(self)
            print(f"Setting status label to: {status_text}")
            self.brightness_area_status_label.setText(status_text)

        # Update the visual overlay to show the current area
        update_brightness_area_overlay(self)

    except Exception as e:
        print(f"Exception in refresh_brightness_area_display: {e}")
        import traceback
        traceback.print_exc()

def _draw_selection_points(self, painter):
    """Draw the currently selected points during area selection."""
    try:
        # Get scaling factors to convert from original image coordinates to preview coordinates
        original_width = self.camera_settings.get_camera_width()
        original_height = self.camera_settings.get_camera_height()

        # Get the current pixmap dimensions for scaling
        original_pixmap = getattr(self.camera_preview_label, '_original_pixmap', None)
        if original_pixmap is None:
            print("No original pixmap available for coordinate scaling in _draw_selection_points")
            return

        preview_width = original_pixmap.width()
        preview_height = original_pixmap.height()

        # Set up the drawing style for selection points
        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(3)
        painter.setPen(pen)
        brush = QBrush(Qt.GlobalColor.red)
        painter.setBrush(brush)

        # Draw each selected point (scale from original camera coords to preview coords)
        for i, point in enumerate(self.brightness_area_points):
            # Scale from original camera coordinates to preview coordinates
            preview_x = int((point[0] / original_width) * preview_width)
            preview_y = int((point[1] / original_height) * preview_height)

            # Draw a point circle
            painter.drawEllipse(int(preview_x - 5), int(preview_y - 5), 10, 10)

            # Draw point number
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)

            # White text on a red background
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(int(preview_x - 5), int(preview_y - 15), f"{i + 1}")

            # Reset pen for the next point
            painter.setPen(pen)

    except Exception as e:
        print(f"Exception in _draw_selection_points: {e}")
        import traceback
        traceback.print_exc()

def _draw_selection_preview(self, painter):
    """Draw preview of the selection area as points are being selected."""
    try:
        if len(self.brightness_area_points) < 2:
            return

        # Get scaling factors to convert from original image coordinates to preview coordinates
        original_width = self.camera_settings.get_camera_width()
        original_height = self.camera_settings.get_camera_height()

        # Get the current pixmap dimensions for scaling
        original_pixmap = getattr(self.camera_preview_label, '_original_pixmap', None)
        if original_pixmap is None:
            print("No original pixmap available for coordinate scaling in _draw_selection_preview")
            return

        preview_width = original_pixmap.width()
        preview_height = original_pixmap.height()

        # Set up drawing style for preview lines
        pen = QPen(Qt.GlobalColor.yellow)
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)

        # Draw lines connecting the selected points
        from PyQt6.QtCore import QPoint
        for i in range(len(self.brightness_area_points) - 1):
            p1 = self.brightness_area_points[i]
            p2 = self.brightness_area_points[i + 1]

            # Scale from original camera coordinates to preview coordinates
            preview_x1 = int((p1[0] / original_width) * preview_width)
            preview_y1 = int((p1[1] / original_height) * preview_height)
            preview_x2 = int((p2[0] / original_width) * preview_width)
            preview_y2 = int((p2[1] / original_height) * preview_height)

            painter.drawLine(QPoint(preview_x1, preview_y1), QPoint(preview_x2, preview_y2))

        # If we have 4 points, close the rectangle
        if len(self.brightness_area_points) == 4:
            p1 = self.brightness_area_points[3]
            p2 = self.brightness_area_points[0]

            # Scale from original camera coordinates to preview coordinates
            preview_x1 = int((p1[0] / original_width) * preview_width)
            preview_y1 = int((p1[1] / original_height) * preview_height)
            preview_x2 = int((p2[0] / original_width) * preview_width)
            preview_y2 = int((p2[1] / original_height) * preview_height)

            painter.drawLine(QPoint(preview_x1, preview_y1), QPoint(preview_x2, preview_y2))

    except Exception as e:
        print(f"Exception in _draw_selection_preview: {e}")
        import traceback
        traceback.print_exc()

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

        # Check if we need to draw the saved brightness area (not in selection mode)
        if not self.brightness_area_selection_mode:
            points = self.camera_settings.get_brightness_area_points()
            if points and len(points) == 4:
                needs_overlay = True

        # Check if we need to draw selection elements
        if self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
            needs_overlay = True

        # If no overlay needed, return the original pixmap
        if not needs_overlay:
            return pixmap

        # Create a copy to draw on
        overlay_pixmap = pixmap.copy()


        painter = QPainter(overlay_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw saved brightness area (if exists and not in selection mode)
        if not self.brightness_area_selection_mode:
            _draw_saved_brightness_area(self,painter)

        # Draw current selection points and area preview
        if self.brightness_area_selection_mode and len(self.brightness_area_points) > 0:
            _draw_selection_points(self, painter)

            # Draw a partial area preview if we have 2 or more points
            if len(self.brightness_area_points) >= 2:
                _draw_selection_preview(self, painter)

        painter.end()

        return overlay_pixmap

    except Exception as e:
        print(f"Exception in _apply_brightness_overlay_to_pixmap: {e}")
        import traceback
        traceback.print_exc()
        return pixmap  # Return original on error

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
            self.brightness_area_status_label.setText(get_brightness_area_status_text(self))

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

def finish_brightness_area_selection(self):
    """Complete brightness area selection and save points."""
    try:
        if len(self.brightness_area_points) == 4:
            # Save the points to camera settings
            self.camera_settings.set_brightness_area_points(self.brightness_area_points)

            # Emit value changed signals for each point to trigger settings save
            for i, point in enumerate(self.brightness_area_points):
                key = [CameraSettingKey.BRIGHTNESS_AREA_P1.value, CameraSettingKey.BRIGHTNESS_AREA_P2.value,
                       CameraSettingKey.BRIGHTNESS_AREA_P3.value, CameraSettingKey.BRIGHTNESS_AREA_P4.value][i]
                self.value_changed_signal.emit(key, point, self.className)

            self.showToast("Brightness area saved successfully!")

            # Update status display
            if hasattr(self, 'brightness_area_status_label'):
                self.brightness_area_status_label.setText(get_brightness_area_status_text(self))

            # Exit selection mode
            toggle_brightness_area_selection_mode(self, False)
        else:
            self.showToast("Error: Need exactly 4 points for brightness area")

    except Exception as e:
        print(f"Exception in finish_brightness_area_selection: {e}")
        self.showToast(f"Error saving brightness area: {e}")

def handle_brightness_area_point_selection(self, x, y):
    """Handle point selection for brightness area definition."""
    try:
        # Add the point to our temporary list
        self.brightness_area_points.append([x, y])
        point_num = len(self.brightness_area_points)

        self.showToast(f"Point {point_num}/4 selected: ({x}, {y})")

        # Check if we have collected all points
        if len(self.brightness_area_points) >= self.brightness_area_max_points:
            finish_brightness_area_selection(self)
        else:
            # Update visual feedback for partial selection
            update_brightness_area_overlay(self)

    except Exception as e:
        print(f"Exception in handle_brightness_area_point_selection: {e}")
