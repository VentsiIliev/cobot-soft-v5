import os

from PyQt6 import QtCore
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtWidgets import QVBoxLayout, QSizePolicy, QPushButton, QLabel


from frontend.widgets.CustomWidgets import CustomTabWidget, BackgroundTabPage
from frontend.widgets.Drawer import Drawer
from frontend.widgets.robotManualControl.RobotJogWidget import RobotJogWidget
from plugins.core.settings.ui.robot_settings_tab.RobotConfigUI import RobotConfigUI
from .CameraSettingsTabLayout import CameraSettingsTabLayout
from plugins.core.glue_settings_plugin.ui.GlueSettingsTabLayout import GlueSettingsTabLayout
from communication_layer.api.v1.endpoints import glue_endpoints
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings

#
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "icons")
BACKGROUND = os.path.join(RESOURCE_DIR, "Background_&_Logo.png")
CAMERA_SETTINGS_ICON_PATH = os.path.join(RESOURCE_DIR, "CAMERA_SETTINGS_BUTTON.png")
CONTOUR_SETTINGS_ICON_PATH = os.path.join(RESOURCE_DIR, "CONTOUR_SETTINGS_BUTTON_SQUARE.png")
ROBOT_SETTINGS_ICON_PATH = os.path.join(RESOURCE_DIR, "ROBOT_SETTINGS_BUTTON_SQUARE.png")
GLUE_SETTINGS_ICON_PATH = os.path.join(RESOURCE_DIR, "glue_qty.png")


class BackgroundWidget(CustomTabWidget):
    def __init__(self):
        super().__init__()

        # Load the background image
        self.background = QPixmap(BACKGROUND)  # Update with your image path
        if self.background.isNull():
            print("Error: Background image not loaded correctly!")

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)  # Scale image to widget size
        else:
            print("Background image not loaded")
        super().paintEvent(event)  # Call the base class paintEvent to ensure proper widget rendering


class SettingsContent(BackgroundWidget):
    # Action signals
    update_camera_feed_requested = QtCore.pyqtSignal()
    raw_mode_requested = QtCore.pyqtSignal(bool)
    
    # Settings change signal - replaces callback pattern
    setting_changed = QtCore.pyqtSignal(str, object, str)  # key, value, component_type

    def __init__(self, controller=None, controller_service=None):
        super().__init__()

        # Store controller_service for passing to UI components
        # Prefer controller_service over raw controller
        self.controller_service = controller_service
        self.controller = controller  # Legacy fallback

        self.setStyleSheet(""" 
            QTabWidget {
                background-color: white; 
                padding: 10px; 
            }
            QTabBar::tab { 
                background: transparent; 
                border: none; 
            } 
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Initialize tab containers
        self.cameraSettingsTab = None
        self.robotSettingsTab = None
        self.glueSettingsTab = None
        
        # Initialize layout containers
        self.cameraSettingsTabLayout = None
        self.robotSettingsTabLayout = None
        self.glueSettingsTabLayout = None

        # Get needed tabs from application context
        needed_tabs = self._get_needed_settings_tabs()
        print(f"SettingsContent: Creating tabs for application: {needed_tabs}")
        
        # Create tabs dynamically based on application needs
        self._create_dynamic_tabs(needed_tabs)
        
        print(f"SettingsContent: Tabs created successfully. Glue tab exists: {self.glueSettingsTab is not None}")

        # Set icons for tabs (Initial)
        self.update_tab_icons()

        # Connect unified signals to settings callback
        self._connect_settings_signals()
        
        # Setup jog drawer for all settings tabs
        self._setup_jog_drawer()
        # self.hide()  # Hide settings content initially

    def _get_needed_settings_tabs(self):
        """Get the settings tabs needed by the current application."""
        try:
            from core.application.ApplicationContext import get_application_settings_tabs
            return get_application_settings_tabs()
        except Exception as e:
            print(f"Error getting needed settings tabs: {e}")
            return ["camera", "robot"]  # Fallback to default tabs

    def _create_dynamic_tabs(self, needed_tabs):
        """Create tabs dynamically based on application needs."""
        try:
            # Create camera tab if needed
            if "camera" in needed_tabs:
                self._create_camera_tab()
            
            # Create robot tab if needed  
            if "robot" in needed_tabs:
                self._create_robot_tab()
                
            # Create glue tab if needed
            if "glue" in needed_tabs:
                self._create_glue_tab()
                
                
        except Exception as e:
            print(f"Error creating dynamic tabs: {e}")
            # Fallback to creating default tabs
            self._create_camera_tab()
            self._create_robot_tab()

    def _create_camera_tab(self):
        """Create camera settings tab."""
        self.cameraSettingsTab = BackgroundTabPage()
        self.addTab(self.cameraSettingsTab, "")
        
        # Create camera settings layout
        self.cameraSettingsTabLayout = CameraSettingsTabLayout(self.cameraSettingsTab)
        self.connectCameraSettingSignals()
        self.cameraSettingsTabLayout.update_camera_feed_signal.connect(lambda: self.update_camera_feed_requested.emit())
        
        # Set the layout to the tab
        self.cameraSettingsTab.setLayout(self.cameraSettingsTabLayout)

    def _create_robot_tab(self):
        """Create robot settings tab."""
        self.robotSettingsTab = BackgroundTabPage()
        self.addTab(self.robotSettingsTab, "")

        # Create robot settings using controller_service (signal-based pattern)
        self.robotSettingsTabLayout = RobotConfigUI(self, self.controller_service)

        # For RobotConfigUI widget, we need to add it as a widget, not set it as layout
        robot_tab_layout = QVBoxLayout()
        robot_tab_layout.addWidget(self.robotSettingsTabLayout)
        self.robotSettingsTab.setLayout(robot_tab_layout)

    def _create_glue_tab(self):
        """Create glue settings tab."""
        self.glueSettingsTab = BackgroundTabPage()
        self.addTab(self.glueSettingsTab, "")

        # Create glue settings with default settings (will be loaded lazily when tab is selected)
        self.glueSettingsTabLayout = GlueSettingsTabLayout(self.glueSettingsTab, GlueSettings())

        # Set the layout to the tab
        self.glueSettingsTab.setLayout(self.glueSettingsTabLayout)


    def _connect_settings_signals(self):
        """
        Connect all settings tab signals to emit the unified setting_changed signal.
        This replaces the old callback pattern with clean signal emission.
        """
        # Connect glue settings value changes if glue tab exists
        if self.glueSettingsTabLayout is not None:
            self.glueSettingsTabLayout.value_changed_signal.connect(self._emit_setting_change)

        # Connect camera settings value changes if camera tab exists
        if self.cameraSettingsTabLayout is not None:
            self.cameraSettingsTabLayout.value_changed_signal.connect(self._emit_setting_change)

        # Connect robot settings value changes if robot tab exists
        if self.robotSettingsTabLayout is not None:
            self.robotSettingsTabLayout.value_changed_signal.connect(self._emit_setting_change)

    def _load_initial_glue_settings(self):
        """Load initial glue settings from the server."""
        try:
            print("Loading initial glue settings from server...")
            response = self.controller.handle(glue_endpoints.SETTINGS_GLUE_GET)
            
            if response and response.get('status') == 'success':
                settings_data = response.get('data', {})
                print(f"Loaded glue settings: {settings_data}")
                return GlueSettings(settings_data)
            else:
                print(f"Failed to load glue settings: {response}")
                return GlueSettings()  # Return default settings
        except Exception as e:
            print(f"Error loading initial glue settings: {e}")
            import traceback
            traceback.print_exc()
            return GlueSettings()  # Return default settings on error
    
    def _emit_setting_change(self, key: str, value, component_type: str):
        """
        Emit the unified setting_changed signal and maintain backward compatibility.
        
        Args:
            key: The setting key
            value: The new value
            component_type: The component class name
        """
        # Emit the new signal for modern signal-based handling
        self.setting_changed.emit(key, value, component_type)
    
    def _setup_jog_drawer(self):
        """Setup the jog drawer and toggle button for all settings tabs"""
        # Create jog drawer as top-level widget for full screen height
        self.jog_drawer = Drawer(None, animation_duration=300, side="right")
        self.jog_drawer.setFixedWidth(350)  # Fixed width for jog panel
        self.jog_drawer.heightOffset = 0  # Use full height with no offset
        self.jog_drawer.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Create jog content
        jog_layout = QVBoxLayout(self.jog_drawer)
        jog_layout.setContentsMargins(15, 15, 15, 15)
        jog_layout.setSpacing(10)
        
        # Jog title
        jog_title = QLabel("Robot Jog Control")
        jog_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333333;
            margin-bottom: 10px;
            padding: 10px;
            background-color: #F0F0F0;
            border-radius: 4px;
        """)
        jog_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        jog_layout.addWidget(jog_title)
        
        # Jog widget
        self.jog_widget = RobotJogWidget()
        self.jog_widget.save_point_btn.setVisible(False)
        self.jog_widget.clear_points_btn.setVisible(False)
        jog_layout.addWidget(self.jog_widget)

        # PERFORMANCE FIX: Connect tab change to control camera timer
        self.currentChanged.connect(self._on_tab_changed)
        print("[SettingsContent] Connected tab change handler for performance optimization")

        # Initialize tracking for lazy-loaded settings
        self._settings_loaded = {
            'camera': False,
            'robot': False,
            'glue': False
        }

        # CRITICAL FIX: Start camera updates and load settings for the first visible tab (usually camera tab)
        # The currentChanged signal doesn't fire for the initially selected tab
        #
        # PERFORMANCE NOTE: Even though VisionService runs in a separate thread, the camera
        # preview updates run on the MAIN GUI THREAD and involve expensive operations:
        # - Image format conversion (BGR→RGB)
        # - QImage/QPixmap creation and memory allocation
        # - Image scaling (very expensive!)
        # - Widget repainting (GPU operations)
        # Running these at 33 FPS on the main thread causes severe UI lag and FPS drops.
        # Solution: Only update at 10 FPS and only when camera tab is actually visible.
        current_index = self.currentIndex()
        if hasattr(self, 'cameraSettingsTab') and self.widget(current_index) == self.cameraSettingsTab:
            if hasattr(self, 'cameraSettingsTabLayout') and self.cameraSettingsTabLayout:
                print("[SettingsContent] Starting camera updates for initially visible camera tab")
                # Use a timer to ensure widget is fully initialized before starting updates
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, self.cameraSettingsTabLayout.start_camera_updates)
                # Also load camera settings immediately since it's the first visible tab
                print("[SettingsContent] Scheduling camera settings load in 150ms...")
                QTimer.singleShot(150, lambda: self._load_tab_settings('camera'))

    def _on_tab_changed(self, index):
        """Handle tab changes to optimize performance - start/stop camera timer and lazy load settings"""
        try:
            # Stop camera updates on all tabs first
            if hasattr(self, 'cameraSettingsTabLayout') and self.cameraSettingsTabLayout:
                self.cameraSettingsTabLayout.stop_camera_updates()

            # Determine which tab was selected and load settings if needed
            current_widget = self.widget(index)

            # Camera tab
            if hasattr(self, 'cameraSettingsTab') and current_widget == self.cameraSettingsTab:
                if hasattr(self, 'cameraSettingsTabLayout') and self.cameraSettingsTabLayout:
                    print(f"[SettingsContent] Camera tab activated - starting camera updates")
                    self.cameraSettingsTabLayout.start_camera_updates()
                # Lazy load camera settings
                self._load_tab_settings('camera')

            # Robot tab
            elif hasattr(self, 'robotSettingsTab') and current_widget == self.robotSettingsTab:
                print(f"[SettingsContent] Robot tab activated")
                # Lazy load robot settings
                self._load_tab_settings('robot')
                # Also trigger device state initialization if available
                if hasattr(self.robotSettingsTabLayout, 'on_tab_selected'):
                    self.robotSettingsTabLayout.on_tab_selected()

            # Glue tab
            elif hasattr(self, 'glueSettingsTab') and current_widget == self.glueSettingsTab:
                print(f"[SettingsContent] Glue tab activated")
                # Lazy load glue settings
                self._load_tab_settings('glue')
                # Also trigger device state initialization if available
                if hasattr(self.glueSettingsTabLayout, 'on_tab_selected'):
                    self.glueSettingsTabLayout.on_tab_selected()

            else:
                print(f"[SettingsContent] Unknown tab activated")

        except Exception as e:
            print(f"Error in tab change handler: {e}")
            import traceback
            traceback.print_exc()

    def _load_tab_settings(self, tab_type):
        """
        Lazy load settings for a specific tab when it's first selected.

        Args:
            tab_type: Type of tab ('camera', 'robot', 'glue')
        """
        # Skip if already loaded
        if self._settings_loaded.get(tab_type, False):
            print(f"[SettingsContent] {tab_type.title()} settings already loaded, skipping...")
            return

        print(f"[SettingsContent] Lazy loading {tab_type} settings...")

        try:
            if self.controller_service is None:
                print(f"[SettingsContent] Controller service not available, cannot load {tab_type} settings")
                return

            # Load settings based on tab type
            if tab_type == 'camera':
                result = self.controller_service.settings.get_camera_settings()
                if result and result.success:
                    self.updateCameraSettings(result.data)
                    self._settings_loaded['camera'] = True
                    print(f"[SettingsContent] ✅ Camera settings loaded successfully")
                else:
                    print(f"[SettingsContent] ❌ Failed to load camera settings: {result.message if result else 'No result'}")

            elif tab_type == 'robot':
                result = self.controller_service.settings.get_robot_settings()
                if result and result.success:
                    self.updateRobotSettings(result.data)
                    self._settings_loaded['robot'] = True
                    print(f"[SettingsContent] ✅ Robot settings loaded successfully")
                else:
                    print(f"[SettingsContent] ❌ Failed to load robot settings: {result.message if result else 'No result'}")

            elif tab_type == 'glue':
                result = self.controller_service.settings.get_glue_settings()
                if result and result.success:
                    self.updateGlueSettings(result.data)
                    self._settings_loaded['glue'] = True
                    print(f"[SettingsContent] ✅ Glue settings loaded successfully")
                else:
                    print(f"[SettingsContent] ❌ Failed to load glue settings: {result.message if result else 'No result'}")

        except Exception as e:
            print(f"[SettingsContent] Error loading {tab_type} settings: {e}")
            import traceback
            traceback.print_exc()

    def clean_up(self):
        """Clean up resources when closing the settings content"""
        if self.cameraSettingsTabLayout is not None:
            self.cameraSettingsTabLayout.clean_up()
        # TODO: Add cleanup for other tabs if needed
        # if self.robotSettingsTabLayout is not None:
        #     self.robotSettingsTabLayout.clean_up()
        # if self.glueSettingsTabLayout is not None:
        #     self.glueSettingsTabLayout.clean_up()

    def updateCameraFeed(self, frame):
        """Update the camera feed in the camera settings tab."""
        if self.cameraSettingsTabLayout is not None:
            self.cameraSettingsTabLayout.update_camera_feed(frame)

    def connectCameraSettingSignals(self):
        print("Connecting camera settings signals")
        self.cameraSettingsTabLayout.star_camera_requested.connect(self.onStartCameraRequested)
        self.cameraSettingsTabLayout.raw_mode_requested.connect(self.onRawModeRequested)

        # Connect settings button signals (BUGFIX: These were missing!)
        self.cameraSettingsTabLayout.load_settings_requested.connect(self.onLoadCameraSettingsRequested)
        self.cameraSettingsTabLayout.save_settings_requested.connect(self.onSaveCameraSettingsRequested)
        self.cameraSettingsTabLayout.reset_settings_requested.connect(self.onResetCameraSettingsRequested)

    def onStartCameraRequested(self):
        print("Camera start requested")

    def onRawModeRequested(self, state):
        print("Raw mode requested")
        # Emit a signal to update the camera feed
        self.raw_mode_requested.emit(state)

    def onLoadCameraSettingsRequested(self):
        """Handle load camera settings button click"""
        print("[SettingsContent] Load camera settings requested")
        try:
            if self.controller_service:
                result = self.controller_service.settings.get_camera_settings()
                if result and result.success:
                    self.updateCameraSettings(result.data)
                    print("[SettingsContent] Camera settings loaded and UI updated")
                    # Show success toast if available
                    if hasattr(self.cameraSettingsTabLayout, 'showToast'):
                        self.cameraSettingsTabLayout.showToast("Camera settings loaded successfully")
                else:
                    print(f"[SettingsContent] Failed to load camera settings: {result.message if result else 'No result'}")
                    if hasattr(self.cameraSettingsTabLayout, 'showToast'):
                        self.cameraSettingsTabLayout.showToast("Failed to load camera settings")
        except Exception as e:
            print(f"[SettingsContent] Error loading camera settings: {e}")
            import traceback
            traceback.print_exc()

    def onSaveCameraSettingsRequested(self):
        """Handle save camera settings button click"""
        print("[SettingsContent] Save camera settings requested")
        try:
            if self.controller_service and hasattr(self.cameraSettingsTabLayout, 'camera_settings'):
                result = self.controller_service.settings.update_camera_settings(
                    self.cameraSettingsTabLayout.camera_settings
                )
                if result and result.success:
                    print("[SettingsContent] Camera settings saved successfully")
                    if hasattr(self.cameraSettingsTabLayout, 'showToast'):
                        self.cameraSettingsTabLayout.showToast("Camera settings saved successfully")
                else:
                    print(f"[SettingsContent] Failed to save camera settings: {result.message if result else 'No result'}")
                    if hasattr(self.cameraSettingsTabLayout, 'showToast'):
                        self.cameraSettingsTabLayout.showToast("Failed to save camera settings")
        except Exception as e:
            print(f"[SettingsContent] Error saving camera settings: {e}")
            import traceback
            traceback.print_exc()

    def onResetCameraSettingsRequested(self):
        """Handle reset camera settings button click"""
        print("[SettingsContent] Reset camera settings requested")
        try:
            if self.controller_service:
                result = self.controller_service.settings.reset_camera_settings()
                if result and result.success:
                    # Reload the default settings into the UI
                    self.updateCameraSettings(result.data)
                    print("[SettingsContent] Camera settings reset to defaults")
                    if hasattr(self.cameraSettingsTabLayout, 'showToast'):
                        self.cameraSettingsTabLayout.showToast("Camera settings reset to defaults")
                else:
                    print(f"[SettingsContent] Failed to reset camera settings: {result.message if result else 'No result'}")
                    if hasattr(self.cameraSettingsTabLayout, 'showToast'):
                        self.cameraSettingsTabLayout.showToast("Failed to reset camera settings")
        except Exception as e:
            print(f"[SettingsContent] Error resetting camera settings: {e}")
            import traceback
            traceback.print_exc()

    def update_tab_icons(self):
        """Dynamically update tab icons based on window width and created tabs"""
        tab_icon_size = int(self.width() * 0.05)  # 5% of new window width for tabs
        
        # Set icons based on which tabs were actually created
        tab_index = 0
        if self.cameraSettingsTab is not None:
            self.setTabIcon(tab_index, QIcon(CAMERA_SETTINGS_ICON_PATH))
            tab_index += 1
        
        if self.robotSettingsTab is not None:
            self.setTabIcon(tab_index, QIcon(ROBOT_SETTINGS_ICON_PATH))
            tab_index += 1
            
        if self.glueSettingsTab is not None:
            self.setTabIcon(tab_index, QIcon(GLUE_SETTINGS_ICON_PATH))
            tab_index += 1
        
        self.tabBar().setIconSize(QSize(tab_icon_size, tab_icon_size))

    def resizeEvent(self, event):
        """Resize the tab widget dynamically on window resize"""
        new_width = self.width()

        # Resize the tab widget to be responsive to the window size
        self.setMinimumWidth(int(new_width * 0.3))  # 30% of the window width
        self.update_tab_icons()
        
        # Handle jog drawer resizing
        if hasattr(self, 'jog_drawer'):
            self._resize_drawer_to_screen_height()
        if hasattr(self, 'jog_toggle_button'):
            self._position_toggle_button()

        super().resizeEvent(event)

    def _resize_drawer_to_screen_height(self):
        """Resize drawer to full screen height"""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QPoint

        # Get main window position and the screen it's on
        main_window = self.window()
        main_window_global_pos = main_window.mapToGlobal(QPoint(0, 0))

        # Get the screen that contains the main window
        screen = QApplication.screenAt(main_window_global_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        # Set drawer to full screen height
        self.jog_drawer.setFixedHeight(screen_geometry.height())
        self.jog_drawer.heightOffset = 0  # No offset, use full height

        # Position drawer based on its current state using screen coordinates
        screen_right = screen_geometry.x() + screen_geometry.width()

        if hasattr(self, 'jog_drawer') and self.jog_drawer.is_open:
            # If open, position at visible location on screen
            x = screen_right - self.jog_drawer.width()
        else:
            # If closed, position off-screen
            x = screen_right

        self.jog_drawer.move(x, screen_geometry.y())  # Position using correct screen coordinates

    def showEvent(self, event):
        """Handle show events to ensure proper positioning"""
        super().showEvent(event)
        if hasattr(self, 'jog_drawer'):
            self._resize_drawer_to_screen_height()
        if hasattr(self, 'jog_toggle_button'):
            self._position_toggle_button()

    def updateCameraSettings(self, cameraSettings):
        print(f"[SettingsContent] updateCameraSettings called with settings: draw_contours={cameraSettings.get_draw_contours() if cameraSettings else 'None'}")
        if self.cameraSettingsTabLayout is not None:
            self.cameraSettingsTabLayout.updateValues(cameraSettings)
        else:
            print("[SettingsContent] WARNING: cameraSettingsTabLayout is None, cannot update values")

    def updateRobotSettings(self, robotSettings):
        if self.robotSettingsTabLayout is not None:
            self.robotSettingsTabLayout.updateValues(robotSettings)

    def updateContourSettings(self, contourSettings):
        # TODO: Implement contour settings update if needed
        # if self.contourSettingsTabLayout is not None:
        #     self.contourSettingsTabLayout.updateValues(contourSettings)
        return

    def updateGlueSettings(self, glueSettings):
        if self.glueSettingsTabLayout is not None:
            self.glueSettingsTabLayout.updateValues(glueSettings)

    def _position_toggle_button(self):
        """Position the toggle button based on drawer state"""
        if not hasattr(self, 'jog_toggle_button'):
            return

        # Position relative to this widget's geometry
        widget_rect = self.rect()
        button_y = (widget_rect.height() - self.jog_toggle_button.height()) // 2

        if hasattr(self, 'jog_drawer') and self.jog_drawer.is_open:
            # When drawer is open, position button at the left edge of the drawer
            # The drawer is positioned at (parent_width - drawer_width), so button goes just to the left
            button_x = widget_rect.width() - self.jog_drawer.width() - self.jog_toggle_button.width() - 5
        else:
            # When drawer is closed, position button at the right edge of the widget
            button_x = widget_rect.width() - self.jog_toggle_button.width() - 10

        self.jog_toggle_button.move(button_x, button_y)
        self.jog_toggle_button.setVisible(True)
        self.jog_toggle_button.raise_()
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QSizePolicy

    app = QApplication(sys.argv)
    window = SettingsContent()
    window.show()
    sys.exit(app.exec())
