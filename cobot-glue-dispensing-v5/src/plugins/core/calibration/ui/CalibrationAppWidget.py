from PyQt6.QtWidgets import QWidget

from core.model.settings.robot_calibration_settings import RobotCalibrationSettings
from frontend.core.shared.base_widgets.AppWidget import AppWidget
from plugins.core.calibration.ui.CalibrationSettingsTab import CalibrationServiceTabLayout


class CalibrationAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None, controller_service=None):
        self.parent= parent
        self.controller_service = controller_service
        super().__init__("ServiceCalibrationAppWidget", parent)
        print("ServiceCalibrationAppWidget initialized with parent:", self.parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button
        self.setStyleSheet("""
                           QWidget {
                               background-color: #f8f9fa;
                               font-family: 'Segoe UI', Arial, sans-serif;
                               color: #000000;  /* Force black text */
                           }

                       """)
        try:
            def updateCameraFeedCallback():
                if self.controller_service is None:
                    # No controller available yet; update with None (placeholder) or skip
                    self.content_layout.update_camera_feed(None)
                    return
                try:
                    result = self.controller_service.camera.get_latest_frame()
                    frame = result.data if result else None
                except Exception:
                    frame = None
                self.content_layout.update_camera_feed(frame)

            self.content_widget = QWidget(self.parent)
            self.content_layout = CalibrationServiceTabLayout(parent_widget=self.parent, calibration_service=None, controller_service=self.controller_service)
            self.content_layout.update_camera_feed_signal.connect(lambda: updateCameraFeedCallback())

            # Connect controller-related signals only if controller_service present
            if self.controller_service:
                self.content_layout.move_to_pickup_requested.connect(lambda: self.controller_service.robot.move_to_home())
                self.content_layout.jogRequested.connect(lambda endpoint,axis, dir_str, step_size: self.on_jog_requested(axis, dir_str, step_size))
                self.content_layout.compute_homography_requested.connect(lambda: self.controller_service.robot.calibrate_robot())
                self.content_layout.save_point_requested.connect(lambda: self.controller_service.robot.save_calibration_point())
            else:
                print("CalibrationAppWidget: controller_service is None; skipping controller signal connections")

            def onMoveToCalibrationPos():
                if self.controller_service:
                    try:
                        self.controller_service.camera.enable_raw_mode()
                        self.controller_service.robot.move_to_calibration_position()
                    except Exception:
                        import traceback
                        traceback.print_exc()
                        print("onMoveToCalibrationPos: controller_service action failed")

            self.content_layout.move_to_calibration_requested.connect(lambda: onMoveToCalibrationPos())
            if self.controller_service:
                self.content_layout.calibrate_camera_requested.connect(lambda: self.controller_service.camera.calibrate_camera())
                self.content_layout.capture_image_requested.connect(lambda: self.controller_service.camera.capture_calibration_image())
                self.content_layout.auto_calibrate_requested.connect(lambda: self.controller_service.camera.calibrate_camera())
            # self.content_layout.test_calibration_requested.connect(lambda: self.controller.handle(TEST_CALIBRATION))
            if self.controller_service:
                self.content_layout.save_work_area_requested.connect(lambda points: self.controller_service.camera.save_work_area_points(points))
            else:
                # no controller - ignore save requests
                self.content_layout.save_work_area_requested.connect(lambda points: print("save_work_area requested but no controller present"))

            # self.content_layout.start_calibration_requested.connect(lambda: self.controller.handle(CALIBRATE))

            self.content_widget.setLayout(self.content_layout)
            print("CALIBRATION WIDGET TYPE:", type(self.content_widget))
            # broker = MessageBroker()
            # broker.subscribe("Language", content_widget.updateLanguage)

            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except Exception:
            import traceback
            traceback.print_exc()
            print("Service Calibration setup failed — using placeholder")

    def on_jog_requested(self, axis, dir_str,step_size):

        result = self.controller_service.robot.jog_robot(axis, dir_str, step_size)
        print(f"{result.message}")

