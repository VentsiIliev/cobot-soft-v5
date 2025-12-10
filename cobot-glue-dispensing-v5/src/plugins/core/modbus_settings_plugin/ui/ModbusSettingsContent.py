import os
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QSizePolicy
from PyQt6.QtGui import QIcon
from frontend.widgets.CustomWidgets import CustomTabWidget, BackgroundTabPage
from plugins.core.modbus_settings_plugin.ui.ModbusConnectionTab import ModbusConnectionTab
from plugins.core.modbus_settings_plugin.ui.ModbusDevicesTab import ModbusDevicesTab
# Icon paths
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons")
MODBUS_CONNECTION_ICON_PATH = os.path.join(RESOURCE_DIR, "modbus_connection.png")
MODBUS_DEVICES_ICON_PATH = os.path.join(RESOURCE_DIR, "modbus_devices.png")
class ModbusSettingsContent(CustomTabWidget):
    """
    Main Modbus Settings content widget with tabs.
    Tabs:
    - Connection: Modbus RTU/TCP connection settings
    - Devices: (Future) Modbus device management
    - Monitoring: (Future) Real-time Modbus monitoring
    """
    def __init__(self, controller=None, controller_service=None):
        super().__init__()
        # Store controller_service for passing to UI components
        self.controller_service = controller_service
        self.controller = controller
        self.setStyleSheet("""
            QTabWidget {
                background-color: white;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #ccc;
                padding: 8px 16px;
                margin: 2px;
                min-width: 100px;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e0e0e0;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Initialize tab containers
        self.connection_tab = None
        self.devices_tab = None
        # Initialize layout containers
        self.connection_tab_layout = None
        self.devices_tab_layout = None
        # Create tabs
        self.create_modbus_tabs()
    def create_modbus_tabs(self):
        """Create Modbus configuration tabs"""
        print("Creating Modbus Settings tabs...")
        # Create Connection tab
        self.create_connection_tab()

        # Create Devices tab
        self.create_devices_tab()

        print(f"Modbus Settings tabs created successfully - Total tabs: {self.count()}")
        for i in range(self.count()):
            print(f"  Tab {i}: {self.tabText(i)}")
    def create_connection_tab(self):
        """Create the Modbus Connection settings tab"""
        print("Creating Modbus Connection tab...")
        # Create a tab page
        self.connection_tab = BackgroundTabPage()
        # Create and add the connection settings layout
        self.connection_tab_layout = ModbusConnectionTab(
            parent_widget=self.connection_tab,
            controller_service=self.controller_service
        )
        self.connection_tab.setLayout(self.connection_tab_layout)
        # Load icon
        icon_path = MODBUS_CONNECTION_ICON_PATH
        # Add tab with icon if available
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.addTab(self.connection_tab, icon, "Connection")
            self.setIconSize(QSize(24, 24))
        else:
            # No icon, just text
            self.addTab(self.connection_tab, "Connection")
        print("Modbus Connection tab created")
    def create_devices_tab(self):
        """
        Create the Modbus Devices tab
        This tab shows:
        - List of configured Modbus devices
        - Device status (online/offline)
        - Device management actions
        """
        print("Creating Modbus Devices tab...")
        # Create tab page
        self.devices_tab = BackgroundTabPage()
        # Create and add the devices management layout
        self.devices_tab_layout = ModbusDevicesTab(
            parent_widget=self.devices_tab,
            controller_service=self.controller_service
        )
        self.devices_tab.setLayout(self.devices_tab_layout)
        # Load icon
        icon_path = MODBUS_DEVICES_ICON_PATH
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.addTab(self.devices_tab, icon, "Devices")
            self.setIconSize(QSize(24, 24))
        else:
            self.addTab(self.devices_tab, "Devices")
        print("Modbus Devices tab created")
