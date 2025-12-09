from modules.modbusCommunication.ModbusClient import ModbusClient
# from utils.linuxUtils import get_modbus_port
import minimalmodbus
from enum import Enum
from dataclasses import dataclass
from typing import ClassVar


class ModbusParity(Enum):
    """
    Enum за Modbus паритет.

    Атрибути:
        NONE: Без паритет.
        EVEN: Четен паритет.
        ODD: Нечетен паритет.
    """
    NONE = minimalmodbus.serial.PARITY_NONE
    EVEN = minimalmodbus.serial.PARITY_EVEN
    ODD = minimalmodbus.serial.PARITY_ODD


@dataclass
class ModbusClientConfig:
    """
    Конфигурационен dataclass за Modbus клиент.

    Атрибути:
        slave_id (int): ID на Modbus slave устройството.
        port (str): Сериен порт за комуникация.
        baudrate (int): Скорост на сериен порт.
        byte_size (int): Размер на байт.
        parity (ModbusParity): Паритет.
        stop_bits (int): Брой стоп-бита.
        timeout (float): Таймаут за комуникация в секунди.
        inter_byte_timeout (float): Минимално време между байтовете.
        max_retries (int): Максимален брой опити при комуникационни грешки.
    """
    slave_id: int
    port: str
    baudrate: int
    byte_size: int
    parity: ModbusParity
    stop_bits: int
    timeout: float  # 20 ms timeout
    inter_byte_timeout: float  # 10 ms delay
    max_retries: int


# Примерна конфигурация
config: ModbusClientConfig = ModbusClientConfig(
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
    """
    Контролер за създаване и конфигуриране на Modbus клиенти.

    Методи:
        getModbusClient(slaveId: int) -> ModbusClient:
            Връща конфигуриран ModbusClient за подаден slave ID.
    """
    @classmethod
    def getModbusClient(cls, slaveId: int) -> ModbusClient:
        """
        Създава и конфигурира ModbusClient според глобалната конфигурация.

        Параметри:
            slaveId (int): ID на Modbus slave устройството.

        Връща:
            ModbusClient: Конфигуриран клиент за комуникация.
        """
        # port = get_modbus_port()
        port: str = config.port
        client: ModbusClient = ModbusClient(slave=slaveId, port=port, max_retries=config.max_retries)

        # Конфигурация на клиента
        client.client.serial.baudrate = config.baudrate
        client.client.serial.bytesize = config.byte_size
        client.client.serial.parity = config.parity.value
        client.client.serial.stopbits = config.stop_bits
        client.client.serial.timeout = config.timeout
        client.client.serial.inter_byte_timeout = config.inter_byte_timeout
        client.clear_buffers_before_each_transaction = True
        client.mode = minimalmodbus.MODE_RTU
        # client.close_port_after_each_call = False  # коментирано в текущата версия

        return client
