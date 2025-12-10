from PyQt6.QtWidgets import QVBoxLayout
from frontend.core.shared.base_widgets.AppWidget import AppWidget
from plugins.core.modbus_settings_plugin.ui.ModbusSettingsContent import ModbusSettingsContent
class ModbusSettingsAppWidget(AppWidget):
    def __init__(self, parent=None, controller=None, controller_service=None):
        # Prefer controller_service if provided, otherwise use controller
        self.controller_service = controller_service
        self.controller = controller
        print(f"ModbusSettingsAppWidget initializing with controller_service: {controller_service}, controller: {controller}")
        super().__init__("Modbus Settings", parent)
        print(f"ModbusSettingsAppWidget initialized with parent: {parent}")
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Create the Modbus Settings content with tabs
        # Pass controller_service if available, otherwise wrap controller
        if self.controller_service:
            controller_to_pass = self.controller_service
        elif self.controller:
            # Wrap controller in ControllerService for compatibility
            from frontend.core.services.ControllerService import ControllerService
            controller_to_pass = ControllerService(self.controller)
        else:
            controller_to_pass = None
        self.content_widget = ModbusSettingsContent(
            controller=self.controller,
            controller_service=controller_to_pass
        )
        layout.addWidget(self.content_widget)
        self.setLayout(layout)
        print("ModbusSettingsAppWidget UI setup complete with tabs")
