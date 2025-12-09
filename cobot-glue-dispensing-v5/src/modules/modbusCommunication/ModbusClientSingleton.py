from threading import Lock
from modules.modbusCommunication.modbus_lock import modbus_lock
from modules.modbusCommunication.ModbusClient import ModbusClient
from typing import Optional


class ModbusClientSingleton:
    """
    Singleton обвивка (wrapper) за ModbusClient, гарантираща, че се използва само
    една инстанция на ModbusClient в цялото приложение. Полезно за управление
    на споделени хардуерни комуникационни ресурси.

    Атрибути:
        _client_instance (Optional[ModbusClient]): Статична променлива, съдържаща singleton инстанцията.
        _lock (Lock): Lock обект за безопасна инициализация в мултитред среда.
    """
    _client_instance: Optional[ModbusClient] = None
    _lock: Lock = modbus_lock

    @staticmethod
    def get_instance(slave: int = 10, port: str = 'COM5', baudrate: int = 115200,
                     bytesize: int = 8, stopbits: int = 1, timeout: float = 0.01,
                     max_retries: int = 30) -> ModbusClient:
        """
        Връща singleton инстанцията на ModbusClient. Ако тя още не съществува,
        се създава нова с подадените параметри, включително max_retries.
        Използва double-checked locking за безопасна инициализация в мултитред среда.

        Параметри:
            slave (int): Адрес на Modbus slave устройство.
            port (str): Серийният порт за комуникация (например 'COM5').
            baudrate (int): Скорост на сериен порт.
            bytesize (int): Размер на байт.
            stopbits (int): Брой стоп-бита.
            timeout (float): Таймаут за комуникация в секунди.
            max_retries (int): Максимален брой опити при комуникационни грешки.

        Връща:
            ModbusClient: Singleton инстанция на ModbusClient.
        """
        if ModbusClientSingleton._client_instance is None:
            with ModbusClientSingleton._lock:
                if ModbusClientSingleton._client_instance is None:  # Double-checked locking
                    ModbusClientSingleton._client_instance = ModbusClient(
                        slave, port, baudrate, bytesize, stopbits, timeout, max_retries=max_retries
                    )
        return ModbusClientSingleton._client_instance

    @staticmethod
    def get_lock() -> Lock:
        """
        Връща lock обекта, използван за синхронизация на singleton инстанцията.

        Връща:
            Lock: Lock обект за thread-safe операции с ModbusClientSingleton.
        """
        return ModbusClientSingleton._lock
