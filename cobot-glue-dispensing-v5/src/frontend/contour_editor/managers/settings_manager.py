from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from frontend.contour_editor import constants
from frontend.contour_editor.ConstantsManager import ConstantsManager
from frontend.contour_editor.widgets.ConstantsSettingsDialog import ConstantsSettingsDialog
from frontend.contour_editor.widgets.GlobalSettingsDialog import GlobalSettingsDialog


class SettingsManager:
    def __init__(self, editor):
        self.editor = editor
        self.point_manager_widget = None  # Will be set later by parent

        # Load and apply initial settings
        self.load_initial_settings()
        
        # Setup settings-related UI
        self.setup_settings_shortcuts()
        
        # Initialize cached constants
        self.setup_cached_constants()
    
    def set_point_manager_widget(self, widget):
        """Set the point manager widget reference (called by parent ContourEditor)"""
        self.point_manager_widget = widget

    def load_initial_settings(self):
        """Load user settings from JSON and apply to constants"""
        settings = ConstantsManager.load_settings()
        ConstantsManager.apply_settings(settings)
    
    def setup_settings_shortcuts(self):
        """Setup keyboard shortcuts for settings"""
        # Settings dialog shortcut (Ctrl+S)
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+S"), self.editor)
        self.settings_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.settings_shortcut.activated.connect(self.open_settings_dialog)
        self.settings_shortcut.setEnabled(True)

        # Global settings shortcut (Ctrl+G)
        self.global_settings_shortcut = QShortcut(QKeySequence("Ctrl+G"), self.editor)
        self.global_settings_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.global_settings_shortcut.activated.connect(self.show_global_settings)
        self.global_settings_shortcut.setEnabled(True)

    def setup_cached_constants(self):
        """Initialize cached constants from the constants module"""
        self.handle_radius = constants.POINT_HANDLE_RADIUS
        self.handle_color = constants.POINT_HANDLE_COLOR
        self.handle_selected_color = constants.POINT_HANDLE_SELECTED_COLOR
        self.min_point_display_scale = constants.POINT_MIN_DISPLAY_SCALE
        self.cluster_distance_px = constants.CLUSTER_DISTANCE_PX
    
    def open_settings_dialog(self):
        """Open the constants settings dialog (Ctrl+S)"""

        dialog = ConstantsSettingsDialog(self.editor)
        result = dialog.show()

        if result == dialog.DialogCode.Accepted:
            print("Settings dialog closed with OK")
            # Note: Settings are already applied and reloaded by the dialog's apply_changes method
    
    def reload_constants(self):
        """Reload constants that are cached as instance variables"""
        # Reload the constants module to get updated values

        # Update cached instance variables
        self.handle_radius = constants.POINT_HANDLE_RADIUS
        self.handle_color = constants.POINT_HANDLE_COLOR
        self.handle_selected_color = constants.POINT_HANDLE_SELECTED_COLOR
        self.min_point_display_scale = constants.POINT_MIN_DISPLAY_SCALE
        self.cluster_distance_px = constants.CLUSTER_DISTANCE_PX

        # Update editor's cached values
        self.editor.handle_radius = self.handle_radius
        self.editor.handle_color = self.handle_color
        self.editor.handle_selected_color = self.handle_selected_color
        self.editor.min_point_display_scale = self.min_point_display_scale
        self.editor.cluster_distance_px = self.cluster_distance_px

        # Update timer intervals
        if hasattr(self.editor, 'drag_timer'):
            self.editor.drag_timer.setInterval(constants.DRAG_UPDATE_INTERVAL_MS)
        if hasattr(self.editor.overlay_manager, 'point_info_timer'):
            self.editor.overlay_manager.point_info_timer.setInterval(constants.POINT_INFO_HOLD_DURATION_MS)

        print("Reloaded cached constants in editor")

        # Trigger a repaint to show the changes
        self.editor.update()
    
    def show_global_settings(self):
        """Show the global settings dialog (Ctrl+G)"""

        # Use the stored point_manager_widget reference
        if self.point_manager_widget:
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            dialog = GlobalSettingsDialog(self.point_manager_widget, parent=self.editor)
            dialog.setMinimumWidth(screen_width)
            dialog.setMinimumHeight(int(screen_height / 2))
            dialog.setMaximumHeight(int(screen_height / 2))
            dialog.adjustSize()
            dialog.show()
        else:
            raise ValueError("[SettingsManager] point_manager_widget is not set - cannot open global settings dialog")
