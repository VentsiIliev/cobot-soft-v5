# Документация за Modbus модули

Тази документация описва Modbus комуникационния слой на приложението, включително класовете `ModbusClient`, `ModbusClientSingleton`, `ModbusController` и помощните обекти за синхронизация (`modbus_lock`).  

---

## Съдържание

1. [ModbusClient](#modbusclient)
2. [modbus_lock](#modbus_lock)
3. [ModbusClientSingleton](#modbusclientsingleton)
4. [ModbusController и ModbusClientConfig](#modbuscontroller-и-modbusclientconfig)
5. [Примерна употреба](#примерна-употреба)

---

## ModbusClient

**Клас:** `ModbusClient`  
**Описание:** Клас за комуникация с Modbus slave устройства чрез Modbus RTU протокол по сериен порт. Позволява четене и писане на регистри и битове.  

### Атрибути

- `slave: int` – Адрес на Modbus slave устройство.  
- `client: minimalmodbus.Instrument` – Минимална Modbus библиотека за комуникация.  
- `max_retries: int` – Максимален брой опити при комуникационни грешки.  

### Методи

#### `writeRegister(register: int, value: float, signed: bool = False) -> Optional[ModbusExceptionType]`
Записва стойност в регистър.  
**Връща:** `None` при успех, `ModbusExceptionType` при грешка.  

#### `writeRegisters(start_register: int, values: List[float]) -> Optional[ModbusExceptionType]`
Записва последователност от стойности в регистри.  
**Връща:** `None` при успех, `ModbusExceptionType` при грешка.  

#### `readRegisters(start_register: int, count: int) -> Tuple[Optional[List[int]], Optional[ModbusExceptionType]]`
Чете последователност от регистри.  
**Връща:** `(values, None)` при успех, `(None, ModbusExceptionType)` при грешка.  

#### `read(register: int) -> Tuple[Optional[int], Optional[ModbusExceptionType]]`
Чете стойност от конкретен регистър.  
**Връща:** `(стойност, None)` при успех, `(None, ModbusExceptionType)` при грешка.  

#### `readBit(address: int, functioncode: int = 1) -> int`
Чете бит от Modbus устройство.  
**Връща:** `0` или `1`.  

#### `writeBit(address: int, value: int) -> None`
Записва бит в Modbus устройство.  

#### `close() -> None`
Затваря серийния порт и освобождава ресурсите.  

---

## modbus_lock

**Обект:** `modbus_lock: threading.Lock`  

**Описание:** Глобален lock обект за синхронизация на Modbus комуникацията. Използва се за безопасно извършване на операции върху сериен порт от множество нишки.  

**Пример за употреба:**
```python
from modules.modbusCommunication.modbus_lock import modbus_lock

with modbus_lock:
    client.write_register(1, 123)
