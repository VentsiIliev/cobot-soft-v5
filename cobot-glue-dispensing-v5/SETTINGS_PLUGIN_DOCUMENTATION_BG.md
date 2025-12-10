# Документация за Settings Plugin (Настройки)
## Съдържание
1. [Преглед](#преглед)
2. [Архитектура](#архитектура)
3. [Потока на Данните](#потока-на-данните)
4. [Файлова Структура](#файлова-структура)
5. [API Endpoints](#api-endpoints)
6. [Компоненти](#компоненти)
7. [Tabs (Раздели)](#tabs-раздели)
8. [Signal Pattern](#signal-pattern)
9. [Примери за Използване](#примери-за-използване)
---
## Преглед
Settings Plugin е централизирана система за управление на всички настройки в приложението. Системата имплементира унифициран интерфейс за конфигуриране на камера, робот, лепило и други компоненти.
### Основни Функционалности
- ✅ Управление на настройки за робот (Robot Settings)
- ✅ Управление на настройки за камера (Camera Settings)  
- ✅ Управление на настройки за лепило (Glue Settings)
- ✅ Табулиран интерфейс с икони
- ✅ Signal-based архитектура (вместо callbacks)
- ✅ Repository Pattern за персистентност
- ✅ Lazy loading на настройки (зареждат се при избор на tab)
- ✅ Jog Drawer за ръчно управление на робота
- ✅ Real-time валидация и обратна връзка
---
## Архитектура
Системата следва многослойна архитектура с Signal Pattern за комуникация:
```
┌─────────────────────────────────────────────────────────────────────┐
│                    Plugin Layer (Settings Plugin)                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ SettingsPlugin (IPlugin)                                      │  │
│  │  - metadata (name, version, permissions)                      │  │
│  │  - initialize(controller_service)                             │  │
│  │  - create_widget() → SettingsAppWidget                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    UI Layer (Frontend Widgets)                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ SettingsAppWidget (AppWidget)                                 │  │
│  │  └─ SettingsContent (CustomTabWidget)                         │  │
│  │      ├─ RobotConfigUI (Robot Settings Tab)                    │  │
│  │      │   ├─ General Settings Sub-tab                          │  │
│  │      │   ├─ Movement Groups Sub-tab                           │  │
│  │      │   ├─ Safety Sub-tab                                    │  │
│  │      │   └─ Robot Calibration Sub-tab                         │  │
│  │      ├─ CameraSettingsTabLayout (Camera Settings Tab)         │  │
│  │      └─ GlueSettingsTabLayout (Glue Settings Tab)             │  │
│  │          ├─ Glue Types Tab                                    │  │
│  │          ├─ Hardware Config Tab                               │  │
│  │          └─ Glue Cells Tab                                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Signal Flow:                                                        │
│  Widget Change → setting_changed(key, value, type) ──┐              │
│                                                        │              │
│  Widget Action → update_camera_feed_requested() ──────┼─→ Signals   │
│                                                        │              │
│  Widget Action → raw_mode_requested(bool) ────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                            ↓ (pyqtSignal)
┌─────────────────────────────────────────────────────────────────────┐
│              Communication Layer (API Gateway + Services)            │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ SettingsAppWidget._handle_setting_change()                    │  │
│  │  └─ controller_service.settings.update_setting()              │  │
│  │                                                                 │  │
│  │ MainRouter → SettingsDispatcher                               │  │
│  │  ├─ handle_robot_settings()                                   │  │
│  │  ├─ handle_camera_settings()                                  │  │
│  │  ├─ handle_glue_settings()                                    │  │
│  │  └─ handle_robot_calibration_settings()                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓ (Repository Pattern)
┌─────────────────────────────────────────────────────────────────────┐
│                  Data Access Layer (Repositories)                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ RobotSettingsRepository                                        │  │
│  │  └─ BaseJsonSettingsRepository[RobotConfig]                   │  │
│  │                                                                 │  │
│  │ CameraSettingsRepository                                       │  │
│  │  └─ BaseJsonSettingsRepository[CameraSettings]                │  │
│  │                                                                 │  │
│  │ RobotCalibrationRepository                                     │  │
│  │  └─ BaseJsonSettingsRepository[RobotCalibration]              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓ (JSON I/O)
┌─────────────────────────────────────────────────────────────────────┐
│                     Model Layer (Data Models)                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ RobotConfig                                                    │  │
│  │  - global_motion: GlobalMotionSettings                        │  │
│  │  - movement_groups: Dict[str, MovementGroup]                  │  │
│  │  - safety_limits: SafetyLimits                                │  │
│  │                                                                 │  │
│  │ CameraSettings                                                 │  │
│  │  - backend, resolution, fps, etc.                             │  │
│  │                                                                 │  │
│  │ RobotCalibrationSettings                                       │  │
│  │  - workspace_origin, camera_calibration, etc.                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    File System (Storage)                             │
│  ~/.cache/cobot-glue-dispensing-v5/                                 │
│    glue_dispensing_application/storage/settings/                    │
│      ├─ robot_config.json                                           │
│      ├─ camera_settings.json                                        │
│      └─ robot_calibration.json                                      │
└─────────────────────────────────────────────────────────────────────┘
```
---
## Потока на Данните
### 1. Инициализация на Plugin (Startup)
```
[1] Приложението стартира
      ↓
[2] PluginManager.load_plugins()
      ↓
[3] SettingsPlugin.initialize(controller_service)
      - Запазва controller_service референция
      - Маркира plugin като initialized
      ↓
[4] SettingsPlugin._is_initialized = True
      ↓
[5] Plugin е готов, но widget НЕ е създаден все още
```
### 2. Създаване на Widget (User Opens Settings)
```
[1] Потребителят кликва "Settings" в менюто
      ↓
[2] MainWindow → SettingsPlugin.create_widget()
      ↓
[3] Проверка: if not self._is_initialized → raise RuntimeError
      ↓
[4] Създава се SettingsAppWidget
      - controller_service се подава като параметър
      - widget се кешира в self._widget_instance
      ↓
[5] SettingsAppWidget.setup_ui()
      ↓
[6] Създава се SettingsContent с controller_service
      ↓
[7] SettingsContent._get_needed_settings_tabs()
      - Проверява какви tabs са нужни за приложението
      - Връща списък: ['robot', 'camera', 'glue']
      ↓
[8] SettingsContent._create_dynamic_tabs(needed_tabs)
      ├─ create_robot_settings_tab()
      ├─ create_camera_settings_tab()
      └─ create_glue_settings_tab()
      ↓
[9] За всеки tab:
      - Създава BackgroundTabPage
      - Създава съответния Layout (RobotConfigUI, CameraSettingsTabLayout, и т.н.)
      - Добавя tab с икона
      ↓
[10] SettingsContent._connect_settings_signals()
      - Свързва signal-и от всеки tab към unified handler
      ↓
[11] UI е готов - настройките все още НЕ са заредени (lazy loading)
```
**Пример код:**
```python
# В SettingsPlugin
def create_widget(self, parent=None):
    if not self._is_initialized:
        raise RuntimeError("Plugin not initialized")
    self._widget_instance = SettingsAppWidget(
        controller=self.controller_service.controller,
        controller_service=self.controller_service
    )
    return self._widget_instance
```
### 3. Зареждане на Настройки (Lazy Loading)
```
[1] Потребителят избира tab (напр. "Robot Settings")
      ↓
[2] Tab widget се показва за първи път
      ↓
[3] RobotConfigUI проверява: if not self._settings_loaded
      ↓
[4] RobotConfigUI._load_robot_settings()
      ↓
[5] controller_service.send_request(SETTINGS_ROBOT_GET)
      ↓
[6] MainRouter получава заявката
      ↓
[7] MainRouter → SettingsDispatcher.dispatch()
      ↓
[8] SettingsDispatcher.handle_robot_settings()
      ↓
[9] RobotSettingsRepository.load()
      ↓
[10] Чете robot_config.json от диска
      ↓
[11] RobotConfig.from_dict(json_data)
      ↓
[12] Response(status='success', data=robot_config.to_dict())
      ↓
[13] UI получава response и попълва полетата
      ↓
[14] self._settings_loaded = True (не се зарежда повторно)
```
**Пример код:**
```python
# В RobotConfigUI
def _load_robot_settings(self):
    if self._settings_loaded:
        return
    response_dict = self.controller_service.send_request(
        settings_endpoints.SETTINGS_ROBOT_GET
    )
    response = Response.from_dict(response_dict)
    if response.status == 'success':
        self._populate_ui_from_config(response.data)
        self._settings_loaded = True
```
### 4. Промяна на Настройка (Signal Pattern)
```
[1] Потребителят променя стойност (напр. max_velocity)
      ↓
[2] QSpinBox.valueChanged signal се задейства
      ↓
[3] Lambda функция улавя промяната
      ↓
[4] Емитира се unified signal:
      self.setting_changed.emit('max_velocity', 100.5, 'GlobalMotionSettings')
      ↓
[5] SettingsContent получава signal-а
      ↓
[6] SettingsContent пропагира signal-а нагоре
      ↓
[7] SettingsAppWidget._handle_setting_change(key, value, component_type)
      ↓
[8] controller_service.settings.update_setting(key, value, component_type)
      ↓
[9] SettingsService.update_setting()
      - Избира правилната strategy (robot_config_strategy)
      - strategy.update(key, value)
      ↓
[10] RobotConfigStrategy.update()
      - Зарежда текущия config
      - config.update_field(key, value)
      - Запазва обратно
      ↓
[11] RobotSettingsRepository.save(config)
      ↓
[12] JSON файлът се актуализира на диска
      ↓
[13] Връща Response със success/error
      ↓
[14] UI показва feedback (toast или log)
```
**Signal Flow Диаграма:**
```
Widget Input Change
      ↓
[valueChanged signal]
      ↓
Lambda: emit setting_changed(key, value, type)
      ↓
SettingsContent.setting_changed (relay)
      ↓
SettingsAppWidget._handle_setting_change()
      ↓
controller_service.settings.update_setting()
      ↓
Strategy Pattern → Repository → File I/O
      ↓
Response → Feedback
```
### 5. Специални Действия (Camera Feed, Raw Mode)
```
[1] Потребителят кликва бутон за Camera Feed Update
      ↓
[2] update_camera_feed_requested.emit()
      ↓
[3] SettingsContent пропагира signal-а
      ↓
[4] SettingsAppWidget.updateCameraFeedCallback()
      ↓
[5] controller.handle(camera_endpoints.UPDATE_CAMERA_FEED)
      ↓
[6] CameraController актуализира feed-а
      ↓
[7] Връща frame
      ↓
[8] UI показва актуализирания frame
```
**За Raw Mode:**
```
[1] CheckBox state change → raw_mode_requested.emit(state)
      ↓
[2] SettingsAppWidget.onRawModeRequested(state)
      ↓
[3] if state:
      controller.handle(CAMERA_ACTION_RAW_MODE_ON)
    else:
      controller.handle(CAMERA_ACTION_RAW_MODE_OFF)
      ↓
[4] CameraController превключва режима
```
### 6. Glue Types Management (Специфичен Поток)
```
[1] Потребителят отваря Glue Settings → Glue Types tab
      ↓
[2] GlueTypeTab.glue_types_load_requested.emit()
      ↓
[3] SettingsAppWidget._handle_load_glue_types()
      ↓
[4] controller.handle(GLUE_TYPES_GET)
      ↓
[5] SettingsDispatcher.handle_glue_types()
      ↓
[6] Чете glue_types.json или заявка към база данни
      ↓
[7] Response с масив от glue types
      ↓
[8] GlueTypeTab.update_glue_types_from_response(response)
      ↓
[9] Таблицата се попълва с данните
```
**Add Glue Type:**
```
[1] User clicks "Add"
      ↓
[2] glue_type_add_requested.emit(name, description)
      ↓
[3] SettingsAppWidget._handle_add_glue_type()
      ↓
[4] controller.handleAddGlueType(name, description)
      ↓
[5] GLUE_TYPE_ADD_CUSTOM endpoint
      ↓
[6] Добавя в storage
      ↓
[7] Response success/error
      ↓
[8] Reload all glue types
      ↓
[9] QMessageBox shows result
```
---
## Файлова Структура
### Plugin Layer
```
src/plugins/core/settings/
├── __init__.py
├── plugin.py                          # SettingsPlugin класа
├── plugin.json                        # Plugin metadata
│
├── icons/                             # Tab икони
│   ├── settings.png                   # Plugin icon
│   ├── CAMERA_SETTINGS_BUTTON.png
│   ├── ROBOT_SETTINGS_BUTTON_SQUARE.png
│   ├── glue_qty.png
│   └── Background_&_Logo.png
│
├── enums/                             # Setting keys енумерации
│   ├── CameraSettingKeys.py
│   ├── RobotCalibrationSettingKeys.py
│   └── GlueSettingKeys.py
│
├── ui/                                # UI компоненти
│   ├── __init__.py
│   ├── SettingsAppWidget.py           # Главен widget
│   ├── SettingsContent.py             # Tab контейнер
│   ├── BaseSettingsTabLayout.py       # Базов клас за tabs
│   ├── CameraSettingsTabLayout.py     # Camera tab
│   ├── GlueCellSettingsTabLayout.py   # Glue cells tab
│   │
│   ├── robot_settings_tab/            # Robot settings sub-module
│   │   ├── __init__.py
│   │   ├── RobotConfigUI.py           # Главен robot tab
│   │   ├── signals.py                 # Signal дефиниции
│   │   ├── translate.py               # Преводи
│   │   │
│   │   ├── sub_tabs/                  # Robot sub-tabs
│   │   │   ├── general_settings.py
│   │   │   ├── movement_groups.py
│   │   │   ├── safety.py
│   │   │   └── robot_calibration.py
│   │   │
│   │   └── robot_config_groups/       # UI групи
│   │       ├── base.py
│   │       ├── global_motion.py
│   │       ├── movement_group.py
│   │       ├── robot_info.py
│   │       └── safety_limits.py
│   │
│   └── helpers/                       # Helper widgets
│       ├── commands.py
│       └── jog_widget.py              # Jog drawer
│
└── services/                          # (празна, за бъдеща употреба)
```
### Communication Layer
```
src/communication_layer/
├── api/v1/endpoints/
│   └── settings_endpoints.py          # Settings endpoint дефиниции
│
└── api_gateway/dispatch/
    └── settings_dispatcher.py         # Settings заявки handler
```
### Data Access Layer
```
src/core/database/settings/
├── BaseJsonSettingsRepository.py      # Базов repository клас
├── RobotSettingsRepository.py         # Robot config repository
├── CameraSettingsRepository.py        # Camera settings repository
└── RobotCalibrationRepository.py      # Robot calibration repository
```
### Model Layer
```
src/core/model/settings/
├── BaseSettings.py                    # Базов settings модел
├── CameraSettings.py                  # Camera settings model
├── robot_calibration_settings.py      # Calibration model
│
├── robotConfig/                       # Robot config models
│   ├── __init__.py
│   ├── robotConfigModel.py            # RobotConfig главен клас
│   ├── GlobalMotionSettings.py        # Global motion настройки
│   ├── MovementGroup.py               # Movement group модел
│   ├── SafetyLimits.py                # Safety limits модел
│   └── OffsetDirectionMap.py          # Offset направления
│
└── enums/
    └── CameraSettingKey.py            # Camera setting ключове
```
### Services Layer
```
src/core/services/settings/
├── SettingsService.py                 # Main settings service
├── interfaces/
│   └── ISettingsRepository.py         # Repository interface
│
└── strategies/                        # Strategy pattern за различни типове
    ├── base_strategy.py
    ├── robot_config_strategy.py
    └── robot_calibration_strategy.py
```
### Storage
```
~/.cache/cobot-glue-dispensing-v5/
└── glue_dispensing_application/storage/settings/
    ├── robot_config.json
    ├── camera_settings.json
    └── robot_calibration.json
```
---
## API Endpoints
### 1. SETTINGS_ROBOT_GET
**Път:** `/api/v1/settings/robot`  
**Метод:** GET  
**Цел:** Зареждане на пълната robot конфигурация
**Request:**
```python
controller_service.send_request(settings_endpoints.SETTINGS_ROBOT_GET)
```
**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "global_motion": {
      "max_velocity": 100.5,
      "max_acceleration": 50.0,
      "max_jerk": 200.0,
      "blend_radius": 0.01
    },
    "movement_groups": {
      "approach": {
        "velocity": 80.0,
        "acceleration": 40.0
      }
    },
    "safety_limits": {
      "max_tcp_speed": 250.0,
      "max_joint_speed": [180.0, 180.0, 180.0, 360.0, 360.0, 360.0]
    }
  }
}
```
**Handler:** `SettingsDispatcher.handle_robot_settings()`
```python
if request == settings_endpoints.SETTINGS_ROBOT_GET:
    repo = RobotSettingsRepository(file_path=robot_config_path)
    config = repo.load()
    return Response(
        Constants.RESPONSE_STATUS_SUCCESS,
        data=config.to_dict()
    ).to_dict()
```
---
### 2. SETTINGS_ROBOT_SET
**Път:** `/api/v1/settings/robot/set`  
**Метод:** POST  
**Цел:** Запазване на цяла robot конфигурация
**Request:**
```python
controller_service.send_request(
    settings_endpoints.SETTINGS_ROBOT_SET,
    data={
        'global_motion': {...},
        'movement_groups': {...},
        'safety_limits': {...}
    }
)
```
**Response (Success):**
```json
{
  "status": "success",
  "message": "Robot configuration saved successfully"
}
```
---
### 3. SETTINGS_ROBOT_CALIBRATION_GET
**Път:** `/api/v1/settings/robot/calibration`  
**Метод:** GET  
**Цел:** Зареждане на robot calibration данни
**Request:**
```python
controller_service.send_request(settings_endpoints.SETTINGS_ROBOT_CALIBRATION_GET)
```
**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "workspace_origin": {"x": 0.0, "y": 0.0, "z": 0.0},
    "camera_calibration": {
      "pixel_to_mm_x": 0.1,
      "pixel_to_mm_y": 0.1
    },
    "tcp_offset": {"x": 0.0, "y": 0.0, "z": 150.0}
  }
}
```
---
### 4. SETTINGS_ROBOT_CALIBRATION_SET
**Път:** `/api/v1/settings/robot/calibration/set`  
**Метод:** POST  
**Цел:** Запазване на robot calibration
**Request:**
```python
controller_service.send_request(
    settings_endpoints.SETTINGS_ROBOT_CALIBRATION_SET,
    data={
        'workspace_origin': {'x': 10.0, 'y': 20.0, 'z': 0.0}
    }
)
```
---
### 5. SETTINGS_CAMERA_GET
**Път:** `/api/v1/settings/camera`  
**Метод:** GET  
**Цел:** Зареждане на camera настройки
**Request:**
```python
controller_service.send_request(settings_endpoints.SETTINGS_CAMERA_GET)
```
**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "backend": "OPENCV",
    "camera_index": 0,
    "resolution": [1920, 1080],
    "fps": 30,
    "auto_exposure": false,
    "exposure": 100,
    "gain": 50
  }
}
```
---
### 6. SETTINGS_CAMERA_SET
**Път:** `/api/v1/settings/camera/set`  
**Метод:** POST  
**Цел:** Запазване на camera настройки
**Request:**
```python
controller_service.send_request(
    settings_endpoints.SETTINGS_CAMERA_SET,
    data={
        'backend': 'V4L2',
        'resolution': [1280, 720],
        'fps': 60
    }
)
```
---
### 7. SETTINGS_GET
**Път:** `/api/v1/settings`  
**Метод:** GET  
**Цел:** Generic settings заявка
**Request:**
```python
controller_service.send_request(
    settings_endpoints.SETTINGS_GET,
    data={'type': 'some_setting_type'}
)
```
---
### 8. SETTINGS_UPDATE
**Път:** `/api/v1/settings`  
**Метод:** POST  
**Цел:** Generic settings актуализация
**Request:**
```python
controller_service.send_request(
    settings_endpoints.SETTINGS_UPDATE,
    data={
        'type': 'some_type',
        'key': 'some_key',
        'value': 'some_value'
    }
)
```
---
## Компоненти
### 1. SettingsPlugin (Plugin Entry Point)
**Файл:** `plugins/core/settings/plugin.py`
**Описание:** Главната входна точка за Settings plugin. Имплементира IPlugin интерфейса.
**Metadata:**
```python
PluginMetadata(
    name="Settings",
    version="1.0.0",
    author="PL Team",
    description="System settings management",
    category=PluginCategory.CORE,
    permissions=[
        PluginPermission.SETTINGS_READ,
        PluginPermission.SETTINGS_WRITE
    ],
    auto_load=True
)
```
**Методи:**
#### initialize(controller_service) → bool
```python
def initialize(self, controller_service):
    self.controller_service = controller_service
    self._mark_initialized(True)
    return True
```
#### create_widget(parent) → QWidget
```python
def create_widget(self, parent=None):
    if not self._is_initialized:
        raise RuntimeError("Plugin not initialized")
    self._widget_instance = SettingsAppWidget(
        controller=self.controller_service.controller,
        controller_service=self.controller_service
    )
    return self._widget_instance
```
---
### 2. SettingsAppWidget (Main Widget)
**Файл:** `plugins/core/settings/ui/SettingsAppWidget.py`
**Описание:** Главният UI widget, наследява AppWidget.
**Signal Handling:**
```python
# Unified settings change
self.content_widget.setting_changed.connect(self._handle_setting_change)
# Action signals
self.content_widget.update_camera_feed_requested.connect(updateCameraFeedCallback)
self.content_widget.raw_mode_requested.connect(onRawModeRequested)
```
**Метод за обработка на промени:**
```python
def _handle_setting_change(self, key, value, component_type):
    print(f"🔧 Setting change: {component_type}.{key} = {value}")
    result = self.controller_service.settings.update_setting(
        key, value, component_type
    )
    if result:
        print(f"✅ {result.message}")
    else:
        print(f"❌ {result.message}")
```
---
### 3. SettingsContent (Tab Container)
**Файл:** `plugins/core/settings/ui/SettingsContent.py`
**Описание:** CustomTabWidget, съдържа всички settings tabs.
**Signals:**
```python
# Action signals
update_camera_feed_requested = pyqtSignal()
raw_mode_requested = pyqtSignal(bool)
# Settings change signal
setting_changed = pyqtSignal(str, object, str)  # key, value, component_type
```
**Dynamic Tab Creation:**
```python
def _get_needed_settings_tabs(self):
    """Determine which tabs are needed for current application"""
    needed_tabs = []
    # Check application context
    if hasattr(self, 'controller_service'):
        app_name = getattr(self.controller_service, 'app_name', None)
        if app_name == 'glue_dispensing_application':
            needed_tabs = ['robot', 'camera', 'glue']
        else:
            needed_tabs = ['robot', 'camera']
    return needed_tabs
def _create_dynamic_tabs(self, needed_tabs):
    """Create only the tabs needed for this application"""
    if 'robot' in needed_tabs:
        self.create_robot_settings_tab()
    if 'camera' in needed_tabs:
        self.create_camera_settings_tab()
    if 'glue' in needed_tabs:
        self.create_glue_settings_tab()
```
**Signal Connection:**
```python
def _connect_settings_signals(self):
    """Connect all tab signals to unified handler"""
    # Robot settings
    if self.robotSettingsTabLayout:
        self.robotSettingsTabLayout.setting_changed.connect(
            self.setting_changed.emit
        )
    # Camera settings
    if self.cameraSettingsTabLayout:
        self.cameraSettingsTabLayout.setting_changed.connect(
            self.setting_changed.emit
        )
    # Glue settings
    if self.glueSettingsTabLayout:
        self.glueSettingsTabLayout.setting_changed.connect(
            self.setting_changed.emit
        )
```
---
### 4. RobotConfigUI (Robot Settings Tab)
**Файл:** `plugins/core/settings/ui/robot_settings_tab/RobotConfigUI.py`
**Описание:** Главният tab за robot настройки, съдържа 4 sub-tabs.
**Sub-tabs:**
1. **General Settings** - Global motion параметри
2. **Movement Groups** - Различни групи движения
3. **Safety** - Safety limits
4. **Robot Calibration** - Calibration данни
**Signals:**
```python
# От robot_settings_tab/signals.py
setting_changed = pyqtSignal(str, object, str)  # key, value, component_type
```
**Lazy Loading:**
```python
def showEvent(self, event):
    """Load settings when tab is shown for first time"""
    super().showEvent(event)
    if not self._settings_loaded:
        self._load_robot_settings()
def _load_robot_settings(self):
    """Load robot settings via endpoint"""
    response_dict = self.controller_service.send_request(
        settings_endpoints.SETTINGS_ROBOT_GET
    )
    response = Response.from_dict(response_dict)
    if response.status == 'success':
        self._populate_ui_from_config(response.data)
        self._settings_loaded = True
```
**Signal Emission:**
```python
# В GlobalMotionSettings group
self.max_velocity_spinbox.valueChanged.connect(
    lambda v: self.setting_changed.emit(
        'max_velocity', v, 'GlobalMotionSettings'
    )
)
```
---
### 5. CameraSettingsTabLayout (Camera Settings Tab)
**Файл:** `plugins/core/settings/ui/CameraSettingsTabLayout.py`
**Описание:** Tab за camera настройки.
**Секции:**
- Camera Backend (OPENCV, V4L2, GSTREAMER)
- Resolution
- FPS
- Exposure settings
- Gain settings
- White balance
- Raw mode toggle
**Signal Emission:**
```python
self.backend_dropdown.currentTextChanged.connect(
    lambda v: self.setting_changed.emit('backend', v, 'CameraSettings')
)
self.raw_mode_checkbox.stateChanged.connect(
    lambda state: self.raw_mode_requested.emit(state == Qt.CheckState.Checked)
)
```
---
### 6. GlueSettingsTabLayout (Glue Settings Tab)
**Файл:** `plugins/core/glue_settings_plugin/ui/GlueSettingsTabLayout.py`
**Описание:** Tab за glue настройки (може да е в отделен plugin).
**Sub-tabs:**
1. **Glue Types** - Управление на типове лепило
2. **Hardware Config** - Hardware конфигурация
3. **Glue Cells** - Glue cells настройки
**Signals:**
```python
# От Glue Types tab
glue_types_load_requested = pyqtSignal()
glue_type_add_requested = pyqtSignal(str, str)  # name, description
glue_type_update_requested = pyqtSignal(str, str, str)  # id, name, description
glue_type_remove_requested = pyqtSignal(str)  # id
```
---
## Tabs (Раздели)
### Robot Settings Tab
**Структура:**
```
RobotConfigUI (QWidget)
├── Sub-tab: General Settings
│   └── GlobalMotionSettings group
│       ├── Max Velocity (QDoubleSpinBox)
│       ├── Max Acceleration (QDoubleSpinBox)
│       ├── Max Jerk (QDoubleSpinBox)
│       └── Blend Radius (QDoubleSpinBox)
│
├── Sub-tab: Movement Groups
│   └── За всяка група:
│       ├── Velocity (QDoubleSpinBox)
│       ├── Acceleration (QDoubleSpinBox)
│       └── Jerk (QDoubleSpinBox)
│
├── Sub-tab: Safety
│   └── SafetyLimits group
│       ├── Max TCP Speed (QDoubleSpinBox)
│       └── Max Joint Speeds (6x QDoubleSpinBox)
│
└── Sub-tab: Robot Calibration
    ├── Workspace Origin (X, Y, Z)
    ├── Camera Calibration
    └── TCP Offset
```
**Пример UI код:**
```python
# В GlobalMotionSettings group
self.max_velocity_spinbox = QDoubleSpinBox()
self.max_velocity_spinbox.setRange(0.0, 1000.0)
self.max_velocity_spinbox.setValue(config.max_velocity)
self.max_velocity_spinbox.valueChanged.connect(
    lambda v: self.setting_changed.emit('max_velocity', v, 'GlobalMotionSettings')
)
```
---
### Camera Settings Tab
**Структура:**
```
CameraSettingsTabLayout (QVBoxLayout)
├── Backend Selection Group
│   └── Dropdown: OPENCV, V4L2, GSTREAMER
│
├── Resolution Group
│   ├── Width (QSpinBox)
│   └── Height (QSpinBox)
│
├── FPS Group
│   └── FPS (QSpinBox)
│
├── Exposure Group
│   ├── Auto Exposure (QCheckBox)
│   └── Manual Exposure (QSlider)
│
├── Gain Group
│   └── Gain (QSlider)
│
├── White Balance Group
│   ├── Auto WB (QCheckBox)
│   └── Manual WB (QSlider)
│
└── Actions Group
    ├── Update Camera Feed (QPushButton)
    └── Raw Mode (QCheckBox)
```
**Пример UI код:**
```python
# Backend dropdown
self.backend_dropdown = QComboBox()
self.backend_dropdown.addItems(['OPENCV', 'V4L2', 'GSTREAMER'])
self.backend_dropdown.currentTextChanged.connect(
    lambda v: self.setting_changed.emit('backend', v, 'CameraSettings')
)
# Raw mode
self.raw_mode_checkbox = QCheckBox("Raw Mode")
self.raw_mode_checkbox.stateChanged.connect(
    lambda state: self.raw_mode_requested.emit(state == Qt.CheckState.Checked)
)
```
---
### Glue Settings Tab
**Структура:**
```
GlueSettingsTabLayout (CustomTabWidget)
├── Sub-tab: Glue Types
│   ├── Table: ID, Name, Description, Actions
│   └── Buttons: Add, Edit, Delete
│
├── Sub-tab: Hardware Config
│   ├── Motor Addresses
│   └── Cell Configurations
│
└── Sub-tab: Glue Cells
    └── Cell-specific настройки
```
---
## Signal Pattern
Settings Plugin използва **Signal-based Architecture** вместо callback pattern.
### Старият Начин (Callbacks) ❌
```python
# СТАРО - НЕ СЕ ИЗПОЛЗВА ПОВЕЧЕ
def onMaxVelocityChanged(value):
    controller.updateRobotSetting('max_velocity', value)
spinbox.valueChanged.connect(onMaxVelocityChanged)
```
**Проблеми:**
- Tight coupling между UI и controller
- Трудно тестване
- Няма унифицирана обработка
- Code duplication
### Новият Начин (Signals) ✅
```python
# НОВО - Signal-based
# 1. Widget emits unified signal
spinbox.valueChanged.connect(
    lambda v: self.setting_changed.emit('max_velocity', v, 'GlobalMotionSettings')
)
# 2. Tab relays signal upward
tab.setting_changed.connect(self.setting_changed.emit)
# 3. AppWidget handles all settings uniformly
def _handle_setting_change(self, key, value, component_type):
    result = controller_service.settings.update_setting(key, value, component_type)
```
**Предимства:**
- Loose coupling
- Лесно тестване
- Унифицирана обработка
- DRY принцип
### Signal Flow Example
```
┌────────────────────────────────────┐
│ QSpinBox (max_velocity)            │
│  valueChanged(100.5)               │
└────────────┬───────────────────────┘
             │
             ↓ lambda emits
┌────────────────────────────────────┐
│ GlobalMotionSettings                │
│  setting_changed.emit(              │
│    'max_velocity', 100.5,           │
│    'GlobalMotionSettings'           │
│  )                                  │
└────────────┬───────────────────────┘
             │
             ↓ relay
┌────────────────────────────────────┐
│ RobotConfigUI                       │
│  setting_changed.emit(...)          │
└────────────┬───────────────────────┘
             │
             ↓ relay
┌────────────────────────────────────┐
│ SettingsContent                     │
│  setting_changed.emit(...)          │
└────────────┬───────────────────────┘
             │
             ↓ connect
┌────────────────────────────────────┐
│ SettingsAppWidget                   │
│  _handle_setting_change(            │
│    key='max_velocity',              │
│    value=100.5,                     │
│    component_type='GlobalMotion'    │
│  )                                  │
│    ↓                                │
│  controller_service.settings        │
│    .update_setting(...)             │
└─────────────────────────────────────┘
```
---
## Примери за Използване
### Пример 1: Зареждане на Robot Settings
```python
# В RobotConfigUI
def _load_robot_settings(self):
    """Load robot settings when tab is first shown"""
    from communication_layer.api.v1.endpoints import settings_endpoints
    from communication_layer.api.v1.Response import Response
    # Send request via controller_service
    response_dict = self.controller_service.send_request(
        settings_endpoints.SETTINGS_ROBOT_GET
    )
    # Parse response
    response = Response.from_dict(response_dict)
    if response.status == 'success':
        config_data = response.data
        # Populate UI fields
        self.global_motion_group.set_values(
            config_data['global_motion']
        )
        self.movement_groups_tab.set_values(
            config_data['movement_groups']
        )
        self._settings_loaded = True
        print("✅ Robot settings loaded successfully")
    else:
        print(f"❌ Failed to load settings: {response.message}")
```
---
### Пример 2: Промяна на Max Velocity
```python
# В GlobalMotionSettings UI group
class GlobalMotionSettings(QGroupBox):
    setting_changed = pyqtSignal(str, object, str)
    def __init__(self):
        super().__init__("Global Motion")
        # Create spinbox
        self.max_velocity_spinbox = QDoubleSpinBox()
        self.max_velocity_spinbox.setRange(0.0, 1000.0)
        self.max_velocity_spinbox.setSuffix(" mm/s")
        self.max_velocity_spinbox.setValue(100.5)
        # Connect to signal
        self.max_velocity_spinbox.valueChanged.connect(
            self._on_max_velocity_changed
        )
    def _on_max_velocity_changed(self, value):
        """Emit unified signal when value changes"""
        self.setting_changed.emit(
            'max_velocity',           # key
            value,                    # value
            'GlobalMotionSettings'    # component_type
        )
        print(f"Max Velocity changed to: {value}")
# В RobotConfigUI - relay signal
self.global_motion_group.setting_changed.connect(
    self.setting_changed.emit
)
# В SettingsContent - relay signal
self.robotSettingsTabLayout.setting_changed.connect(
    self.setting_changed.emit
)
# В SettingsAppWidget - handle change
def _handle_setting_change(self, key, value, component_type):
    print(f"🔧 {component_type}.{key} = {value}")
    result = self.controller_service.settings.update_setting(
        key, value, component_type
    )
    if result.status == 'success':
        print(f"✅ Saved successfully")
    else:
        print(f"❌ Save failed: {result.message}")
```
---
### Пример 3: Camera Feed Update
```python
# В CameraSettingsTabLayout
class CameraSettingsTabLayout(BaseSettingsTabLayout):
    update_camera_feed_requested = pyqtSignal()
    def __init__(self):
        super().__init__()
        # Create button
        self.update_feed_btn = QPushButton("Update Camera Feed")
        self.update_feed_btn.clicked.connect(
            self._on_update_feed_clicked
        )
    def _on_update_feed_clicked(self):
        """Request camera feed update"""
        print("Requesting camera feed update...")
        self.update_camera_feed_requested.emit()
# В SettingsContent - relay signal
self.cameraSettingsTabLayout.update_camera_feed_requested.connect(
    self.update_camera_feed_requested.emit
)
# В SettingsAppWidget - handle action
def updateCameraFeedCallback(self):
    """Handle camera feed update request"""
    from communication_layer.api.v1.endpoints import camera_endpoints
    frame = self.controller.handle(
        camera_endpoints.UPDATE_CAMERA_FEED
    )
    # Update UI with new frame
    self.content_widget.updateCameraFeed(frame)
    print("✅ Camera feed updated")
```
---
### Пример 4: Add Glue Type
```python
# В GlueTypeTab
class GlueTypeTab(QWidget):
    glue_type_add_requested = pyqtSignal(str, str)  # name, description
    def _on_add_button_clicked(self):
        """Show dialog and emit add request"""
        dialog = AddGlueTypeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name_input.text()
            description = dialog.description_input.toPlainText()
            # Emit signal
            self.glue_type_add_requested.emit(name, description)
# В SettingsAppWidget - handle add
def _setup_glue_types_signals(self):
    """Connect glue type signals"""
    tab = self.content_widget.glueSettingsTabLayout.glue_type_tab
    # Connect add signal
    tab.glue_type_add_requested.connect(
        self._handle_add_glue_type
    )
def _handle_add_glue_type(self, name, description):
    """Add glue type via controller"""
    from communication_layer.api.v1.Response import Response
    from PyQt6.QtWidgets import QMessageBox
    # Call controller
    response_dict = self.controller.handleAddGlueType(name, description)
    response = Response.from_dict(response_dict)
    if response.status == "success":
        # Reload all glue types
        self._handle_load_glue_types()
        QMessageBox.information(
            self, 
            "Success", 
            f"Glue type '{name}' added successfully"
        )
    else:
        QMessageBox.warning(
            self,
            "Error",
            response.message
        )
```
---
### Пример 5: Jog Drawer (Robot Manual Control)
```python
# В SettingsContent
def _setup_jog_drawer(self):
    """Setup jog drawer for manual robot control"""
    # Create drawer
    self.jog_drawer = Drawer(parent=self, position="right")
    # Create jog widget
    jog_widget = RobotJogWidget(controller_service=self.controller_service)
    # Add to drawer
    self.jog_drawer.setWidget(jog_widget)
    # Create toggle button
    jog_toggle_btn = QPushButton("Manual Control")
    jog_toggle_btn.clicked.connect(self.jog_drawer.toggle)
    # Add button to robot settings tab
    if self.robotSettingsTabLayout:
        self.robotSettingsTabLayout.addWidget(jog_toggle_btn)
# Използване в RobotJogWidget
class RobotJogWidget(QWidget):
    def __init__(self, controller_service):
        super().__init__()
        self.controller_service = controller_service
        # Create jog buttons
        self.setup_jog_buttons()
    def jog_positive_x(self):
        """Jog robot in positive X direction"""
        from communication_layer.api.v1.endpoints import robot_endpoints
        response = self.controller_service.send_request(
            robot_endpoints.ROBOT_JOG,
            data={'axis': 'x', 'direction': 'positive', 'distance': 10.0}
        )
        if response['status'] == 'success':
            print("✅ Jogged +X 10mm")
```
---
### Пример 6: Lazy Loading Pattern
```python
# В всеки settings tab
class SomeSettingsTab(QWidget):
    def __init__(self, controller_service):
        super().__init__()
        self.controller_service = controller_service
        self._settings_loaded = False
        # Setup UI but don't load settings yet
        self.setup_ui()
    def showEvent(self, event):
        """Qt event when widget becomes visible"""
        super().showEvent(event)
        # Load settings only on first show
        if not self._settings_loaded:
            self._load_settings()
    def _load_settings(self):
        """Load settings from backend"""
        print("Loading settings (first time)...")
        response_dict = self.controller_service.send_request(
            settings_endpoints.SOME_SETTINGS_GET
        )
        response = Response.from_dict(response_dict)
        if response.status == 'success':
            self._populate_ui(response.data)
            self._settings_loaded = True
        print(f"Settings loaded: {self._settings_loaded}")
```
**Предимства на Lazy Loading:**
- Приложението стартира по-бързо
- Settings се зареждат само ако потребителят ги отвори
- По-малко initial network/disk I/O
- По-добър user experience
---
## Заключение
Settings Plugin имплементира пълноценна система за управление на настройки с:
✅ **Модулна Архитектура** - Ясно разделение на слоеве  
✅ **Signal Pattern** - Loose coupling, лесно тестване  
✅ **Repository Pattern** - Консистентно data access  
✅ **Lazy Loading** - По-бързо стартиране на приложението  
✅ **Dynamic Tabs** - Различни tabs за различни приложения  
✅ **Unified Interface** - Еднакъв начин за обработка на всички настройки  
✅ **Type Safety** - Dataclass модели с type hints  
✅ **Extensible** - Лесно добавяне на нови settings tabs  
Системата е готова за production използване и следва best practices! 🎉
---
**Версия:** 1.0  
**Дата:** 10 Декември 2025  
**Автор:** Cobot Glue Dispensing System Team
