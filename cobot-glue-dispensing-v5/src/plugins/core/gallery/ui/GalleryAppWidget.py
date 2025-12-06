from PyQt6.QtCore import pyqtSignal

from communication_layer.api.v1.endpoints import workpiece_endpoints
from frontend.core.shared.base_widgets.AppWidget import AppWidget


class GalleryAppWidget(AppWidget):
    """Specialized widget for User Management application"""
    apply_button_clicked = pyqtSignal()
    edit_requested = pyqtSignal(str)
    def __init__(self, parent=None, controller=None, controller_service=None, onApplyCallback=None, thumbnails=None):
        self.controller = controller
        self.controller_service = controller_service
        self.thumbnails = thumbnails
        self.onApplyCallback = onApplyCallback
        super().__init__("Gallery", parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        try:
            workpieces = self.controller.handle(workpiece_endpoints.WORKPIECE_GET_ALL)

            def onApply(filename):
                if not filename:
                    print("❌ No filename provided")
                    return

                self.controller.handleSetPreselectedWorkpiece(filename)



            from plugins.core.gallery.ui.gallery.GalleryContent import GalleryContent
            # Remove the placeholder content

            if self.onApplyCallback is None:
                self.onApplyCallback = onApply

            content_widget = GalleryContent(workpieces=workpieces, thumbnails=self.thumbnails,
                                            onApplyCallback=self.onApplyCallback,controller=self.controller)
            content_widget.edit_requested.connect(lambda workpiece_id: self.edit_requested.emit(workpiece_id))


            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(content_widget)
        except ImportError as e:
            # Keep the placeholder if the UserManagementWidget is not available
            print(f"Gallery not available due to ImportError: {e}, using placeholder")
            import traceback
            traceback.print_exc()
        except Exception as e:
            # Keep the placeholder if there are other errors
            print(f"Gallery not available due to error: {e}, using placeholder")
            import traceback
            traceback.print_exc()
