from modules.modbusCommunication.ModbusClient import ModbusClient
import minimalmodbus
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import json

from modules.shared.utils.linuxUtils import get_modbus_port


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
    timeout: float
    inter_byte_timeout: float
    max_retries: int


SUDO_PASS = "plp"


def load_modbus_config() -> dict:
    """
    Load Modbus configuration from settings file.

    Returns:
        dict: Modbus configuration
    """
    try:
        from core.application.ApplicationStorageResolver import get_app_settings_path

        config_path = Path(get_app_settings_path("glue_dispensing_application", "modbus_config"))

        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"ModbusController: Loaded config from {config_path}: {config}")
                return config
        else:
            print(f"ModbusController: Config file not found at {config_path}, using defaults")
            return {
                'port': 'COM5',
                'baudrate': 115200,
                'bytesize': 8,
                'stopbits': 1,
                'parity': 'N',
                'timeout': 0.01,
                'slave_address': 10,
                'max_retries': 30
            }
    except Exception as e:
        print(f"ModbusController: Error loading Modbus config: {e}, using defaults")
        return {
            'port': 'COM5',
            'baudrate': 115200,
            'bytesize': 8,
            'stopbits': 1,
            'parity': 'N',
            'timeout': 0.01,
            'slave_address': 10,
            'max_retries': 30
        }


def get_config_from_settings() -> ModbusClientConfig:
    """
    Create ModbusClientConfig from settings file.

    Returns:
        ModbusClientConfig: Configuration object
    """
    settings = load_modbus_config()

    parity_map = {
        'N': ModbusParity.NONE,
        'E': ModbusParity.EVEN,
        'O': ModbusParity.ODD
    }

    port = settings.get('port', 'COM5')
    if port.startswith('COM'):
        try:
            port = get_modbus_port(sudo_password=SUDO_PASS)
        except Exception as e:
            print(f"Error getting Modbus port: {e}, using configured port: {port}")

    return ModbusClientConfig(
        slave_id=settings.get('slave_address', 10),
        port=port,
        baudrate=settings.get('baudrate', 115200),
        byte_size=settings.get('bytesize', 8),
        parity=parity_map.get(settings.get('parity', 'N'), ModbusParity.NONE),
        stop_bits=settings.get('stopbits', 1),
        timeout=settings.get('timeout', 0.01),
        inter_byte_timeout=0.01,
        max_retries=settings.get('max_retries', 30)
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
        config = get_config_from_settings()

        print(f"ModbusController: Creating client for slave {slaveId} with config: "
              f"port={config.port}, baudrate={config.baudrate}, parity={config.parity}, "
              f"timeout={config.timeout}, max_retries={config.max_retries}")

        port: str = config.port
        client: ModbusClient = ModbusClient(slave=slaveId, port=port, max_retries=config.max_retries)

        client.client.serial.baudrate = config.baudrate
        client.client.serial.bytesize = config.byte_size
        client.client.serial.parity = config.parity.value
        client.client.serial.stopbits = config.stop_bits
        client.client.serial.timeout = config.timeout
        client.client.serial.inter_byte_timeout = config.inter_byte_timeout
        client.clear_buffers_before_each_transaction = True
        client.mode = minimalmodbus.MODE_RTU

        return client
