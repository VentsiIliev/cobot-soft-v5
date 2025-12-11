"""Contour Editor Application Widget"""
from frontend.contour_editor.ContourEditor import MainApplicationFrame
from frontend.contour_editor.services.CaptureDataHandler import CaptureDataHandler
from frontend.contour_editor.services.SaveWorkpieceHandler import SaveWorkpieceHandler
from frontend.core.shared.base_widgets.AppWidget import AppWidget
from frontend.dialogs.CustomFeedbackDialog import CustomFeedbackDialog, DialogType
from communication_layer.api.v1.endpoints import workpiece_endpoints, operations_endpoints
from communication_layer.api.v1.endpoints import camera_endpoints


class ContourEditorAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None,controller=None):
        self.controller = controller
        self.parent = parent
        self.content_widget = None
        super().__init__("Contour Editor", parent)
    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        # Replace the content with actual UserManagementWidget if available
        try:
            print("🔧 Creating MainApplicationFrame for contour editor...")
            # Remove the placeholder content
            self.content_widget = MainApplicationFrame(parent=self.parent)
            print(f"✅ MainApplicationFrame created: {type(self.content_widget)}")
            
            # Inject controller into content_widget for backward compatibility
            self.content_widget.controller = self.controller

            # Connect signals for data requests - handle all controller/service calls here
            self._connect_editor_signals()

            # Connect other signals
            self.content_widget.capture_requested.connect(self.on_camera_capture_requested)
            self.content_widget.update_camera_feed_requested.connect(self.on_update_camera_feed_requested)
            self.content_widget.save_workpiece_requested.connect(lambda data: self.via_camera_on_create_workpiece_submit(data))
            self.content_widget.execute_workpiece_requested.connect(self.on_execute_workpiece_requested)
            print("✅ Contour editor signals connected")
            
            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            print(f"🔍 Current layout items count: {layout.count()}")
            
            if layout.count() > 0:
                old_content = layout.itemAt(layout.count() - 1).widget()
                print(f"🗑️ Removing old placeholder: {type(old_content)}")
                layout.removeWidget(old_content)
                old_content.deleteLater()
            
            layout.addWidget(self.content_widget)
            print("✅ Contour editor widget added to layout")
            
            # Show the content widget
            self.content_widget.show()
            print("✅ Contour editor content widget shown")
        except ImportError as e:
            import traceback
            traceback.print_exc()
            print(f"Contour Editor not available due to ImportError: {e}, using placeholder")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Contour Editor failed to load due to error: {e}, using placeholder")

    def _connect_editor_signals(self):
        """Connect signals from nested editors to handle data requests centrally"""
        # Navigate to the innermost editor
        if hasattr(self.content_widget, 'contourEditor'):
            if hasattr(self.content_widget.contourEditor, 'editor_with_rulers'):
                if hasattr(self.content_widget.contourEditor.editor_with_rulers, 'editor'):
                    editor = self.content_widget.contourEditor.editor_with_rulers.editor

                    # Connect fetch_glue_types signal
                    if hasattr(editor, 'fetch_glue_types_requested'):
                        editor.fetch_glue_types_requested.connect(self.on_fetch_glue_types_requested)
                        print("✅ Connected fetch_glue_types_requested signal")

                    # Connect glue_types_received to update editor's list
                    if hasattr(editor, 'glue_types_received'):
                        editor.glue_types_received.connect(lambda types: setattr(editor, 'glue_type_names', types))
                        print("✅ Connected glue_types_received signal")

    def on_fetch_glue_types_requested(self):
        """Handle request to fetch glue types - centralized controller access"""
        print("[ContourEditorAppWidget] Fetching glue types via ControllerService...")
        try:
            from frontend.core.services import ControllerService

            controller_service = ControllerService(self.controller)
            result = controller_service.settings.get_glue_types()

            if result.success and result.data:
                # Extract just the names
                glue_type_names = [gt.get("name") for gt in result.data if gt.get("name")]
                print(f"[ContourEditorAppWidget] Fetched {len(glue_type_names)} glue types")

                # Update the editor via signal
                if hasattr(self.content_widget, 'contourEditor'):
                    if hasattr(self.content_widget.contourEditor, 'editor_with_rulers'):
                        if hasattr(self.content_widget.contourEditor.editor_with_rulers, 'editor'):
                            editor = self.content_widget.contourEditor.editor_with_rulers.editor
                            editor.glue_type_names = glue_type_names
                            # Emit signal with the data
                            if hasattr(editor, 'glue_types_received'):
                                editor.glue_types_received.emit(glue_type_names)
            else:
                print(f"[ContourEditorAppWidget] Failed to fetch glue types: {result.message}")
        except Exception as e:
            print(f"[ContourEditorAppWidget] Error fetching glue types: {e}")
            import traceback
            traceback.print_exc()



    def on_update_camera_feed_requested(self):
        image = self.controller.handle(camera_endpoints.UPDATE_CAMERA_FEED)
        if image is None:
            # print("No image received for camera feed update")
            return
        self.content_widget.set_image(image)
        # print(f"Updated camera feed in Contour Editor")

    def on_camera_capture_requested(self):
        """
        Handle camera capture requested signal.

        Uses CaptureDataHandler to centralize the capture flow and ensure
        it goes through the proper ContourEditorData pipeline.
        """
        print("Camera capture requested from Contour Editor")
        controller_result = self.controller.handle(operations_endpoints.CREATE_WORKPIECE)
        print(f"Controller result from WORKPIECE_CREATE: len controller_result = {len(controller_result)} {controller_result}")
        result, message,data = controller_result

        if not result:
            # show error message box
            warning_dialog = CustomFeedbackDialog(
                parent=self,
                title="Warning",
                message=f"Failed to capture image: {message}",
                dialog_type=DialogType.INFO,
                ok_text="OK",
                cancel_text=None
            )
            warning_dialog.show()
            return

        print(f"CREATE_WORKPIECE_STEP_2 result: {result}, message: {message}")

        # Handle image update
        print(f"Contour Editor received image data: {data}")
        # Fix: data is a dict, not an object - use dict access instead of attribute access
        image = data.get('image') if isinstance(data, dict) else None
        if image is not None:
            print("Updating Contour Editor with new image")
            # pause the camera feed update timer
            self.content_widget.contourEditor.camera_feed_update_timer.stop()
            self.set_image(image)
        else:
            print("No image returned from CREATE_WORKPIECE_STEP_2")

        # Use CaptureDataHandler to load capture data into editor
        # This ensures we go through ContourEditorData instead of raw dicts

        editor_data = CaptureDataHandler.handle_capture_data(
            workpiece_manager=self.content_widget.contourEditor.workpiece_manager,
            capture_data=data,
            close_contour=True
        )

        if editor_data:
            CaptureDataHandler.print_capture_summary(editor_data)

        # Set callback for saving workpiece
        self.set_create_workpiece_for_on_submit_callback(self.via_camera_on_create_workpiece_submit)

    def via_camera_on_create_workpiece_submit(self, data):
        """
        Handle workpiece save via camera capture workflow.

        Uses SaveWorkpieceHandler to ensure consistent data flow through
        ContourEditorData and WorkpieceAdapter.
        """


        # Use the centralized handler
        success, message = SaveWorkpieceHandler.save_workpiece(
            workpiece_manager=self.content_widget.contourEditor.workpiece_manager,
            form_data=data,
            controller=self.controller
        )

        if success:
            print(f"✅ Workpiece saved successfully: {message}")
        else:
            print(f"❌ Failed to save workpiece: {message}")

        return success, message

    def set_image(self,image):
        """Set the image to be displayed in the contour editor"""
        try:
            self.content_widget.set_image(image)
            print("Set image in Contour Editor")
        except AttributeError:
            import traceback
            traceback.print_exc()
            print("Contour Editor widget does not support set_image method")

    def init_contours(self,contours_by_layer):
        """Initialize contours in the contour editor"""
        try:
            print("content_widget type:", type(self.content_widget))
            self.content_widget.init_contours(contours_by_layer)
        except AttributeError:
            # print the actual error
            import traceback
            traceback.print_exc()
            print("Contour Editor widget does not support init_contours method")

    def set_create_workpiece_for_on_submit_callback(self, callback):
        """Set the callback for when the create workpiece button is clicked"""
        try:
            print("Setting create workpiece callback")
            self.content_widget.set_create_workpiece_for_on_submit_callback(callback)
        except AttributeError:
            print("Contour Editor widget does not support set_create_workpiece_for_on_submit_callback method")

    def to_wp_data(self):
        return self.content_widget.contourEditor.manager.to_wp_data()

    def load_workpiece(self,workpiece):
        self.content_widget.contourEditor.load_workpiece(workpiece)

    def on_execute_workpiece_requested(self, workpiece):
        """Handle workpiece execution request - centralized controller access"""
        print(f"[ContourEditorAppWidget] Executing workpiece via controller: {workpiece}")
        try:
            self.controller.handleExecuteFromGallery(workpiece)
        except Exception as e:
            print(f"[ContourEditorAppWidget] Error executing workpiece: {e}")
            import traceback
            traceback.print_exc()
