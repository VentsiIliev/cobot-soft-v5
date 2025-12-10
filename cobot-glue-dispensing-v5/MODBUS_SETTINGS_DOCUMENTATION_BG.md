# Документация за Modbus Настройки
## Съдържание
1. [Преглед](#преглед)
2. [Архитектура](#архитектура)
3. [Потока на Данните](#потока-на-данните)
4. [Файлова Структура](#файлова-структура)
5. [API Endpoints](#api-endpoints)
6. [Компоненти](#компоненти)
7. [Примери за Използване](#примери-за-използване)
---
## Преглед
Системата за Modbus настройки имплементира пълен цикъл на управление на конфигурация от потребителския интерфейс до хранилището на данни, следвайки Repository Pattern за консистентност с останалата част от проекта.
### Основни Функционалности
- ✅ Визуализация и редактиране на Modbus RTU конфигурация
- ✅ Автоматично запазване на промените
- ✅ Откриване на наличен сериен порт
- ✅ Тестване на връзката
- ✅ Табулиран интерфейс с Connection и Devices секции
- ✅ Персистентно съхранение в JSON формат
---
## Архитектура
Системата следва многослойна архитектура:
```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer (Frontend)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ModbusSettingsAppWidget                               │  │
│  │  └─ ModbusSettingsContent (Tabs)                      │  │
│  │      ├─ ModbusConnectionTab (Connection Settings)     │  │
│  │      └─ ModbusDevicesTab (Device Management)          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓↑ (controller_service)
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (SettingsService)            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ControllerService.settings (SettingsService)          │  │
│  │  ├─ get_modbus_settings()                             │  │
│  │  ├─ update_modbus_setting(field, value)               │  │
│  │  ├─ test_modbus_connection()                          │  │
│  │  └─ detect_modbus_port()                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓↑ (via RequestSender)
┌─────────────────────────────────────────────────────────────┐
│              Communication Layer (API Gateway)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Controller → RequestSender                            │  │
│  │  └─ MainRouter (dispatch requests)                    │  │
│  │      └─ SettingsDispatcher                            │  │
│  │          └─ handle_modbus_settings()                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓↑ (repository)
┌─────────────────────────────────────────────────────────────┐
│                  Data Access Layer (Repository)              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ModbusSettingsRepository                              │  │
│  │  └─ BaseJsonSettingsRepository                        │  │
│  │      ├─ load() - Зареждане от JSON                    │  │
│  │      ├─ save() - Запазване в JSON                     │  │
│  │      └─ update_field() - Актуализация на поле         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓↑ (file I/O)
┌─────────────────────────────────────────────────────────────┐
│                     Model Layer (Data)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ModbusConfig (dataclass)                              │  │
│  │  - port: str                                          │  │
│  │  - baudrate: int                                      │  │
│  │  - bytesize: int                                      │  │
│  │  - stopbits: int                                      │  │
│  │  - parity: str                                        │  │
│  │  - timeout: float                                     │  │
│  │  - slave_address: int                                 │  │
│  │  - max_retries: int                                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────┐
│                    File System (Storage)                     │
│  ~/.cache/cobot-glue-dispensing-v5/                         │
│    glue_dispensing_application/storage/settings/             │
│      modbus_config.json                                      │
└─────────────────────────────────────────────────────────────┘
```
---
## Потока на Данните
### 1. Зареждане на Конфигурация (UI → Storage)
```
[1] Потребителят отваря Modbus Settings
      ↓
[2] ModbusConnectionTab.__init__()
      ↓
[3] _load_settings_from_endpoints()
      ↓
[4] controller_service.settings.get_modbus_settings()
      ↓
[5] SettingsService.get_modbus_settings()
      ↓
[6] controller.requestSender.send_request(MODBUS_CONFIG_GET)
      ↓
[7] SettingsDispatcher.handle_modbus_settings()
      ↓
[8] ModbusSettingsRepository.load()
      ↓
[9] Чете modbus_config.json от диска
      ↓
[10] ModbusConfig.from_dict(json_data)
      ↓
[11] Връща Response със success и config data
      ↓
[12] ServiceResult обгръща response-а
      ↓
[13] UI попълва полетата с получените данни
```
**Пример код:**
```python
# В ModbusConnectionTab.py
result = self.controller_service.settings.get_modbus_settings()
if result.success:
    self.config = result.data  # {'port': 'COM5', 'baudrate': 115200, ...}
```
### 2. Актуализация на Конфигурация (UI → Storage)
```
[1] Потребителят променя стойност (напр. baudrate)
      ↓
[2] Signal се задейства: baudrate_dropdown.currentTextChanged
      ↓
[3] _on_field_changed('baudrate', 115200)
      ↓
[4] controller_service.settings.update_modbus_setting('baudrate', 115200)
      ↓
[5] SettingsService.update_modbus_setting()
      ↓
[6] controller.requestSender.send_request(MODBUS_CONFIG_UPDATE,
                                          data={'field': 'baudrate', 'value': 115200})
      ↓
[7] SettingsDispatcher.handle_modbus_settings()
      ↓
[8] ModbusSettingsRepository.update_field('baudrate', 115200)
      ↓
[9] Зарежда текущия config от файла
      ↓
[10] config.update_field('baudrate', 115200)
      ↓
[11] Запазва актуализирания config обратно в JSON файла
      ↓
[12] Връща Response със success message
      ↓
[13] ServiceResult обгръща response-а
      ↓
[14] UI показва toast нотификация "✅ Baudrate updated"
```
**Пример код:**
```python
# В ModbusConnectionTab.py
def _on_field_changed(self, field, value):
    result = self.controller_service.settings.update_modbus_setting(field, value)
    if result.success:
        self.config[field] = value
        self.showToast(f"✅ {field} updated")
    # Автоматично запазване при всяка промяна
```
### 3. Откриване на Порт (UI → System → UI)
```
[1] Потребителят кликва "Detect Port"
      ↓
[2] _on_detect_port()
      ↓
[3] Бутонът се деактивира, текстът става "Detecting..."
      ↓
[4] controller_service.settings.detect_modbus_port()
      ↓
[5] SettingsService.detect_modbus_port()
      ↓
[6] controller.requestSender.send_request(MODBUS_GET_AVAILABLE_PORT)
      ↓
[7] SettingsDispatcher.handle_modbus_settings()
      ↓
[8] platform.system() проверка
      ├─ Windows: връща "COM5"
      └─ Linux: извиква get_modbus_port(sudo_password)
      ↓
[9] get_modbus_port() извиква системна команда
      - Търси /dev/ttyUSB* устройства
      - Връща открития порт или празен string
      ↓
[10] Връща Response с port data: {"port": "/dev/ttyUSB0"}
      ↓
[11] ServiceResult обгръща response-а
      ↓
[12] UI попълва port_input полето
      ↓
[13] Автоматично се задейства _on_field_changed('port', '/dev/ttyUSB0')
      ↓
[14] Новият порт се запазва в конфигурацията
      ↓
[15] Toast нотификация: "✅ Port detected: /dev/ttyUSB0"
      ↓
[16] Бутонът се активира отново
```
### 4. Тестване на Връзка (UI → ModbusClient → UI)
```
[1] Потребителят кликва "Test Connection"
      ↓
[2] _on_test_connection()
      ↓
[3] Status label: "Testing connection..."
      ↓
[4] controller_service.settings.test_modbus_connection()
      ↓
[5] SettingsService.test_modbus_connection()
      ↓
[6] controller.requestSender.send_request(MODBUS_TEST_CONNECTION)
      ↓
[7] SettingsDispatcher.handle_modbus_settings()
      ↓
[8] ModbusSettingsRepository.load() - зарежда конфигурацията
      ↓
[9] Създава тестов ModbusClient с параметрите от config
      ↓
[10] ModbusClient инициализира serial connection
      ├─ Success: връзката е успешна
      └─ Error: хвърля изключение (timeout, connection refused, etc.)
      ↓
[11] Затваря тестовата връзка
      ↓
[12] Връща Response със success/error
      ↓
[13] ServiceResult обгръща response-а
      ↓
[14] UI актуализира status label
      ├─ Success: "✅ Connection successful!"
      └─ Error: "❌ Connection failed: [error message]"
      ↓
[15] Toast нотификация с резултата
```
### 5. Използване от ModbusController (Runtime)
```
[1] Приложението се нуждае от Modbus клиент
      ↓
[2] ModbusController.getModbusClient(slaveId=10)
      ↓
[3] load_modbus_config_from_repo()
      ↓
[4] ModbusSettingsRepository.load()
      ↓
[5] Чете modbus_config.json
      ↓
[6] Връща ModbusConfig обект
      ↓
[7] get_config_from_settings()
      ↓
[8] Конвертира ModbusConfig → ModbusClientConfig
      - Маpва parity: 'N' → ModbusParity.NONE
      - Ако port='COM5' (Linux): извиква get_modbus_port()
      ↓
[9] Създава ModbusClient с параметрите
      - serial.baudrate = config.baudrate
      - serial.bytesize = config.bytesize
      - serial.parity = config.parity.value
      - и т.н.
      ↓
[10] Връща конфигуриран ModbusClient готов за използване
```
---
## Файлова Структура
### Frontend (UI Layer)
```
src/plugins/core/modbus_settings_plugin/
├── __init__.py
├── plugin.py                          # Регистрация на plugin
│
├── ui/
│   ├── ModbusSettingsAppWidget.py     # Главен widget на приложението
│   ├── ModbusSettingsContent.py       # Tab контейнер
│   ├── ModbusConnectionTab.py         # Connection настройки UI
│   ├── ModbusDevicesTab.py            # Devices управление UI
│   └── ModbusSettingsTabLayout.py     # (deprecated - заменен с горните)
│
└── icons/
    ├── modbus_connection.png
    └── modbus_devices.png
```
### Communication Layer (API & Routing)
```
src/communication_layer/
├── api/v1/endpoints/
│   └── modbus_endpoints.py            # Дефиниции на endpoints
│
├── api/v1/
│   └── Response.py                    # Response wrapper клас
│
└── api_gateway/
    ├── DomesticRequestSender.py       # Request sender
    │
    └── dispatch/
        ├── main_router.py             # Главен маршрутизатор
        └── settings_dispatcher.py     # Modbus handler логика
```
### Data Access Layer (Repository)
```
src/core/database/settings/
├── BaseJsonSettingsRepository.py      # Базов клас за JSON repositories
├── ModbusSettingsRepository.py        # Modbus repository имплементация
├── RobotSettingsRepository.py         # (същият pattern)
└── CameraSettingsRepository.py        # (същият pattern)
```
### Model Layer (Data Structures)
```
src/core/model/settings/
└── modbusConfig/
    ├── __init__.py
    └── modbusConfigModel.py           # ModbusConfig dataclass
```
### Business Logic (ModbusController)
```
src/modules/modbusCommunication/
├── __init__.py
├── ModbusController.py                # Factory за Modbus клиенти
├── ModbusClient.py                    # Wrapper за minimalmodbus
└── (други Modbus компоненти)
```
### Storage (Персистентни Данни)
```
~/.cache/cobot-glue-dispensing-v5/
└── glue_dispensing_application/
    └── storage/
        └── settings/
            └── modbus_config.json     # Конфигурационен файл
```
---
## API Endpoints
### 1. MODBUS_CONFIG_GET
**Път:** `/api/v1/settings/modbus/config`  
**Метод:** GET  
**Цел:** Зареждане на пълната Modbus конфигурация
**Request:**
```python
controller.requestSender.send_request(modbus_endpoints.MODBUS_CONFIG_GET)
```
**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "port": "COM5",
    "baudrate": 115200,
    "bytesize": 8,
    "stopbits": 1,
    "parity": "N",
    "timeout": 0.01,
    "slave_address": 10,
    "max_retries": 30
  }
}
```
**Response (Error):**
```json
{
  "status": "error",
  "message": "Error loading Modbus configuration: [error details]"
}
```
**Handler:** `SettingsDispatcher.handle_modbus_settings()`
```python
modbus_repo = ModbusSettingsRepository(file_path=str(config_path))
config = modbus_repo.load()
return Response(Constants.RESPONSE_STATUS_SUCCESS, data=config.to_dict()).to_dict()
```
---
### 2. MODBUS_CONFIG_UPDATE
**Път:** `/api/v1/settings/modbus/config/update`  
**Метод:** POST  
**Цел:** Актуализация на отделно поле от конфигурацията
**Request:**
```python
controller.requestSender.send_request(
    modbus_endpoints.MODBUS_CONFIG_UPDATE,
    data={'field': 'baudrate', 'value': 57600}
)
```
**Request Data Schema:**
```json
{
  "field": "baudrate",     // име на полето
  "value": 57600           // нова стойност
}
```
**Валидни Полета:**
- `port` (string)
- `baudrate` (int)
- `bytesize` (int)
- `stopbits` (int)
- `parity` (string: 'N', 'E', 'O', 'M', 'S')
- `timeout` (float)
- `slave_address` (int)
- `max_retries` (int)
**Response (Success):**
```json
{
  "status": "success",
  "message": "Modbus baudrate updated successfully"
}
```
**Response (Error - Missing Fields):**
```json
{
  "status": "error",
  "message": "Missing required fields: field and value"
}
```
**Handler:**
```python
field = data['field']
value = data['value']
modbus_repo.update_field(field, value)
```
---
### 3. MODBUS_TEST_CONNECTION
**Път:** `/api/v1/settings/modbus/test`  
**Метод:** POST  
**Цел:** Тестване на връзката с текущата конфигурация
**Request:**
```python
controller.requestSender.send_request(modbus_endpoints.MODBUS_TEST_CONNECTION)
```
**Response (Success):**
```json
{
  "status": "success",
  "message": "Successfully connected to Modbus slave at COM5"
}
```
**Response (Error):**
```json
{
  "status": "error",
  "message": "Connection test failed: [Errno 2] No such file or directory: 'COM5'"
}
```
**Handler Логика:**
```python
config = modbus_repo.load()
# Създава тестов Modbus клиент
test_client = ModbusClient(
    slave=config.slave_address,
    port=config.port,
    baudrate=config.baudrate,
    bytesize=config.bytesize,
    stopbits=config.stopbits,
    timeout=config.timeout,
    parity=parity_map.get(config.parity),
    max_retries=config.max_retries
)
# Затваря връзката след теста
test_client.client.serial.close()
```
---
### 4. MODBUS_GET_AVAILABLE_PORT
**Път:** `/api/v1/settings/modbus/available/port`  
**Метод:** GET  
**Цел:** Откриване на наличен сериен порт в системата
**Request:**
```python
controller.requestSender.send_request(modbus_endpoints.MODBUS_GET_AVAILABLE_PORT)
```
**Response (Success - Port Found):**
```json
{
  "status": "success",
  "data": {
    "port": "/dev/ttyUSB0"
  },
  "message": "Detected Modbus port: /dev/ttyUSB0"
}
```
**Response (Error - No Port):**
```json
{
  "status": "error",
  "message": "No Modbus port detected. Please ensure the device is connected."
}
```
**Handler Логика:**
```python
if platform.system() == "Windows":
    port = "COM5"
else:
    from modules.shared.utils.linuxUtils import get_modbus_port
    port = get_modbus_port(sudo_password="plp")
    if not port or port.strip() == "":
        return Response(
            Constants.RESPONSE_STATUS_ERROR,
            message="No Modbus port detected..."
        ).to_dict()
return Response(
    Constants.RESPONSE_STATUS_SUCCESS,
    data={"port": port},
    message=f"Detected Modbus port: {port}"
).to_dict()
```
---
## Компоненти
### 1. ModbusConfig (Модел)
**Файл:** `src/core/model/settings/modbusConfig/modbusConfigModel.py`
**Описание:** Dataclass, представящ Modbus конфигурация с типова безопасност.
**Структура:**
```python
@dataclass
class ModbusConfig:
    port: str = 'COM5'              # Сериен порт (COM5, /dev/ttyUSB0)
    baudrate: int = 115200          # Скорост (9600, 19200, 38400, 57600, 115200)
    bytesize: int = 8               # Data bits (5, 6, 7, 8)
    stopbits: int = 1               # Stop bits (1, 1.5, 2)
    parity: str = 'N'               # Parity (N, E, O, M, S)
    timeout: float = 0.01           # Timeout в секунди
    slave_address: int = 10         # Modbus slave адрес (1-247)
    max_retries: int = 30           # Максимален брой повторения
```
**Методи:**
```python
# Създаване от dictionary
config = ModbusConfig.from_dict({
    'port': '/dev/ttyUSB0',
    'baudrate': 57600
})
# Конвертиране към dictionary
config_dict = config.to_dict()
# Актуализация на поле
config.update_field('baudrate', 115200)
```
**Валидация:**
- Хвърля `ValueError` при опит за актуализация на несъществуващо поле
- Type hints гарантират типова коректност
---
### 2. ModbusSettingsRepository (Repository)
**Файл:** `src/core/database/settings/ModbusSettingsRepository.py`
**Описание:** Управлява персистентното съхранение на Modbus конфигурация.
**Наследява:** `BaseJsonSettingsRepository[ModbusConfig]`
**Публични Методи:**
#### load() → ModbusConfig
Зарежда конфигурацията от JSON файла.
```python
repo = ModbusSettingsRepository(file_path="/path/to/modbus_config.json")
config = repo.load()  # Връща ModbusConfig обект
```
**Поведение:**
- Ако файлът не съществува → създава го с default стойности
- Ако файлът е повреден → връща default конфигурация
- Автоматично принтира съобщения за дебъг
#### save(config: ModbusConfig) → None
Запазва конфигурацията в JSON файла.
```python
config = ModbusConfig(baudrate=57600)
repo.save(config)
```
**Поведение:**
- Създава директориите, ако не съществуват
- Форматира JSON с indentation
- Хвърля `SettingsSaveError` при грешка
#### update_field(field: str, value: Any) → None
Актуализира отделно поле.
```python
repo.update_field('baudrate', 115200)
```
**Поведение:**
1. Зарежда текущата конфигурация
2. Актуализира полето
3. Запазва обратно
#### exists() → bool
Проверява дали файлът съществува.
```python
if repo.exists():
    config = repo.load()
else:
    config = repo.get_default()
```
---
### 3. SettingsDispatcher (Handler)
**Файл:** `src/communication_layer/api_gateway/dispatch/settings_dispatcher.py`
**Описание:** Маршрутизира и обработва Modbus настройки заявки.
**Метод:** `handle_modbus_settings(parts, request, data=None)`
**Маршрутизация:**
```python
if request == modbus_endpoints.MODBUS_CONFIG_GET:
    # Зареждане на конфигурация
elif request == modbus_endpoints.MODBUS_CONFIG_UPDATE:
    # Актуализация на поле
elif request == modbus_endpoints.MODBUS_TEST_CONNECTION:
    # Тестване на връзка
elif request == modbus_endpoints.MODBUS_GET_AVAILABLE_PORT:
    # Откриване на порт
```
**Възвръщаема Стойност:** `dict` (Response.to_dict())
```python
{
    "status": "success" | "error",
    "data": {...},           # optional
    "message": "..."         # optional
}
```
---
### 4. ModbusConnectionTab (UI)
**Файл:** `src/plugins/core/modbus_settings_plugin/ui/ModbusConnectionTab.py`
**Описание:** UI компонент за конфигуриране на Modbus връзката.
**Секции:**
#### Connection Group
- **Serial Port** - Text input + "Detect Port" бутон
- **Baudrate** - Dropdown (9600, 19200, 38400, 57600, 115200, 230400)
- **Data Bits** - Dropdown (5, 6, 7, 8)
- **Stop Bits** - Dropdown (1, 1.5, 2)
- **Parity** - Dropdown (None, Even, Odd, Mark, Space)
#### Modbus Settings Group
- **Slave Address** - SpinBox (1-247)
- **Timeout** - DoubleSpinBox (0.001-10.0 seconds)
- **Max Retries** - SpinBox (1-100)
#### Connection Test Group
- **Test Connection** - Бутон за тестване
- **Status Label** - Показва резултат от теста
**Auto-Save:**
Всяка промяна автоматично се запазва чрез `_on_field_changed()`:
```python
self.baudrate_dropdown.currentTextChanged.connect(
    lambda: self._on_field_changed('baudrate', int(self.baudrate_dropdown.currentText()))
)
```
**Toast Notifications:**
```python
self.showToast("✅ Baudrate updated")
self.showToast("❌ Connection test failed")
```
---
### 5. ModbusController (Factory)
**Файл:** `src/modules/modbusCommunication/ModbusController.py`
**Описание:** Factory клас за създаване на конфигурирани Modbus клиенти.
**Публичен Метод:**
```python
@classmethod
def getModbusClient(cls, slaveId: int) -> ModbusClient:
    """
    Създава и конфигурира ModbusClient според запазената конфигурация.
    """
    config = get_config_from_settings()
    client = ModbusClient(slave=slaveId, port=config.port, max_retries=config.max_retries)
    client.client.serial.baudrate = config.baudrate
    client.client.serial.bytesize = config.byte_size
    client.client.serial.parity = config.parity.value
    # ... и други настройки
    return client
```
**Използване:**
```python
from modules.modbusCommunication import ModbusController
# Създаване на клиент за slave устройство с ID 10
client = ModbusController.getModbusClient(slaveId=10)
# Четене на holding register
value = client.read_holding_register(address=0)
```
**Вътрешни Функции:**
#### load_modbus_config_from_repo() → ModbusConfig
```python
modbus_repo = ModbusSettingsRepository(file_path=str(config_path))
config = modbus_repo.load()
return config
```
#### get_config_from_settings() → ModbusClientConfig
```python
settings = load_modbus_config_from_repo()
# Конвертиране към ModbusClientConfig
return ModbusClientConfig(
    slave_id=settings.slave_address,
    port=settings.port,
    baudrate=settings.baudrate,
    # ...
)
```
**Port Resolution (Linux):**
```python
port = settings.port
if port.startswith('COM'):
    # На Linux конвертира 'COM5' → '/dev/ttyUSB0'
    port = get_modbus_port(sudo_password=SUDO_PASS)
```
---
## Примери за Използване
### Пример 1: Зареждане и Показване на Конфигурация
```python
# В UI компонент
from communication_layer.api.v1.endpoints import modbus_endpoints
from communication_layer.api.v1.Response import Response
# Изпращане на заявка
controller = self.controller_service.get_controller()
response_dict = controller.requestSender.send_request(modbus_endpoints.MODBUS_CONFIG_GET)
response = Response.from_dict(response_dict)
if response.status == 'success':
    config = response.data
    print(f"Port: {config['port']}")
    print(f"Baudrate: {config['baudrate']}")
    print(f"Slave Address: {config['slave_address']}")
else:
    print(f"Error: {response.message}")
```
---
### Пример 2: Промяна на Baudrate
```python
# Изпращане на update заявка
request_data = {
    'field': 'baudrate',
    'value': 57600
}
response_dict = controller.requestSender.send_request(
    modbus_endpoints.MODBUS_CONFIG_UPDATE,
    data=request_data
)
response = Response.from_dict(response_dict)
if response.status == 'success':
    print("✅ Baudrate updated to 57600")
else:
    print(f"❌ Update failed: {response.message}")
```
---
### Пример 3: Откриване на Наличен Порт
```python
# Откриване на порт
response_dict = controller.requestSender.send_request(
    modbus_endpoints.MODBUS_GET_AVAILABLE_PORT
)
response = Response.from_dict(response_dict)
if response.status == 'success':
    detected_port = response.data['port']
    print(f"✅ Detected port: {detected_port}")
    # Автоматично актуализиране на конфигурацията
    update_data = {'field': 'port', 'value': detected_port}
    controller.requestSender.send_request(
        modbus_endpoints.MODBUS_CONFIG_UPDATE,
        data=update_data
    )
else:
    print(f"❌ No port detected: {response.message}")
```
---
### Пример 4: Тестване на Връзка
```python
# Тестване на връзката
response_dict = controller.requestSender.send_request(
    modbus_endpoints.MODBUS_TEST_CONNECTION
)
response = Response.from_dict(response_dict)
if response.status == 'success':
    print(f"✅ {response.message}")
    # "Successfully connected to Modbus slave at /dev/ttyUSB0"
else:
    print(f"❌ Connection failed: {response.message}")
```
---
### Пример 5: Директно Използване на Repository
```python
from pathlib import Path
from core.application.ApplicationStorageResolver import get_app_settings_path
from core.database.settings.ModbusSettingsRepository import ModbusSettingsRepository
from core.model.settings.modbusConfig.modbusConfigModel import ModbusConfig
# Създаване на repository
config_path = Path(get_app_settings_path("glue_dispensing_application", "modbus_config"))
repo = ModbusSettingsRepository(file_path=str(config_path))
# Зареждане
config = repo.load()
print(f"Current port: {config.port}")
# Промяна
config.port = "/dev/ttyUSB1"
config.baudrate = 57600
# Запазване
repo.save(config)
print("✅ Configuration saved")
# Или директна актуализация на поле
repo.update_field('slave_address', 15)
print("✅ Slave address updated to 15")
```
---
### Пример 6: Създаване на Modbus Клиент
```python
from modules.modbusCommunication import ModbusController
# Автоматично използва запазената конфигурация
client = ModbusController.getModbusClient(slaveId=10)
# Четене на holding register
try:
    value = client.read_holding_register(address=100)
    print(f"Register 100 value: {value}")
except Exception as e:
    print(f"Read failed: {e}")
# Писане на holding register
try:
    client.write_holding_register(address=200, value=1500)
    print("✅ Register 200 written successfully")
except Exception as e:
    print(f"Write failed: {e}")
```
---
## Конфигурационен Файл
**Локация:** `~/.cache/cobot-glue-dispensing-v5/glue_dispensing_application/storage/settings/modbus_config.json`
**Пълен път (resolва се динамично):**
```python
from core.application.ApplicationStorageResolver import get_app_settings_path
config_path = get_app_settings_path("glue_dispensing_application", "modbus_config")
# Резултат: ~/.cache/.../glue_dispensing_application/storage/settings/modbus_config.json
```
**Структура на JSON:**
```json
{
  "port": "COM5",
  "baudrate": 115200,
  "bytesize": 8,
  "stopbits": 1,
  "parity": "N",
  "timeout": 0.01,
  "slave_address": 10,
  "max_retries": 30
}
```
**Полета:**
| Поле | Тип | Валидни Стойности | Описание |
|------|-----|-------------------|----------|
| `port` | string | "COM5", "/dev/ttyUSB0" | Сериен порт |
| `baudrate` | int | 9600, 19200, 38400, 57600, 115200, 230400 | Скорост в bps |
| `bytesize` | int | 5, 6, 7, 8 | Брой data bits |
| `stopbits` | int | 1, 2 | Брой stop bits |
| `parity` | string | 'N', 'E', 'O', 'M', 'S' | Parity контрол |
| `timeout` | float | 0.001 - 10.0 | Timeout в секунди |
| `slave_address` | int | 1 - 247 | Modbus slave адрес |
| `max_retries` | int | 1 - 100 | Максимален брой повторения |
**Parity стойности:**
- `N` - None (без parity)
- `E` - Even (четен parity)
- `O` - Odd (нечетен parity)
- `M` - Mark (винаги 1)
- `S` - Space (винаги 0)
---
## Грешки и Обработка
### Типични Грешки
#### 1. Липсващ Конфигурационен Файл
**Симптом:** Файлът `modbus_config.json` не съществува
**Поведение:**
```
Settings file not found: ~/.cache/.../modbus_config.json. Created with defaults.
```
**Решение:** Автоматично се създава с default стойности
---
#### 2. Повреден JSON
**Симптом:** JSON файлът е невалиден
**Поведение:**
```
Failed to load modbus_config settings: Expecting property name enclosed in double quotes
```
**Решение:** Връща default конфигурация, файлът трябва да се поправи ръчно
---
#### 3. Липсващи Полета
**Симптом:** UPDATE заявка без `field` и `value`
**Response:**
```json
{
  "status": "error",
  "message": "Missing required fields: field and value"
}
```
**Решение:** Уверете се, че data съдържа `{'field': '...', 'value': ...}`
---
#### 4. Невалидно Поле
**Симптом:** Опит за актуализация на несъществуващо поле
**Грешка:**
```
ValueError: Invalid field: invalid_field_name
```
**Решение:** Проверете валидните имена на полета в ModbusConfig
---
#### 5. Connection Test Failed
**Симптом:** Modbus устройството не отговаря
**Response:**
```json
{
  "status": "error",
  "message": "Connection test failed: [Errno 2] No such file or directory: 'COM5'"
}
```
**Причини:**
- Устройството не е свързано
- Грешен порт
- Грешна конфигурация (baudrate, parity, и т.н.)
- Липса на права за достъп до порта
**Решение:**
1. Проверете физическата връзка
2. Използвайте "Detect Port" за откриване
3. Проверете правата за достъп: `sudo chmod 666 /dev/ttyUSB0`
---
#### 6. No Port Detected
**Симптом:** Системата не може да открие Modbus устройство
**Response:**
```json
{
  "status": "error",
  "message": "No Modbus port detected. Please ensure the device is connected."
}
```
**Решение:**
1. Свържете Modbus устройството
2. Проверете с `ls -l /dev/ttyUSB*`
3. Проверете dmesg за USB събития: `dmesg | tail`
---
## Разширения и Бъдещо Развитие
### Планирани Функционалности
1. **Device Registry**
   - Запазване на множество устройства с различни slave ID
   - Автоматично откриване на устройства на bus-а
   - Device templates с предварително дефинирани register карти
2. **Connection Pool**
   - Споделяне на връзка между множество клиенти
   - Автоматично reconnect при загуба на връзка
   - Connection health monitoring
3. **Logging & Monitoring**
   - История на комуникацията
   - Performance metrics (response time, error rate)
   - Real-time Modbus traffic visualization
4. **Advanced Testing**
   - Bulk register read/write тестове
   - Protocol analyzer
   - Connection stress testing
5. **Configuration Profiles**
   - Множество профили за различни setup-и
   - Import/Export на конфигурации
   - Configuration versioning
---
## Заключение
Modbus настройките имплементират пълен stack от UI до персистентно съхранение, следвайки best practices:
✅ **Repository Pattern** - Консистентно с останалите настройки  
✅ **Type Safety** - Dataclass модели с type hints  
✅ **Auto-Save** - Автоматично запазване при промяна  
✅ **Error Handling** - Graceful fallback при грешки  
✅ **User-Friendly UI** - Интуитивен интерфейс с toast нотификации  
✅ **Port Detection** - Автоматично откриване на устройства  
✅ **Connection Testing** - Валидация преди използване  
Системата е готова за production използване! 🎉
---
**Версия:** 1.0  
**Дата:** 10 Декември 2025  
**Автор:** Cobot Glue Dispensing System Team
