from modules.modbusCommunication.ModbusClient import ModbusClient
# from utils.linuxUtils import get_modbus_port
import minimalmodbus
from enum import Enum
from dataclasses import dataclass

class ModbusParity(Enum):
    NONE = minimalmodbus.serial.PARITY_NONE
    EVEN = minimalmodbus.serial.PARITY_EVEN
    ODD = minimalmodbus.serial.PARITY_ODD

@dataclass
class ModbusClientConfig:
    slave_id: int
    port: str
    baudrate: int
    byte_size: int
    parity: ModbusParity
    stop_bits: int
    timeout:float  # 20 ms timeout
    inter_byte_timeout: float  # 10 ms delay
    max_retries: int


config = ModbusClientConfig(
    slave_id=1,
    port="/dev/ttyUSB0",
    baudrate=115200,
    byte_size=8,
    parity=ModbusParity.NONE,
    stop_bits=1,
    timeout=0.02,  # 20 ms timeout
    inter_byte_timeout=0.01,  # 10 ms delay
    max_retries=30
)

class ModbusController:
    @classmethod
    def getModbusClient(cls,slaveId):
        # port = get_modbus_port()
        port = config.port
        # port = "/dev/ttyS1"
        # client = minimalmodbus.Instrument(port, slaveId)
        client = ModbusClient(slave=slaveId, port=port,max_retries=config.max_retries)
        # print(f"Connected Port: {port} Slave Id: {slaveId}")

        """CLIENT CONFIG"""
        client.client.serial.baudrate = config.baudrate
        client.client.serial.bytesize = config.byte_size
        client.client.serial.parity = config.parity.value
        client.client.serial.stopbits = config.stop_bits
        client.client.serial.timeout = config.timeout  # 10 ms timeout
        client.clear_buffers_before_each_transaction = True
        # client.close_port_after_each_call = False
        client.mode = minimalmodbus.MODE_RTU
        client.client.serial.inter_byte_timeout = config.inter_byte_timeout  # 10 ms delay

        return client

