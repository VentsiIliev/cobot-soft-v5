# ---------- UI Layout ----------
from PyQt6.QtCore import Qt, pyqtSignal

from modules.modbusCommunication.ModbusController import ModbusParity, ModbusClientConfig
# import QVBoxLayout
from PyQt6.QtWidgets import QVBoxLayout, QScrollArea, QWidget, QGroupBox, QGridLayout, QLabel, QSpinBox, QComboBox

class ModbusConfigTabLayout(QVBoxLayout):
    value_changed_signal = pyqtSignal(str, object)  # key, value

    def __init__(self, parent_widget=None, config: ModbusClientConfig = None):
        super().__init__()
        self.parent_widget = parent_widget
        self.config = config or ModbusClientConfig(
            slave_id=1, port="COM1", baudrate=9600, byte_size=8,
            parity=ModbusParity.NONE, stop_bits=1,
            timeout=0.02, inter_byte_timeout=0.01, max_retries=3
        )
        self.create_main_content()

    # ---------------- Main Scroll Area ----------------
    def create_main_content(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Add Modbus Settings Groups
        content_layout.addWidget(self.create_general_settings_group())
        content_layout.addWidget(self.create_advanced_settings_group())

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)

        scroll_container = QWidget()
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(scroll_area)

        self.addWidget(scroll_container)

    # ---------------- Groups ----------------
    def create_general_settings_group(self):
        group = QGroupBox("General Modbus Settings")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0
        # Slave ID
        layout.addWidget(QLabel("Slave ID"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.slave_id_input = QSpinBox()
        self.slave_id_input.setRange(1, 247)
        self.slave_id_input.setValue(self.config.slave_id)
        self.slave_id_input.valueChanged.connect(lambda v: self.emit_change("slave_id", v))
        layout.addWidget(self.slave_id_input, row, 1)

        row += 1
        # Port
        layout.addWidget(QLabel("Port"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.port_input = QComboBox()
        # Example: Fill COM ports dynamically if needed
        self.port_input.addItems(["COM1", "COM2", "COM3"])
        self.port_input.setCurrentText(self.config.port)
        self.port_input.currentTextChanged.connect(lambda v: self.emit_change("port", v))
        layout.addWidget(self.port_input, row, 1)

        row += 1
        # Baudrate
        layout.addWidget(QLabel("Baudrate"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.baudrate_input = QSpinBox()
        self.baudrate_input.setRange(1200, 115200)
        self.baudrate_input.setValue(self.config.baudrate)
        self.baudrate_input.valueChanged.connect(lambda v: self.emit_change("baudrate", v))
        layout.addWidget(self.baudrate_input, row, 1)

        row += 1
        # Byte Size
        layout.addWidget(QLabel("Byte Size"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.byte_size_input = QSpinBox()
        self.byte_size_input.setRange(5, 8)
        self.byte_size_input.setValue(self.config.byte_size)
        self.byte_size_input.valueChanged.connect(lambda v: self.emit_change("byte_size", v))
        layout.addWidget(self.byte_size_input, row, 1)

        row += 1
        # Parity
        layout.addWidget(QLabel("Parity"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.parity_input = QComboBox()
        self.parity_input.addItems([p.name for p in ModbusParity])
        self.parity_input.setCurrentText(self.config.parity.name)
        self.parity_input.currentTextChanged.connect(lambda v: self.emit_change("parity", ModbusParity[v]))
        layout.addWidget(self.parity_input, row, 1)

        row += 1
        # Stop Bits
        layout.addWidget(QLabel("Stop Bits"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.stop_bits_input = QSpinBox()
        self.stop_bits_input.setRange(1, 2)
        self.stop_bits_input.setValue(self.config.stop_bits)
        self.stop_bits_input.valueChanged.connect(lambda v: self.emit_change("stop_bits", v))
        layout.addWidget(self.stop_bits_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_advanced_settings_group(self):
        group = QGroupBox("Advanced Modbus Settings")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0
        # Timeout
        layout.addWidget(QLabel("Timeout (s)"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.timeout_input = QDoubleSpinBox()
        self.timeout_input.setRange(0.001, 5.0)
        self.timeout_input.setDecimals(3)
        self.timeout_input.setSingleStep(0.01)
        self.timeout_input.setValue(self.config.timeout)
        self.timeout_input.valueChanged.connect(lambda v: self.emit_change("timeout", v))
        layout.addWidget(self.timeout_input, row, 1)

        row += 1
        # Inter-byte Timeout
        layout.addWidget(QLabel("Inter-byte Timeout (s)"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.inter_byte_timeout_input = QDoubleSpinBox()
        self.inter_byte_timeout_input.setRange(0.001, 1.0)
        self.inter_byte_timeout_input.setDecimals(3)
        self.inter_byte_timeout_input.setSingleStep(0.01)
        self.inter_byte_timeout_input.setValue(self.config.inter_byte_timeout)
        self.inter_byte_timeout_input.valueChanged.connect(lambda v: self.emit_change("inter_byte_timeout", v))
        layout.addWidget(self.inter_byte_timeout_input, row, 1)

        row += 1
        # Max retries
        layout.addWidget(QLabel("Max Retries"), row, 0, Qt.AlignmentFlag.AlignLeft)
        self.max_retries_input = QSpinBox()
        self.max_retries_input.setRange(0, 10)
        self.max_retries_input.setValue(self.config.max_retries)
        self.max_retries_input.valueChanged.connect(lambda v: self.emit_change("max_retries", v))
        layout.addWidget(self.max_retries_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    # ---------------- Helper ----------------
    def emit_change(self, key, value):
        print(f"🔧 Modbus setting changed: {key} = {value}")
        self.value_changed_signal.emit(key, value)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget, QDoubleSpinBox, QLabel, QGroupBox, QGridLayout, QSpinBox, \
    QComboBox, QVBoxLayout, QScrollArea

    app = QApplication(sys.argv)
    window = QWidget()
    layout = ModbusConfigTabLayout(window)
    window.setLayout(layout)
    window.setWindowTitle("Modbus Configuration")
    window.resize(400, 600)
    window.show()
    sys.exit(app.exec())