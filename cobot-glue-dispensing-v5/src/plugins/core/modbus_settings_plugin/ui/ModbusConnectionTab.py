from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QComboBox, QSpinBox, QDoubleSpinBox,
                             QScrollArea, QGroupBox, QGridLayout, QLineEdit, QHBoxLayout)
from frontend.widgets.MaterialButton import MaterialButton
from frontend.widgets.ToastWidget import ToastWidget
from plugins.core.settings.ui.BaseSettingsTabLayout import BaseSettingsTabLayout


class ModbusConnectionTab(BaseSettingsTabLayout, QVBoxLayout):
    """Modbus RTU Connection Settings Tab"""
    value_changed_signal = pyqtSignal(str, object, str)

    def __init__(self, parent_widget=None, controller_service=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing ModbusConnectionTab with controller_service: {controller_service}")
        self.controller_service = controller_service
        self.parent_widget = parent_widget
        self.config = {}
        # Load configuration via endpoints
        self._load_settings_from_endpoints()
        # Create UI
        self.create_main_content()
        # Connect auto-save signals
        self._connect_auto_save_signals()

    def _load_settings_from_endpoints(self):
        """Load Modbus settings via SettingsService"""
        if not self.controller_service:
            print("Warning: controller_service not available, using defaults")
            self._use_default_config()
            return
        try:
            print("Loading Modbus settings via SettingsService...")
            result = self.controller_service.settings.get_modbus_settings()
            if result.success:
                self.config = result.data
                print(f"Successfully loaded Modbus config: {self.config}")
            else:
                print(f"Failed to load Modbus config: {result.message}")
                self._use_default_config()
        except Exception as e:
            print(f"Error loading Modbus settings: {e}")
            import traceback
            traceback.print_exc()
            self._use_default_config()

    def _use_default_config(self):
        """Use default configuration"""
        self.config = {
            'port': 'COM5',
            'baudrate': 115200,
            'bytesize': 8,
            'stopbits': 1,
            'parity': 'N',
            'timeout': 0.01,
            'slave_address': 10,
            'max_retries': 30
        }

    def create_main_content(self):
        """Create the main UI content"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        # Add groups
        content_layout.addWidget(self.create_connection_group())
        content_layout.addWidget(self.create_communication_group())
        content_layout.addWidget(self.create_advanced_group())
        content_layout.addWidget(self.create_test_group())
        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        self.addWidget(scroll_area)

    def create_connection_group(self):
        """Create serial connection settings group"""
        group = QGroupBox("Serial Connection")
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setColumnStretch(1, 1)
        row = 0
        # Serial Port
        label = QLabel("Serial Port:")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        port_layout = QHBoxLayout()
        port_layout.setSpacing(10)

        self.port_input = QLineEdit()
        self.port_input.setText(self.config.get('port', 'COM5'))
        self.port_input.setPlaceholderText("e.g., COM5, /dev/ttyUSB0")
        self.port_input.setMinimumHeight(40)
        port_layout.addWidget(self.port_input, stretch=3)

        self.detect_port_button = MaterialButton("Detect Port")
        self.detect_port_button.setMinimumHeight(40)
        self.detect_port_button.setMaximumWidth(150)
        self.detect_port_button.clicked.connect(self._on_detect_port)
        port_layout.addWidget(self.detect_port_button, stretch=1)

        layout.addLayout(port_layout, row, 1)
        row += 1
        # Baudrate
        label = QLabel("Baudrate:")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.baudrate_dropdown = QComboBox()
        self.baudrate_dropdown.setMinimumHeight(40)
        self.baudrate_dropdown.addItems(["9600", "19200", "38400", "57600", "115200", "230400"])
        baudrate = str(self.config.get('baudrate', 115200))
        index = self.baudrate_dropdown.findText(baudrate)
        if index >= 0:
            self.baudrate_dropdown.setCurrentIndex(index)
        layout.addWidget(self.baudrate_dropdown, row, 1)
        row += 1
        # Bytesize
        label = QLabel("Data Bits:")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.bytesize_dropdown = QComboBox()
        self.bytesize_dropdown.setMinimumHeight(40)
        self.bytesize_dropdown.addItems(["5", "6", "7", "8"])
        bytesize = str(self.config.get('bytesize', 8))
        index = self.bytesize_dropdown.findText(bytesize)
        if index >= 0:
            self.bytesize_dropdown.setCurrentIndex(index)
        layout.addWidget(self.bytesize_dropdown, row, 1)
        row += 1
        # Stopbits
        label = QLabel("Stop Bits:")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.stopbits_dropdown = QComboBox()
        self.stopbits_dropdown.setMinimumHeight(40)
        self.stopbits_dropdown.addItems(["1", "1.5", "2"])
        stopbits = str(self.config.get('stopbits', 1))
        index = self.stopbits_dropdown.findText(stopbits)
        if index >= 0:
            self.stopbits_dropdown.setCurrentIndex(index)
        layout.addWidget(self.stopbits_dropdown, row, 1)
        row += 1
        # Parity
        label = QLabel("Parity:")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.parity_dropdown = QComboBox()
        self.parity_dropdown.setMinimumHeight(40)
        self.parity_dropdown.addItems([
            "None (N)",
            "Even (E)",
            "Odd (O)",
            "Mark (M)",
            "Space (S)"
        ])
        parity = self.config.get('parity', 'N')
        parity_map = {'N': 0, 'E': 1, 'O': 2, 'M': 3, 'S': 4}
        index = parity_map.get(parity, 0)
        self.parity_dropdown.setCurrentIndex(index)
        layout.addWidget(self.parity_dropdown, row, 1)
        group.setLayout(layout)
        return group

    def create_communication_group(self):
        """Create Modbus communication settings group"""
        group = QGroupBox("Modbus Settings")
        layout = QGridLayout()
        layout.setSpacing(15)
        layout.setColumnStretch(1, 1)
        row = 0
        # Slave Address
        label = QLabel("Slave Address:")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.slave_address_spinbox = QSpinBox()
        self.slave_address_spinbox.setMinimum(1)
        self.slave_address_spinbox.setMaximum(247)
        self.slave_address_spinbox.setValue(self.config.get('slave_address', 10))
        self.slave_address_spinbox.setMinimumHeight(40)
        layout.addWidget(self.slave_address_spinbox, row, 1)
        row += 1
        # Timeout
        label = QLabel("Timeout (seconds):")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.timeout_spinbox = QDoubleSpinBox()
        self.timeout_spinbox.setMinimum(0.001)
        self.timeout_spinbox.setMaximum(10.0)
        self.timeout_spinbox.setSingleStep(0.01)
        self.timeout_spinbox.setDecimals(3)
        self.timeout_spinbox.setValue(self.config.get('timeout', 0.01))
        self.timeout_spinbox.setMinimumHeight(40)
        layout.addWidget(self.timeout_spinbox, row, 1)
        row += 1
        # Max Retries
        label = QLabel("Max Retries:")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.max_retries_spinbox = QSpinBox()
        self.max_retries_spinbox.setMinimum(1)
        self.max_retries_spinbox.setMaximum(100)
        self.max_retries_spinbox.setValue(self.config.get('max_retries', 30))
        self.max_retries_spinbox.setMinimumHeight(40)
        layout.addWidget(self.max_retries_spinbox, row, 1)
        group.setLayout(layout)
        return group

    def create_advanced_group(self):
        """Create advanced settings group"""
        group = QGroupBox("Advanced Settings")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        info_label = QLabel(
            "⚠️ Changing these settings may affect communication stability.\n"
            "Only modify if you understand Modbus RTU protocol."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #ff9800; padding: 10px;")
        layout.addWidget(info_label)
        group.setLayout(layout)
        return group

    def create_test_group(self):
        """Create connection test group"""
        group = QGroupBox("Connection Test")
        layout = QVBoxLayout()
        layout.setSpacing(15)
        # Test button
        self.test_button = MaterialButton("Test Connection")
        self.test_button.setMinimumHeight(50)
        self.test_button.clicked.connect(self._on_test_connection)
        layout.addWidget(self.test_button)
        # Status label
        self.status_label = QLabel("Click 'Test Connection' to verify Modbus communication")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("padding: 15px; background: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.status_label)
        group.setLayout(layout)
        return group

    def _connect_auto_save_signals(self):
        """Connect all input widgets to auto-save"""
        self.port_input.textChanged.connect(lambda: self._on_field_changed('port', self.port_input.text()))
        self.baudrate_dropdown.currentTextChanged.connect(
            lambda: self._on_field_changed('baudrate', int(self.baudrate_dropdown.currentText())))
        self.bytesize_dropdown.currentTextChanged.connect(
            lambda: self._on_field_changed('bytesize', int(self.bytesize_dropdown.currentText())))
        self.stopbits_dropdown.currentTextChanged.connect(
            lambda: self._on_field_changed('stopbits', int(float(self.stopbits_dropdown.currentText()))))
        self.parity_dropdown.currentIndexChanged.connect(self._on_parity_changed)
        self.slave_address_spinbox.valueChanged.connect(
            lambda: self._on_field_changed('slave_address', self.slave_address_spinbox.value()))
        self.timeout_spinbox.valueChanged.connect(
            lambda: self._on_field_changed('timeout', self.timeout_spinbox.value()))
        self.max_retries_spinbox.valueChanged.connect(
            lambda: self._on_field_changed('max_retries', self.max_retries_spinbox.value()))

    def _on_parity_changed(self, index):
        """Handle parity change"""
        parity_values = ['N', 'E', 'O', 'M', 'S']
        parity = parity_values[index] if index < len(parity_values) else 'N'
        self._on_field_changed('parity', parity)

    def _on_field_changed(self, field, value):
        """Handle field change and save via SettingsService"""
        if not self.controller_service:
            print(f"Cannot save {field}: controller_service not available")
            return
        try:
            result = self.controller_service.settings.update_modbus_setting(field, value)
            if result.success:
                self.config[field] = value
                print(f"[Modbus Config] {field} updated to: {value}")
                self.showToast(f"✅ {field.replace('_', ' ').title()} updated")
            else:
                print(f"Failed to update {field}: {result.message}")
                self.showToast(f"❌ Failed to update {field}")
        except Exception as e:
            print(f"Error updating {field}: {e}")
            import traceback
            traceback.print_exc()
            self.showToast(f"❌ Error updating {field}")

    def _on_test_connection(self):
        """Test Modbus connection via SettingsService"""
        self.status_label.setText("Testing connection...")
        self.status_label.setStyleSheet("padding: 15px; background: #fff3cd; border-radius: 5px; color: #856404;")
        self.test_button.setEnabled(False)
        try:
            result = self.controller_service.settings.test_modbus_connection()
            if result.success:
                self.status_label.setText(f"✅ Connection successful!\n{result.message}")
                self.status_label.setStyleSheet(
                    "padding: 15px; background: #d4edda; border-radius: 5px; color: #155724;")
                self.showToast("✅ Modbus connection successful")
            else:
                self.status_label.setText(f"❌ Connection failed:\n{result.message}")
                self.status_label.setStyleSheet(
                    "padding: 15px; background: #f8d7da; border-radius: 5px; color: #721c24;")
                self.showToast("❌ Connection test failed")
        except Exception as e:
            self.status_label.setText(f"❌ Error testing connection:\n{str(e)}")
            self.status_label.setStyleSheet("padding: 15px; background: #f8d7da; border-radius: 5px; color: #721c24;")
            self.showToast("❌ Connection test error")
            print(f"Error testing connection: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.test_button.setEnabled(True)

    def _on_detect_port(self):
        """Detect available Modbus port via SettingsService"""
        if not self.controller_service:
            print("Cannot detect port: controller_service not available")
            self.showToast("❌ Service unavailable")
            return

        self.detect_port_button.setEnabled(False)
        self.detect_port_button.setText("Detecting...")

        try:
            result = self.controller_service.settings.detect_modbus_port()

            if result.success:
                detected_port = result.data.get('port', '')
                if detected_port and detected_port.strip():
                    self.port_input.setText(detected_port)
                    self.showToast(f"✅ Port detected: {detected_port}")
                    print(f"Detected Modbus port: {detected_port}")
                else:
                    self.showToast("❌ No port detected")
                    print("No Modbus port detected")
            else:
                self.showToast(f"❌ {result.message}")
                print(f"Failed to detect port: {result.message}")
        except Exception as e:
            self.showToast("❌ Error detecting port")
            print(f"Error detecting port: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.detect_port_button.setEnabled(True)
            self.detect_port_button.setText("Detect Port")

    def showToast(self, message):
        """Show toast notification"""
        if hasattr(self, 'parent_widget') and self.parent_widget:
            toast = ToastWidget(parent=self.parent_widget, message=message)
            toast.show()
        else:
            print(f"Toast: {message}")
