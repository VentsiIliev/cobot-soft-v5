import time
import minimalmodbus
import logging
from typing import List, Tuple, Optional

from applications.glue_dispensing_application.services.glueSprayService.motorControl.errorCodes import \
    ModbusExceptionType
from modules.modbusCommunication.modbus_lock import modbus_lock


class ModbusClient:
    """
    Клас ModbusClient предоставя функционалност за комуникация с Modbus slave устройство
    чрез Modbus RTU протокол по сериен порт. Позволява четене и запис на регистри в
    Modbus slave устройството.

    Атрибути:
        slave (int): Адрес на Modbus slave (по подразбиране 10).
        client (minimalmodbus.Instrument): Инстанция на minimalmodbus Instrument за
                                           Modbus комуникация.
        max_retries (int): Максимален брой опити при неуспешна комуникация.
    """

    def __init__(self, slave: int = 10, port: str = 'COM5', baudrate: int = 115200, bytesize: int = 8,
                 stopbits: int = 1, timeout: float = 0.01, parity: str = minimalmodbus.serial.PARITY_NONE,
                 max_retries: int = 30) -> None:
        """
        Инициализация на ModbusClient.

        Параметри:
            slave (int): Адрес на Modbus slave устройство.
            port (str): Серийният порт за комуникация (например 'COM5').
            baudrate (int): Скорост на сериен порт.
            bytesize (int): Размер на байт.
            stopbits (int): Брой стоп-бита.
            timeout (float): Таймаут за комуникация в секунди.
            parity (str): Паритет (по подразбиране без паритет).
            max_retries (int): Максимален брой опити при комуникационни грешки.

        Изключения:
            Exception: Ако не може да се отвори серийния порт.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.slave: int = slave
        try:
            self.client: minimalmodbus.Instrument = minimalmodbus.Instrument(port, self.slave, debug=False)
        except Exception as e:
            raise Exception(f"ERROR Can not open port {port}. Check the connection and port settings.") from e

        self.client.serial.baudrate = baudrate
        self.client.serial.bytesize = bytesize
        self.client.serial.stopbits = stopbits
        self.client.serial.timeout = timeout
        self.client.serial.parity = parity
        self.max_retries: int = max_retries

    def writeRegister(self, register: int, value: float, signed: bool = False) -> Optional[ModbusExceptionType]:
        """
        Записва стойност в конкретен регистър на Modbus устройството.

        Параметри:
            register (int): Регистър, в който ще се записва.
            value (float): Стойност за запис.
            signed (bool): Дали стойността е подписана.

        Връща:
            None, ако записът е успешен.
            ModbusExceptionType при грешка.
        """
        attempts = 0
        while attempts < self.max_retries:
            with modbus_lock:
                try:
                    self.client.write_register(register, value, signed=signed)
                    return None
                except Exception as e:
                    modbus_error = ModbusExceptionType.from_exception(e)
                    print(
                        f"ModbusClient.writeRegister -> ERROR writing register {register}: {e} - {modbus_error.name}: {modbus_error.description()}")
                    import traceback
                    traceback.print_exc()
                    attempts += 1
                    if attempts < self.max_retries:
                        time.sleep(0.1)
                    else:
                        return modbus_error

        return ModbusExceptionType.MODBUS_EXCEPTION

    def writeRegisters(self, start_register: int, values: List[float]) -> Optional[ModbusExceptionType]:
        """
        Записва последователност от стойности, започвайки от даден регистър.

        Параметри:
            start_register (int): Първи регистър за запис.
            values (List[float]): Стойности за запис.

        Връща:
            None при успешен запис.
            ModbusExceptionType при грешка.
        """
        attempts = 0
        while attempts < self.max_retries:
            with modbus_lock:
                try:
                    self.client.write_registers(start_register, values)
                    time.sleep(0.02)
                    return None
                except Exception as e:
                    modbus_error = ModbusExceptionType.from_exception(e)
                    import traceback
                    traceback.print_exc()
                    attempts += 1
                    if attempts >= self.max_retries:
                        return modbus_error

        return ModbusExceptionType.MODBUS_EXCEPTION

    def readRegisters(self, start_register: int, count: int) -> Tuple[
        Optional[List[int]], Optional[ModbusExceptionType]]:
        """
        Чете последователност от регистри, започвайки от даден регистър.

        Параметри:
            start_register (int): Първи регистър за четене.
            count (int): Брой регистри за четене.

        Връща:
            tuple: (values, None) при успешен прочит.
            tuple: (None, ModbusExceptionType) при грешка.
        """
        attempts = 0
        while attempts < self.max_retries:
            with modbus_lock:
                try:
                    values = self.client.read_registers(start_register, count)
                    return values, None
                except Exception as e:
                    print(f"ModbusClient.readRegisters -> ERROR reading registers: {e}")
                    modbus_error = ModbusExceptionType.from_exception(e)
                    attempts += 1
                    if attempts >= self.max_retries:
                        return None, modbus_error

        return None, ModbusExceptionType.MODBUS_EXCEPTION

    def read(self, register: int) -> Tuple[Optional[int], Optional[ModbusExceptionType]]:
        """
        Чете стойност от конкретен регистър.

        Параметри:
            register (int): Регистър за четене.

        Връща:
            tuple: (стойност, None) при успешен прочит.
            tuple: (None, ModbusExceptionType) при грешка.
        """
        attempts = 0
        while attempts < self.max_retries:
            with modbus_lock:
                try:
                    value = self.client.read_register(register)
                    return value, None
                except Exception as e:
                    modbus_error = ModbusExceptionType.from_exception(e)
                    if modbus_error == ModbusExceptionType.CHECKSUM_ERROR:
                        return None, modbus_error
                    attempts += 1
                    if attempts >= self.max_retries:
                        return None, modbus_error

        return None, ModbusExceptionType.MODBUS_EXCEPTION

    def readBit(self, address: int, functioncode: int = 1) -> int:
        """
        Чете отделен бит от Modbus устройство.

        Параметри:
            address (int): Адрес на бита.
            functioncode (int): Функционален код (по подразбиране 1).

        Връща:
            int: Стойност на бита (0 или 1).
        """
        with modbus_lock:
            return self.client.read_bit(address, functioncode=functioncode)

    def writeBit(self, address: int, value: int) -> None:
        """
        Записва стойност в отделен бит на Modbus устройство.

        Параметри:
            address (int): Адрес на бита.
            value (int): Стойност за запис (0 или 1).
        """
        attempts = 0
        while attempts < self.max_retries:
            with modbus_lock:
                try:
                    self.client.write_bit(address, value)
                    break
                except minimalmodbus.ModbusException as e:
                    import traceback
                    traceback.print_exc()
                    attempts += 1
                    time.sleep(0.1)

    def close(self) -> None:
        """
        Затваря серийния порт и освобождава ресурсите.
        """
        self.client.serial.close()
