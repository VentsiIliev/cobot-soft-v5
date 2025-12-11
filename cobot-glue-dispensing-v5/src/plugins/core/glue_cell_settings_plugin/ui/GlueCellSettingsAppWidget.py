from frontend.core.shared.base_widgets.AppWidget import AppWidget
from plugins.core.settings.ui.GlueCellSettingsTabLayout import GlueCellSettingsTabLayout
from PyQt6.QtWidgets import QWidget

# Use the GlueCellSettingsTabLayout for glue cell settings

class GlueCellSettingsAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None, controller=None, controller_service=None):
        self.controller = controller
        self.controller_service = controller_service
        self.parent = parent
        super().__init__("Glue Cell Settings", parent)
        print("GlueCellSettingsAppWidget initialized with parent:", self.parent)

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
        # Replace the content with actual SettingsContent if available
        try:

            def settingsChangeCallback(key, value, className):
                print(f"Settings changed in {className}: {key} = {value}")
                # Use controller_service if available, otherwise fallback to controller
                if self.controller_service:
                    result = self.controller_service.settings.update_setting(key, value, className)
                    if result.success:
                        print(f"✅ Settings update successful: {result.message}")
                    else:
                        print(f"❌ Settings update failed: {result.message}")
                elif self.controller:
                    # Fallback to direct controller call
                    self.controller.updateSettings(key, value, className)

            try:
                # GlueCellSettingsTabLayout is now a QVBoxLayout, so wrap it in a QWidget
                # like the calibration app does
                self.content_widget = QWidget(self.parent)
                
                # Initialize the layout for glue cells settings with controller_service
                self.content_layout = GlueCellSettingsTabLayout(
                    parent_widget=self.content_widget,
                    controller_service=self.controller_service
                )
                self.content_layout.value_changed_signal.connect(settingsChangeCallback)
                self.content_widget.setLayout(self.content_layout)
            except Exception as e:
                import traceback
                traceback.print_exc()
                # If content widget creation fails, we cannot proceed
                raise e



            # content_widget.show()
            print("GlueCellSettingsTabLayout loaded successfully")
            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            # Keep the placeholder if the UserManagementWidget is not available
            print("GlueCellSettingsTabLayout not available, using placeholder")

    def clean_up(self):
        """Clean up resources when the widget is closed"""
        print("Cleaning up GlueCellSettingsAppWidget")
        try:
            if hasattr(self, 'content_layout') and self.content_layout:
                # Call the cleanup method on the GlueCellSettingsTabLayout
                if hasattr(self.content_layout, '_cleanup_message_broker'):
                    self.content_layout._cleanup_message_broker()
        except Exception as e:
            print(f"Error during GlueCellSettingsAppWidget cleanup: {e}")
        super().clean_up() if hasattr(super(), 'clean_up') else None
