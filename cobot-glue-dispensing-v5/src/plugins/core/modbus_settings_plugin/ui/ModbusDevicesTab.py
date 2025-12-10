from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QHBoxLayout,
                             QScrollArea, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView)

from frontend.widgets.MaterialButton import MaterialButton
from frontend.widgets.ToastWidget import ToastWidget
from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout


class ModbusDevicesTab(BaseSettingsTabLayout, QVBoxLayout):
    """Modbus Devices Management Tab"""

    def __init__(self, parent_widget=None, controller_service=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)

        self.controller_service = controller_service
        self.parent_widget = parent_widget
        self.devices = []

        self.create_main_content()
        self._load_devices()

    def _load_devices(self):
        """Load configured Modbus devices"""
        self.devices = [
            {"id": 1, "name": "Motor Controller 1", "address": 0, "status": "Online"},
            {"id": 2, "name": "Motor Controller 2", "address": 2, "status": "Online"},
            {"id": 3, "name": "Motor Controller 3", "address": 4, "status": "Online"},
            {"id": 4, "name": "Motor Controller 4", "address": 6, "status": "Offline"},
        ]
        self._populate_device_table()

    def create_main_content(self):
        """Create the main UI content"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        content_layout.addWidget(self.create_devices_list_group())
        content_layout.addWidget(self.create_device_actions_group())
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        self.addWidget(scroll_area)

    def create_devices_list_group(self):
        """Create devices list group"""
        group = QGroupBox("Configured Modbus Devices")
        layout = QVBoxLayout()

        info_label = QLabel("Manage Modbus devices connected to the system.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)
        self.devices_table.setHorizontalHeaderLabels(["ID", "Device Name", "Address", "Status"])
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.devices_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.devices_table.setMinimumHeight(300)

        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.devices_table)
        group.setLayout(layout)
        return group

    def create_device_actions_group(self):
        """Create device action buttons"""
        group = QGroupBox("Device Management")
        layout = QHBoxLayout()

        self.add_device_btn = MaterialButton("Add Device")
        self.add_device_btn.setMinimumHeight(50)
        self.add_device_btn.clicked.connect(self._on_add_device)
        layout.addWidget(self.add_device_btn)

        self.remove_device_btn = MaterialButton("Remove Device")
        self.remove_device_btn.setMinimumHeight(50)
        self.remove_device_btn.clicked.connect(self._on_remove_device)
        layout.addWidget(self.remove_device_btn)

        self.refresh_btn = MaterialButton("Refresh Status")
        self.refresh_btn.setMinimumHeight(50)
        self.refresh_btn.clicked.connect(self._on_refresh_devices)
        layout.addWidget(self.refresh_btn)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def _populate_device_table(self):
        """Populate the devices table"""
        self.devices_table.setRowCount(len(self.devices))

        for row, device in enumerate(self.devices):
            id_item = QTableWidgetItem(str(device["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.devices_table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(device["name"])
            self.devices_table.setItem(row, 1, name_item)

            addr_item = QTableWidgetItem(str(device["address"]))
            addr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.devices_table.setItem(row, 2, addr_item)

            status_item = QTableWidgetItem(device["status"])
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if device["status"] == "Online":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            self.devices_table.setItem(row, 3, status_item)

    def _on_add_device(self):
        """Handle add device"""
        self.showToast("ℹ️ Add Device (Coming soon)")

    def _on_remove_device(self):
        """Handle remove device"""
        selected = self.devices_table.selectedIndexes()
        if not selected:
            self.showToast("⚠️ Select a device to remove")
            return
        self.showToast("ℹ️ Remove Device (Coming soon)")

    def _on_refresh_devices(self):
        """Handle refresh"""
        self._load_devices()
        self.showToast("✅ Device status refreshed")

    def showToast(self, message):
        """Show toast notification"""
        if hasattr(self, 'parent_widget') and self.parent_widget:
            toast = ToastWidget(parent=self.parent_widget, message=message)
            toast.show()
        else:
            print(f"Toast: {message}")

