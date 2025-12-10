# Документация за Glue Cell Settings Plugin
## Съдържание
1. [Преглед](#преглед)
2. [Архитектура](#архитектура)
3. [Потока на Данните](#потока-на-данните)
4. [Файлова Структура](#файлова-структура)
5. [API Endpoints](#api-endpoints)
6. [Компоненти](#компоненти)
7. [Message Broker Integration](#message-broker-integration)
8. [Real-time Weight Monitoring](#real-time-weight-monitoring)
9. [Примери за Използване](#примери-за-използване)
---
## Преглед
Glue Cell Settings Plugin е специализирана система за управление и конфигурация на тензометрични датчици (load cells) за измерване на теглото на лепилото. Системата поддържа до 3 независими датчика с real-time мониторинг, калибрация и автоматично запазване на настройки.
### Основни Функционалности
- ✅ Управление на до 3 load cells (тензометрични датчици)
- ✅ Real-time мониторинг на тегло чрез Message Broker
- ✅ Калибрация и tare на всеки датчик
- ✅ Конфигурация на motor addresses и offsets
- ✅ Избор на glue type за всеки cell
- ✅ Test/Production режими
- ✅ Автоматично запазване на промени
- ✅ WebSocket интеграция с glue monitor system
- ✅ Responsive UI с scroll support
### Хардуерна Интеграция
Системата работи с:
- **Load Cells (HX711)** - Тензометрични датчици за тегло
- **Motor Controllers** - Modbus адреси за помпи
- **Glue Monitor Server** - WebSocket сървър за real-time данни
---
## Архитектура
Системата следва многослойна архитектура с real-time communication:
```
┌─────────────────────────────────────────────────────────────────────┐
│                    Plugin Layer (Glue Cell Settings)                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ GlueCellSettingsPlugin (IPlugin)                              │  │
│  │  - metadata (name, version, permissions)                      │  │
│  │  - initialize(controller_service)                             │  │
│  │  - create_widget() → GlueCellSettingsAppWidget                │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    UI Layer (Frontend Widgets)                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ GlueCellSettingsAppWidget (AppWidget)                         │  │
│  │  └─ GlueCellSettingsTabLayout (QVBoxLayout)                   │  │
│  │      ├─ Cell Selection Group                                  │  │
│  │      │   └─ Dropdown: Cell 1, 2, 3                            │  │
│  │      │                                                         │  │
│  │      ├─ Settings Groups (3 колони)                            │  │
│  │      │   ├─ Connection & Hardware                             │  │
│  │      │   │   ├─ Mode Toggle (Test/Production)                 │  │
│  │      │   │   ├─ Glue Type Dropdown                            │  │
│  │      │   │   └─ Motor Address Input                           │  │
│  │      │   │                                                     │  │
│  │      │   ├─ Calibration Settings                              │  │
│  │      │   │   ├─ Scale Factor                                  │  │
│  │      │   │   ├─ Offset                                        │  │
│  │      │   │   └─ Expected Weight                               │  │
│  │      │   │                                                     │  │
│  │      │   └─ Measurement Settings                              │  │
│  │      │       ├─ Sampling Rate                                 │  │
│  │      │       ├─ Filter Type                                   │  │
│  │      │       └─ Averaging Samples                             │  │
│  │      │                                                         │  │
│  │      ├─ Real-time Monitoring Group                            │  │
│  │      │   └─ Current Weight Display (kg)                       │  │
│  │      │                                                         │  │
│  │      └─ Control Buttons Group                                 │  │
│  │          ├─ Tare Button                                       │  │
│  │          ├─ Calibrate Button                                  │  │
│  │          └─ Save Configuration Button                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Signal: value_changed_signal(key, value, className)                │
└─────────────────────────────────────────────────────────────────────┘
                            ↓ (pyqtSignal)
┌─────────────────────────────────────────────────────────────────────┐
│              Communication Layer (Multi-protocol)                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ [1] Settings API (REST)                                       │  │
│  │     controller_service → SettingsDispatcher                   │  │
│  │     ├─ GLUE_CELLS_CONFIG_GET                                  │  │
│  │     ├─ GLUE_CELLS_CONFIG_SET                                  │  │
│  │     ├─ GLUE_CELL_UPDATE                                       │  │
│  │     ├─ GLUE_CELL_CALIBRATE                                    │  │
│  │     ├─ GLUE_CELL_TARE                                         │  │
│  │     └─ GLUE_CELL_UPDATE_TYPE                                  │  │
│  │                                                                 │  │
│  │ [2] Glue Monitor API (HTTP + WebSocket)                       │  │
│  │     GlueDataFetcher (Background Thread)                       │  │
│  │     ├─ UPDATE_SCALE_ENDPOINT                                  │  │
│  │     ├─ TARE_ENDPOINT                                          │  │
│  │     └─ UPDATE_OFFSET_ENDPOINT                                 │  │
│  │                                                                 │  │
│  │ [3] Message Broker (Pub/Sub)                                  │  │
│  │     MessageBroker.subscribe()                                 │  │
│  │     ├─ GlueTopics.GLUE_METER_1_VALUE                          │  │
│  │     ├─ GlueTopics.GLUE_METER_2_VALUE                          │  │
│  │     └─ GlueTopics.GLUE_METER_3_VALUE                          │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  Business Logic Layer (Services)                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ GlueCellsManagerSingleton                                      │  │
│  │  - Singleton pattern за управление на cells                   │  │
│  │  - getCellById(cell_id) → GlueCell                            │  │
│  │  - update_cell_config(cell_id, config)                        │  │
│  │                                                                 │  │
│  │ GlueDataFetcher (Thread)                                       │  │
│  │  - Фонов thread за fetch на данни                             │  │
│  │  - Publish към MessageBroker                                  │  │
│  │  - Работи с WebSocket connection                              │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Storage Layer (File + Server)                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Local JSON Config                                              │  │
│  │  ~/.cache/cobot-glue-dispensing-v5/                           │  │
│  │    glue_dispensing_application/                               │  │
│  │      core_settings/glue_cell_config.json                      │  │
│  │                                                                 │  │
│  │ Glue Monitor Server (External)                                 │  │
│  │  - WebSocket real-time data stream                            │  │
│  │  - HTTP REST API за commands                                  │  │
│  │  - HX711 hardware integration                                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```
---
## Потока на Данните
### 1. Инициализация на Plugin
```
[1] Приложението стартира
      ↓
[2] PluginManager.load_plugins()
      ↓
[3] GlueCellSettingsPlugin.initialize(controller_service)
      - Запазва controller_service
      - Маркира като initialized
      ↓
[4] Plugin е готов за създаване на widget
```
### 2. Създаване на Widget и Инициализация
```
[1] Потребителят отваря Glue Cell Settings
      ↓
[2] GlueCellSettingsPlugin.create_widget()
      ↓
[3] Създава GlueCellSettingsAppWidget
      ↓
[4] GlueCellSettingsAppWidget.setup_ui()
      ↓
[5] Създава GlueCellSettingsTabLayout
      ↓
[6] Инициализация на компоненти:
      ├─ [6a] GlueCellsManagerSingleton.get_instance()
      │   - Singleton pattern
      │   - Управлява 3-те cells
      │
      ├─ [6b] GlueDataFetcher()
      │   - Създава background thread
      │   - Започва fetch на данни
      │   - .start() → thread running
      │
      └─ [6c] MessageBroker()
          - Subscribe към 3 weight topics
          - broker.subscribe(GLUE_METER_1_VALUE, callback)
          - broker.subscribe(GLUE_METER_2_VALUE, callback)
          - broker.subscribe(GLUE_METER_3_VALUE, callback)
      ↓
[7] Зареждане на конфигурация:
      ├─ get_core_settings_path("glue_cell_config.json")
      │   - Application-aware path resolution
      │   - ~/.cache/.../glue_dispensing_application/core_settings/
      │
      └─ _load_settings_from_endpoints()
          - Заявка към GLUE_CELLS_CONFIG_GET
          - Зарежда config за 3-те cells
          - Попълва UI полета
      ↓
[8] Създаване на UI:
      ├─ Cell Selection Dropdown
      ├─ 3 Settings Groups (Connection, Calibration, Measurement)
      ├─ Real-time Monitoring Display
      └─ Control Buttons (Tare, Calibrate, Save)
      ↓
[9] Свързване на signals:
      - Auto-save на промени
      - Cell selection change
      - Mode toggle
      - Button clicks
      ↓
[10] UI е готов и подписан към real-time updates
```
**Пример код:**
```python
# В GlueCellSettingsTabLayout.__init__
self.glue_cells_manager = GlueCellsManagerSingleton.get_instance()
self.glue_data_fetcher = GlueDataFetcher()
self.glue_data_fetcher.start()  # Background thread starts
self.broker = MessageBroker()
self.broker.subscribe(GlueTopics.GLUE_METER_1_VALUE, self._on_weight1_updated)
```
### 3. Real-time Weight Update Flow (Critical Path)
```
[1] Glue Monitor Server (Hardware)
      - HX711 sensor чете тегло
      - WebSocket емитира ново значение
      ↓
[2] GlueDataFetcher (Background Thread)
      - Получава WebSocket message
      - Parse на JSON data
      ↓
[3] MessageBroker.publish()
      - topic: GlueTopics.GLUE_METER_1_VALUE
      - data: {'weight': 2.345, 'timestamp': ...}
      ↓
[4] GlueCellSettingsTabLayout._on_weight1_updated(data)
      - Callback се извиква (subscriber)
      - UI thread context
      ↓
[5] Актуализация на UI:
      if self.current_cell == 1:
          self.weight_value_label.setText(f"{data['weight']:.3f} kg")
          self.weight_value_label.setStyleSheet("color: green;")
      ↓
[6] UI показва актуално тегло (real-time)
```
**Честота на updates:** ~1-10 Hz (зависи от sampling rate)
**Пример код:**
```python
def _on_weight1_updated(self, data):
    """Called when Cell 1 weight updates via MessageBroker"""
    try:
        weight = data.get('weight', 0.0)
        # Update UI if this cell is currently selected
        if self.current_cell == 1:
            self.weight_value_label.setText(f"{weight:.3f} kg")
            # Color coding based on threshold
            if weight < 0.1:
                self.weight_value_label.setStyleSheet("color: red;")
            else:
                self.weight_value_label.setStyleSheet("color: green;")
    except Exception as e:
        print(f"Error updating weight display: {e}")
```
### 4. Cell Selection Change Flow
```
[1] Потребителят избира "Load Cell 2" от dropdown
      ↓
[2] cell_dropdown.currentIndexChanged signal
      ↓
[3] on_cell_changed(index)
      - self.current_cell = index + 1  # 0→1, 1→2, 2→3
      ↓
[4] load_cell_config(cell_id=2)
      ├─ Зарежда config от self.cells_config[str(cell_id)]
      │
      ├─ Попълва UI полета за Cell 2:
      │   - glue_type_dropdown.setCurrentText(config['glue_type'])
      │   - motor_address_input.setText(config['motor_address'])
      │   - scale_factor_input.setText(config['scale_factor'])
      │   - offset_input.setText(config['offset'])
      │   - и т.н.
      │
      └─ Актуализира weight display за Cell 2
          - Взема последно известно тегло от MessageBroker
          - weight_value_label.setText(...)
      ↓
[5] UI показва настройки и real-time данни за Cell 2
```
### 5. Tare Operation Flow
```
[1] Потребителят кликва "Tare" бутон
      ↓
[2] on_tare_clicked()
      - Показва loading state
      - tare_button.setEnabled(False)
      - tare_button.setText("Taring...")
      ↓
[3] HTTP заявка към Glue Monitor Server:
      POST http://localhost:5000/tare
      {
        "cell_id": 2,
        "mode": "production"  // or "test"
      }
      ↓
[4] Glue Monitor Server:
      - Изпраща команда към HX711
      - Чете current raw value
      - Sets offset = raw_value
      - Връща success response
      ↓
[5] Response получен:
      if response.status_code == 200:
          showToast("✅ Cell 2 tared successfully")
          # Update local offset value
          offset = response.json()['new_offset']
          offset_input.setText(str(offset))
          # Save to config
          save_cell_config(cell_id=2, 'offset', offset)
      ↓
[6] UI refresh:
      - tare_button.setEnabled(True)
      - tare_button.setText("Tare")
      - Weight display now shows 0.000 kg (тарирано)
```
**Пример код:**
```python
def on_tare_clicked(self):
    """Tare the currently selected load cell"""
    cell_id = self.current_cell
    self.tare_button.setEnabled(False)
    self.tare_button.setText("Taring...")
    try:
        # Get current mode
        mode = "test" if self.mode_toggle.isChecked() else "production"
        # Send tare request to Glue Monitor Server
        response = requests.post(
            TARE_ENDPOINT,
            json={'cell_id': cell_id, 'mode': mode},
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            new_offset = result.get('new_offset', 0)
            # Update UI
            self.offset_input.setText(str(new_offset))
            # Save to config
            self.save_cell_config(cell_id, 'offset', new_offset)
            self.showToast(f"✅ Cell {cell_id} tared successfully")
        else:
            self.showToast(f"❌ Tare failed: {response.text}")
    except Exception as e:
        self.showToast(f"❌ Tare error: {str(e)}")
    finally:
        self.tare_button.setEnabled(True)
        self.tare_button.setText("Tare")
```
### 6. Calibration Flow
```
[1] Потребителят задава известно тегло:
      - expected_weight_input.setText("1.000")  # 1 kg
      ↓
[2] Потребителят поставя 1kg обект на везната
      ↓
[3] Потребителят кликва "Calibrate"
      ↓
[4] on_calibrate_clicked()
      ↓
[5] Чете current raw value от сензора:
      - HTTP GET към Glue Monitor Server
      - /api/cells/{cell_id}/raw_value
      - response: {"raw_value": 8432756}
      ↓
[6] Изчислява scale_factor:
      expected_weight = 1.000  # kg
      current_offset = self.offset_input.text()  # от tare
      raw_value = 8432756
      scale_factor = (raw_value - current_offset) / expected_weight
      # scale_factor = 8400000 / 1.000 = 8400000
      ↓
[7] Изпраща update към сървъра:
      POST http://localhost:5000/update_scale
      {
        "cell_id": 2,
        "scale_factor": 8400000,
        "mode": "production"
      }
      ↓
[8] Актуализира UI и конфигурация:
      - scale_factor_input.setText("8400000")
      - save_cell_config(cell_id, 'scale_factor', 8400000)
      - showToast("✅ Cell 2 calibrated")
      ↓
[9] От този момент:
      weight = (raw_value - offset) / scale_factor
      // real-time weight е коректен
```
### 7. Auto-save Flow (Settings Change)
```
[1] Потребителят променя Motor Address:
      - motor_address_input.setText("15")
      ↓
[2] QLineEdit.textChanged signal
      ↓
[3] Lambda function емитира:
      self.value_changed_signal.emit(
        'motor_address',        # key
        '15',                   # value
        'GlueCellSettings'      # className
      )
      ↓
[4] GlueCellSettingsAppWidget.settingsChangeCallback()
      ↓
[5] controller_service.settings.update_setting(key, value, className)
      ↓
[6] Актуализира локалния config:
      self.cells_config[str(current_cell)]['motor_address'] = '15'
      ↓
[7] Запазва в JSON файла:
      with open(self.config_path, 'w') as f:
          json.dump(self.cells_config, f, indent=2)
      ↓
[8] Изпраща към API (optional):
      POST /api/v1/settings/glue/cells/update
      {
        "cell_id": 2,
        "field": "motor_address",
        "value": "15"
      }
      ↓
[9] Показва feedback:
      print("✅ Motor address updated to 15")
```
### 8. Mode Toggle Flow (Test ↔ Production)
```
[1] Потребителят кликва Mode Toggle
      ↓
[2] mode_toggle.stateChanged signal
      ↓
[3] on_mode_changed(checked)
      ↓
[4] if checked:
          mode = "test"
          mode_label.setText("Test (Mock Server)")
          mode_label.setStyleSheet("color: #FF8C00;")
      else:
          mode = "production"
          mode_label.setText("Production")
          mode_label.setStyleSheet("color: #2E8B57;")
      ↓
[5] Запазва MODE в config:
      self.cells_config['MODE'] = mode
      save_config_to_file()
      ↓
[6] GlueDataFetcher получава notification:
      - Превключва към mock/real data source
      - Рестартира WebSocket connection
      ↓
[7] От този момент:
      - Test mode: Mock data (random values)
      - Production mode: Real HX711 sensor data
```
---
## Файлова Структура
### Plugin Layer
```
src/plugins/core/glue_cell_settings_plugin/
├── __init__.py
├── plugin.py                          # GlueCellSettingsPlugin
├── plugin.json                        # Plugin metadata
│
├── icons/
│   └── weight_cell.png                # Plugin icon
│
└── ui/
    ├── __init__.py
    └── GlueCellSettingsAppWidget.py   # Main widget
```
### UI Components (Shared with Settings Plugin)
```
src/plugins/core/settings/ui/
└── GlueCellSettingsTabLayout.py       # Main layout (1421 lines)
    - Cell selection
    - Settings groups
    - Real-time monitoring
    - Control buttons
```
### Communication Layer (Endpoints)
```
src/communication_layer/api/v1/endpoints/
└── glue_endpoints.py                  # Glue cell endpoints
    - GLUE_CELLS_CONFIG_GET
    - GLUE_CELLS_CONFIG_SET
    - GLUE_CELL_UPDATE
    - GLUE_CELL_CALIBRATE
    - GLUE_CELL_TARE
    - GLUE_CELL_UPDATE_TYPE
    - GLUE_CELL_WEIGHTS_GET
    - GLUE_CELL_WEIGHT_GET
```
### Message Broker Topics
```
src/communication_layer/api/v1/topics.py
class GlueTopics:
    GLUE_METER_1_VALUE = "glue/meter/1/value"
    GLUE_METER_2_VALUE = "glue/meter/2/value"
    GLUE_METER_3_VALUE = "glue/meter/3/value"
```
### Business Logic (Glue System)
```
src/modules/shared/tools/glue_monitor_system/
├── config.py                          # Server URLs and endpoints
│   - UPDATE_SCALE_ENDPOINT
│   - TARE_ENDPOINT
│   - UPDATE_OFFSET_ENDPOINT
│
├── data_fetcher.py                    # GlueDataFetcher (Thread)
│   - Background data fetching
│   - WebSocket client
│   - MessageBroker publishing
│
└── glue_cells_manager.py              # GlueCellsManagerSingleton
    - Singleton pattern
    - getCellById(cell_id)
    - update_cell_config()
```
### Message Broker
```
src/modules/shared/MessageBroker.py    # Pub/Sub system
- subscribe(topic, callback)
- publish(topic, data)
- unsubscribe(topic, callback)
```
### Storage
```
~/.cache/cobot-glue-dispensing-v5/
└── glue_dispensing_application/
    └── core_settings/
        └── glue_cell_config.json      # Glue cells configuration
```
---
## API Endpoints
### 1. GLUE_CELLS_CONFIG_GET
**Път:** `/api/v1/settings/glue/cells`  
**Метод:** GET  
**Цел:** Зареждане на конфигурация за всички 3 cells
**Request:**
```python
controller_service.send_request(glue_endpoints.GLUE_CELLS_CONFIG_GET)
```
**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "1": {
      "glue_type": "Type A",
      "motor_address": "10",
      "scale_factor": "8400000",
      "offset": "12345",
      "sampling_rate": "10",
      "filter_type": "Moving Average",
      "averaging_samples": "5",
      "expected_weight": "1.000"
    },
    "2": {
      "glue_type": "Type B",
      "motor_address": "11",
      "scale_factor": "8350000",
      "offset": "12456",
      "sampling_rate": "10",
      "filter_type": "Moving Average",
      "averaging_samples": "5",
      "expected_weight": "1.000"
    },
    "3": {
      "glue_type": "Type C",
      "motor_address": "12",
      "scale_factor": "8420000",
      "offset": "12567",
      "sampling_rate": "10",
      "filter_type": "Moving Average",
      "averaging_samples": "5",
      "expected_weight": "1.000"
    },
    "MODE": "production"
  }
}
```
**Handler:** `SettingsDispatcher.handle_glue_cells_settings()`
---
### 2. GLUE_CELLS_CONFIG_SET
**Път:** `/api/v1/settings/glue/cells/set`  
**Метод:** POST  
**Цел:** Запазване на пълна конфигурация за всички cells
**Request:**
```python
controller_service.send_request(
    glue_endpoints.GLUE_CELLS_CONFIG_SET,
    data={
        '1': {...},
        '2': {...},
        '3': {...},
        'MODE': 'production'
    }
)
```
**Response (Success):**
```json
{
  "status": "success",
  "message": "Glue cells configuration saved successfully"
}
```
---
### 3. GLUE_CELL_UPDATE
**Път:** `/api/v1/settings/glue/cells/update`  
**Метод:** POST  
**Цел:** Актуализация на отделно поле за конкретен cell
**Request:**
```python
controller_service.send_request(
    glue_endpoints.GLUE_CELL_UPDATE,
    data={
        'cell_id': '2',
        'field': 'motor_address',
        'value': '15'
    }
)
```
**Response (Success):**
```json
{
  "status": "success",
  "message": "Cell 2 motor_address updated to 15"
}
```
---
### 4. GLUE_CELL_CALIBRATE
**Път:** `/api/v1/settings/glue/cells/calibrate`  
**Метод:** POST  
**Цел:** Калибрация на load cell с известно тегло
**Request:**
```python
controller_service.send_request(
    glue_endpoints.GLUE_CELL_CALIBRATE,
    data={
        'cell_id': '1',
        'expected_weight': 1.000,  # kg
        'mode': 'production'
    }
)
```
**Response (Success):**
```json
{
  "status": "success",
  "message": "Cell 1 calibrated successfully",
  "data": {
    "scale_factor": 8400000,
    "raw_value": 8412345,
    "offset": 12345
  }
}
```
**Калибрационна Формула:**
```
scale_factor = (raw_value - offset) / expected_weight
```
---
### 5. GLUE_CELL_TARE
**Път:** `/api/v1/settings/glue/cells/tare`  
**Метод:** POST  
**Цел:** Tare (нулиране) на load cell
**Request:**
```python
controller_service.send_request(
    glue_endpoints.GLUE_CELL_TARE,
    data={
        'cell_id': '2',
        'mode': 'production'
    }
)
```
**Response (Success):**
```json
{
  "status": "success",
  "message": "Cell 2 tared successfully",
  "data": {
    "new_offset": 8412456
  }
}
```
**Tare Операция:**
```
1. Read current raw_value from sensor
2. Set offset = raw_value
3. Now: weight = (raw_value - offset) / scale_factor = 0
```
---
### 6. GLUE_CELL_UPDATE_TYPE
**Път:** `/api/v1/settings/glue/cells/type`  
**Метод:** POST  
**Цел:** Актуализация на glue type за cell
**Request:**
```python
controller_service.send_request(
    glue_endpoints.GLUE_CELL_UPDATE_TYPE,
    data={
        'cell_id': '1',
        'glue_type': 'Type D'
    }
)
```
**Response (Success):**
```json
{
  "status": "success",
  "message": "Cell 1 glue type updated to Type D"
}
```
---
### 7. GLUE_CELL_WEIGHTS_GET
**Път:** `/api/v1/glue/cells/weights`  
**Метод:** GET  
**Цел:** Получаване на текущи тегла за всички cells
**Request:**
```python
controller_service.send_request(glue_endpoints.GLUE_CELL_WEIGHTS_GET)
```
**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "1": {
      "weight": 2.345,
      "timestamp": "2025-12-10T14:30:15.123Z",
      "status": "stable"
    },
    "2": {
      "weight": 1.876,
      "timestamp": "2025-12-10T14:30:15.123Z",
      "status": "stable"
    },
    "3": {
      "weight": 0.543,
      "timestamp": "2025-12-10T14:30:15.123Z",
      "status": "low"
    }
  }
}
```
---
### 8. GLUE_CELL_WEIGHT_GET
**Път:** `/api/v1/glue/cells/weight`  
**Метод:** GET  
**Цел:** Получаване на тегло за конкретен cell
**Request:**
```python
controller_service.send_request(
    glue_endpoints.GLUE_CELL_WEIGHT_GET,
    data={'cell_id': '2'}
)
```
**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "weight": 1.876,
    "raw_value": 15768432,
    "timestamp": "2025-12-10T14:30:15.123Z"
  }
}
```
---
## Компоненти
### 1. GlueCellSettingsPlugin (Plugin Entry Point)
**Файл:** `plugins/core/glue_cell_settings_plugin/plugin.py`
**Описание:** Входна точка за plugin-а. Имплементира IPlugin интерфейса.
**Metadata:**
```python
PluginMetadata(
    name="Glue Cell Settings",
    version="1.0.0",
    author="PL Team",
    description="Manage settings for glue cells (weight sensors, motors, pumps)",
    category=PluginCategory.CORE,
    permissions=[PluginPermission.FILE_SYSTEM],
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
    if not self._widget_instance:
        self._widget_instance = GlueCellSettingsAppWidget(
            parent=parent,
            controller=self.controller_service.controller,
            controller_service=self.controller_service
        )
    return self._widget_instance
```
---
### 2. GlueCellSettingsAppWidget (Main Widget)
**Файл:** `plugins/core/glue_cell_settings_plugin/ui/GlueCellSettingsAppWidget.py`
**Описание:** Главен widget, обвива GlueCellSettingsTabLayout.
**Signal Handling:**
```python
# Settings change callback
def settingsChangeCallback(key, value, className):
    result = self.controller_service.settings.update_setting(
        key, value, className
    )
```
**Lifecycle:**
```python
def setup_ui(self):
    # Create content widget
    self.content_widget = QWidget()
    # Create layout
    self.content_layout = GlueCellSettingsTabLayout(
        parent_widget=self.content_widget,
        controller_service=self.controller_service
    )
    # Connect signal
    self.content_layout.value_changed_signal.connect(
        settingsChangeCallback
    )
    self.content_widget.setLayout(self.content_layout)
def clean_up(self):
    """Cleanup resources"""
    if hasattr(self, 'content_layout'):
        self.content_layout._cleanup_message_broker()
```
---
### 3. GlueCellSettingsTabLayout (Main Layout)
**Файл:** `plugins/core/settings/ui/GlueCellSettingsTabLayout.py`
**Описание:** Основен layout с всички UI компоненти и бизнес логика.
**Инициализация:**
```python
def __init__(self, parent_widget=None, controller_service=None):
    # Initialize glue system components
    self.glue_cells_manager = GlueCellsManagerSingleton.get_instance()
    self.glue_data_fetcher = GlueDataFetcher()
    self.glue_data_fetcher.start()
    # Initialize message broker
    self.broker = MessageBroker()
    self.broker.subscribe(GlueTopics.GLUE_METER_1_VALUE, self._on_weight1_updated)
    self.broker.subscribe(GlueTopics.GLUE_METER_2_VALUE, self._on_weight2_updated)
    self.broker.subscribe(GlueTopics.GLUE_METER_3_VALUE, self._on_weight3_updated)
    # Load configuration
    self.config_path = get_core_settings_path("glue_cell_config.json")
    self._load_settings_from_endpoints()
    # Create UI
    self.create_main_content()
```
**UI Groups:**
1. **Cell Selection Group**
   - Dropdown за избор на cell (1, 2, 3)
   - Status indicator
2. **Connection & Hardware Settings Group**
   - Mode Toggle (Test/Production)
   - Glue Type Dropdown
   - Motor Address Input
3. **Calibration Settings Group**
   - Scale Factor Input
   - Offset Input (readonly)
   - Expected Weight Input
4. **Measurement Settings Group**
   - Sampling Rate
   - Filter Type
   - Averaging Samples
5. **Real-time Monitoring Group**
   - Current Weight Display
   - Color-coded based on value
6. **Control Buttons Group**
   - Tare Button
   - Calibrate Button
   - Save Configuration Button
**Signal Emission:**
```python
# Auto-save на промяна
self.motor_address_input.textChanged.connect(
    lambda v: self.value_changed_signal.emit(
        'motor_address', v, 'GlueCellSettings'
    )
)
```
---
### 4. GlueCellsManagerSingleton (Business Logic)
**Файл:** `modules/shared/tools/glue_monitor_system/glue_cells_manager.py`
**Описание:** Singleton за управление на 3-те glue cells.
**Pattern:**
```python
class GlueCellsManagerSingleton:
    _instance = None
    @staticmethod
    def get_instance():
        if GlueCellsManagerSingleton._instance is None:
            GlueCellsManagerSingleton._instance = GlueCellsManager()
        return GlueCellsManagerSingleton._instance
```
**Методи:**
```python
def getCellById(self, cell_id: int) -> GlueCell:
    """Get cell configuration by ID"""
    return self.cells[cell_id]
def update_cell_config(self, cell_id: int, field: str, value):
    """Update cell configuration field"""
    self.cells[cell_id].set_config(field, value)
```
---
### 5. GlueDataFetcher (Background Thread)
**Файл:** `modules/shared/tools/glue_monitor_system/data_fetcher.py`
**Описание:** Background thread за fetch на real-time данни от Glue Monitor Server.
**Thread Lifecycle:**
```python
class GlueDataFetcher(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        self.broker = MessageBroker()
    def run(self):
        """Main thread loop"""
        while self.running:
            try:
                # Fetch data from WebSocket
                data = self.fetch_weights()
                # Publish to MessageBroker
                for cell_id, weight_data in data.items():
                    topic = f"glue/meter/{cell_id}/value"
                    self.broker.publish(topic, weight_data)
                # Sleep interval
                time.sleep(0.1)  # 10 Hz
            except Exception as e:
                print(f"Data fetch error: {e}")
                time.sleep(1)
    def stop(self):
        """Stop the thread"""
        self.running = False
```
---
### 6. MessageBroker (Pub/Sub System)
**Файл:** `modules/shared/MessageBroker.py`
**Описание:** Publish/Subscribe pattern за event-driven communication.
**API:**
```python
class MessageBroker:
    def __init__(self):
        self._subscribers = {}  # topic -> [callbacks]
    def subscribe(self, topic: str, callback: callable):
        """Subscribe to a topic"""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
    def publish(self, topic: str, data: dict):
        """Publish data to topic subscribers"""
        if topic in self._subscribers:
            for callback in self._subscribers[topic]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Callback error: {e}")
    def unsubscribe(self, topic: str, callback: callable):
        """Unsubscribe from topic"""
        if topic in self._subscribers:
            self._subscribers[topic].remove(callback)
```
**Използване:**
```python
# Subscribe
broker = MessageBroker()
broker.subscribe("glue/meter/1/value", my_callback)
# Publish
broker.publish("glue/meter/1/value", {'weight': 2.345})
# Callback се извиква автоматично
def my_callback(data):
    print(f"Weight: {data['weight']}")
```
---
## Message Broker Integration
### Topic Structure
```
glue/meter/1/value  →  Cell 1 weight updates
glue/meter/2/value  →  Cell 2 weight updates
glue/meter/3/value  →  Cell 3 weight updates
```
### Data Format
```python
{
    'weight': 2.345,           # kg (float)
    'raw_value': 19712345,     # raw sensor value (int)
    'timestamp': '2025-12-10T14:30:15.123Z',
    'status': 'stable'         # 'stable', 'fluctuating', 'error'
}
```
### Subscription Example
```python
# В GlueCellSettingsTabLayout.__init__
self.broker = MessageBroker()
# Subscribe to all 3 cells
self.broker.subscribe(
    GlueTopics.GLUE_METER_1_VALUE,
    self._on_weight1_updated
)
self.broker.subscribe(
    GlueTopics.GLUE_METER_2_VALUE,
    self._on_weight2_updated
)
self.broker.subscribe(
    GlueTopics.GLUE_METER_3_VALUE,
    self._on_weight3_updated
)
# Callbacks
def _on_weight1_updated(self, data):
    """Handle Cell 1 weight update"""
    if self.current_cell == 1:
        self.update_weight_display(data['weight'])
def _on_weight2_updated(self, data):
    """Handle Cell 2 weight update"""
    if self.current_cell == 2:
        self.update_weight_display(data['weight'])
def _on_weight3_updated(self, data):
    """Handle Cell 3 weight update"""
    if self.current_cell == 3:
        self.update_weight_display(data['weight'])
```
### Cleanup (Important!)
```python
def cleanup(self):
    """Must be called before widget destruction"""
    # Unsubscribe to prevent errors
    self.broker.unsubscribe(GlueTopics.GLUE_METER_1_VALUE, self._on_weight1_updated)
    self.broker.unsubscribe(GlueTopics.GLUE_METER_2_VALUE, self._on_weight2_updated)
    self.broker.unsubscribe(GlueTopics.GLUE_METER_3_VALUE, self._on_weight3_updated)
```
**⚠️ ВАЖНО:** Винаги unsubscribe преди widget destruction, иначе callbacks към изтрити обекти ще предизвикат грешки!
---
## Real-time Weight Monitoring
### Hardware Setup
```
┌─────────────────┐
│   Load Cell     │  (Physical sensor - весоизмервателна клетка)
│   (HX711)       │
└────────┬────────┘
         │ (24-bit ADC output)
         ↓
┌─────────────────┐
│  Raspberry Pi   │  (Running Glue Monitor Server)
│  или Arduino    │
└────────┬────────┘
         │ (WebSocket)
         ↓
┌─────────────────┐
│ GlueDataFetcher │  (Background Thread в приложението)
│   (Thread)      │
└────────┬────────┘
         │ (MessageBroker.publish)
         ↓
┌─────────────────┐
│ MessageBroker   │  (In-process pub/sub)
└────────┬────────┘
         │ (callback)
         ↓
┌─────────────────┐
│      UI         │  (Weight Display Label)
│  (Qt Widget)    │
└─────────────────┘
```
### Weight Calculation Formula
```python
# Raw value от HX711 sensor
raw_value = 19712345  # 24-bit integer
# Calibration parameters (от config)
offset = 12345        # от tare операция
scale_factor = 8400000  # от calibration
# Calculate actual weight
weight_kg = (raw_value - offset) / scale_factor
# Example:
# weight_kg = (19712345 - 12345) / 8400000 = 2.345 kg
```
### Update Frequency
- **Sampling Rate:** Конфигурируем (1-100 Hz)
- **Default:** 10 Hz (10 updates per second)
- **Network latency:** ~10-50ms
- **UI update:** Throttled to avoid flickering
### Filtering
Поддържани filter types:
1. **Moving Average** - Плъзгаща средна стойност
2. **Median Filter** - Медиана от N samples
3. **Kalman Filter** - Advanced noise filtering
4. **None** - Raw values (no filtering)
**Пример - Moving Average:**
```python
samples = [2.340, 2.345, 2.342, 2.348, 2.341]
averaging_samples = 5
filtered_weight = sum(samples) / len(samples)
# filtered_weight = 2.343 kg
```
---
## Примери за Използване
### Пример 1: Първоначална Настройка на Cell
```python
"""
Сценарий: Настройка на нов load cell от нулата
"""
# Стъпка 1: Избор на cell
cell_dropdown.setCurrentIndex(0)  # Cell 1
# Стъпка 2: Избор на glue type
glue_type_dropdown.setCurrentText("Type A")
# Стъпка 3: Задаване на motor address
motor_address_input.setText("10")
# Стъпка 4: Tare операция (празна везна)
on_tare_clicked()
# → Сървърът чете raw value
# → offset = raw_value (напр. 12345)
# → offset_input.setText("12345")
# Стъпка 5: Calibration с известно тегло
# Поставяме 1.000 kg обект на везната
expected_weight_input.setText("1.000")
on_calibrate_clicked()
# → Чете current raw value (напр. 8412345)
# → scale_factor = (8412345 - 12345) / 1.000 = 8400000
# → scale_factor_input.setText("8400000")
# Стъпка 6: Запазване
on_save_clicked()
# → Конфигурацията се запазва в JSON файла
# → Готово! Cell е калибриран и готов за работа
```
---
### Пример 2: Real-time Мониторинг
```python
"""
Сценарий: Наблюдение на тегло в real-time
"""
# UI код в GlueCellSettingsTabLayout
def _on_weight1_updated(self, data):
    """MessageBroker callback за Cell 1"""
    try:
        weight = data.get('weight', 0.0)
        timestamp = data.get('timestamp', '')
        status = data.get('status', 'unknown')
        # Update UI само ако Cell 1 е избран
        if self.current_cell == 1:
            # Format weight с 3 decimal places
            self.weight_value_label.setText(f"{weight:.3f} kg")
            # Color coding
            if weight < 0.1:
                color = "red"      # Празна
                status_text = "Empty"
            elif weight < 1.0:
                color = "orange"   # Ниско
                status_text = "Low"
            else:
                color = "green"    # Нормално
                status_text = "OK"
            self.weight_value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
            self.status_indicator.setText(status_text)
            # Log за debugging
            print(f"[Cell 1] Weight: {weight:.3f} kg | Status: {status} | Time: {timestamp}")
    except Exception as e:
        print(f"Error updating weight display: {e}")
```
**Резултат:** UI се актуализира автоматично 10 пъти в секунда с нови стойности.
---
### Пример 3: Превключване между Cells
```python
"""
Сценарий: Бърза проверка на всички 3 cells
"""
def check_all_cells():
    """Iterate через всички cells и покажи тегла"""
    for cell_id in [1, 2, 3]:
        # Избор на cell
        cell_dropdown.setCurrentIndex(cell_id - 1)
        # UI автоматично се актуализира чрез on_cell_changed()
        # load_cell_config(cell_id) се извиква
        # Wait малко за UI update
        QApplication.processEvents()
        time.sleep(0.5)
        # Чете current weight
        current_weight = weight_value_label.text()
        print(f"Cell {cell_id}: {current_weight}")
# Output:
# Cell 1: 2.345 kg
# Cell 2: 1.876 kg
# Cell 3: 0.543 kg
```
---
### Пример 4: Test Mode с Mock Data
```python
"""
Сценарий: Тестване на UI без реален hardware
"""
# Превключване в Test mode
mode_toggle.setChecked(True)
# → on_mode_changed(True)
# → MODE = "test"
# → mode_label.setText("Test (Mock Server)")
# GlueDataFetcher автоматично превключва към mock data:
class GlueDataFetcher(Thread):
    def fetch_weights(self):
        if self.mode == "test":
            # Generate random mock data
            return {
                '1': {
                    'weight': random.uniform(0.5, 3.0),
                    'raw_value': random.randint(4000000, 25000000),
                    'timestamp': datetime.now().isoformat(),
                    'status': 'stable'
                },
                '2': {...},
                '3': {...}
            }
        else:
            # Fetch real data from WebSocket
            return self.websocket_client.receive()
# UI показва mock data в real-time
# Полезно за:
# - UI development без hardware
# - Демонстрации
# - Automated testing
```
---
### Пример 5: Batch Configuration Update
```python
"""
Сценарий: Конфигуриране на всички 3 cells наведнъж
"""
# Configuration template
cell_configs = {
    '1': {
        'glue_type': 'Type A',
        'motor_address': '10',
        'sampling_rate': '10',
        'filter_type': 'Moving Average',
        'averaging_samples': '5'
    },
    '2': {
        'glue_type': 'Type B',
        'motor_address': '11',
        'sampling_rate': '10',
        'filter_type': 'Moving Average',
        'averaging_samples': '5'
    },
    '3': {
        'glue_type': 'Type C',
        'motor_address': '12',
        'sampling_rate': '10',
        'filter_type': 'Moving Average',
        'averaging_samples': '5'
    }
}
# Apply configuration
for cell_id, config in cell_configs.items():
    # Select cell
    cell_dropdown.setCurrentIndex(int(cell_id) - 1)
    # Apply each setting
    for field, value in config.items():
        widget = getattr(self, f"{field}_input")
        if isinstance(widget, QComboBox):
            widget.setCurrentText(value)
        elif isinstance(widget, QLineEdit):
            widget.setText(value)
        # Auto-save signal се задейства автоматично
        print(f"Cell {cell_id}: {field} = {value}")
# Save all
on_save_clicked()
print("✅ All cells configured successfully!")
```
---
### Пример 6: Error Handling и Retry Logic
```python
"""
Сценарий: Graceful handling на connection errors
"""
def on_tare_clicked_with_retry(self):
    """Tare с retry logic"""
    cell_id = self.current_cell
    max_retries = 3
    retry_delay = 1.0  # seconds
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Tare attempt {attempt}/{max_retries}")
            # Send tare request
            mode = "test" if self.mode_toggle.isChecked() else "production"
            response = requests.post(
                TARE_ENDPOINT,
                json={'cell_id': cell_id, 'mode': mode},
                timeout=5
            )
            if response.status_code == 200:
                # Success
                result = response.json()
                new_offset = result.get('new_offset', 0)
                self.offset_input.setText(str(new_offset))
                self.save_cell_config(cell_id, 'offset', new_offset)
                self.showToast(f"✅ Cell {cell_id} tared successfully")
                return True
            else:
                # Server error
                error_msg = response.text
                print(f"Tare failed (HTTP {response.status_code}): {error_msg}")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.showToast(f"❌ Tare failed after {max_retries} attempts")
                    return False
        except requests.Timeout:
            print(f"Tare timeout (attempt {attempt})")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                self.showToast("❌ Tare timeout - check connection")
                return False
        except Exception as e:
            print(f"Tare error: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                self.showToast(f"❌ Tare error: {str(e)}")
                return False
    return False
```
---
## Configuration File Format
**Локация:** `~/.cache/cobot-glue-dispensing-v5/glue_dispensing_application/core_settings/glue_cell_config.json`
**Структура:**
```json
{
  "1": {
    "glue_type": "Type A",
    "motor_address": "10",
    "scale_factor": "8400000",
    "offset": "12345",
    "sampling_rate": "10",
    "filter_type": "Moving Average",
    "averaging_samples": "5",
    "expected_weight": "1.000"
  },
  "2": {
    "glue_type": "Type B",
    "motor_address": "11",
    "scale_factor": "8350000",
    "offset": "12456",
    "sampling_rate": "10",
    "filter_type": "Moving Average",
    "averaging_samples": "5",
    "expected_weight": "1.000"
  },
  "3": {
    "glue_type": "Type C",
    "motor_address": "12",
    "scale_factor": "8420000",
    "offset": "12567",
    "sampling_rate": "10",
    "filter_type": "Moving Average",
    "averaging_samples": "5",
    "expected_weight": "1.000"
  },
  "MODE": "production"
}
```
**Полета:**
| Поле | Тип | Описание |
|------|-----|----------|
| `glue_type` | string | Вид лепило за този cell |
| `motor_address` | string | Modbus адрес на помпата |
| `scale_factor` | string | Calibration scale factor |
| `offset` | string | Tare offset стойност |
| `sampling_rate` | string | Hz за sampling |
| `filter_type` | string | Тип filter за данните |
| `averaging_samples` | string | Брой samples за averaging |
| `expected_weight` | string | Expected тегло за calibration (kg) |
| `MODE` | string | "production" или "test" |
---
## Заключение
Glue Cell Settings Plugin имплементира пълноценна система за управление на тензометрични датчици с:
✅ **Real-time Monitoring** - WebSocket + MessageBroker за live данни  
✅ **Multi-cell Support** - До 3 независими датчика  
✅ **Calibration System** - Tare и calibration с известно тегло  
✅ **Auto-save** - Автоматично запазване на всички промени  
✅ **Test Mode** - Mock data за development без hardware  
✅ **Filtering** - Multiple filter types за стабилни показания  
✅ **Modbus Integration** - Motor address configuration  
✅ **Application-aware Storage** - Правилно path resolution  
✅ **Graceful Cleanup** - Proper MessageBroker unsubscribe  
Системата е готова за production използване в glue dispensing applications! 🎉
---
**Версия:** 1.0  
**Дата:** 10 Декември 2025  
**Автор:** Cobot Glue Dispensing System Team
---
## 🔄 ВАЖНА АКТУАЛИЗАЦИЯ (Декември 2025)
### Архитектурна Промяна: Премахнато Директното Писане в JSON
**Преди (❌ ГРЕШНО):**
```python
# GlueCellSettingsTabLayout - СТАР КОД
def on_mode_changed(self, state):
    with open(self.config_path, 'w') as f:
        json.dump(config_data, f, indent=2)  # ❌ Директно писане!
```
**Сега (✅ ПРАВИЛНО):**
```python
# GlueCellSettingsTabLayout - НОВ КОД
def on_mode_changed(self, state):
    controller = self.controller_service.get_controller()
    settings_service = controller.controller_service.settings
    new_mode = "test" if state else "production"
    result = settings_service.update_glue_cells_config({"MODE": new_mode})
    if result.success:
        # UI актуализация
    else:
        # Грешка: result.message
```
---
## Нова Архитектура с SettingsService
### Поток на Данните (АКТУАЛИЗИРАН)
```
┌──────────────────────────────────────────────────────────────┐
│                  UI Layer                                     │
│  GlueCellSettingsTabLayout                                    │
│   - on_mode_changed()                                         │
│   - _update_cell_config()                                     │
│   - _update_cell_calibration()                                │
│   - _update_cell_measurement()                                │
│                                                                │
│  ✅ Използва: self.controller_service                         │
│  ❌ НЕ използва: open(file, 'w'), json.dump()                │
└──────────────────────────────────────────────────────────────┘
                    ↓ (get_controller())
┌──────────────────────────────────────────────────────────────┐
│              Service Layer                                    │
│  SettingsService (frontend/core/services/domain/)            │
│   ┌────────────────────────────────────────────────────────┐ │
│   │ Нови Методи:                                           │ │
│   │                                                         │ │
│   │ 1. get_glue_cells_config() → ServiceResult            │ │
│   │    - Зарежда пълна конфигурация                       │ │
│   │    - Endpoint: GLUE_CELLS_CONFIG_GET                  │ │
│   │                                                         │ │
│   │ 2. update_glue_cells_config(data) → ServiceResult     │ │
│   │    - Актуализира глобални настройки (MODE)            │ │
│   │    - Endpoint: GLUE_CELLS_CONFIG_SET                  │ │
│   │    - Пример: {"MODE": "test"}                         │ │
│   │                                                         │ │
│   │ 3. update_glue_cell(cell_id, data) → ServiceResult    │ │
│   │    - Актуализира конкретна клетка                     │ │
│   │    - Endpoint: GLUE_CELL_UPDATE                       │ │
│   │    - Примери:                                          │ │
│   │      • {cell_id: 1, "capacity": 10000}                │ │
│   │      • {cell_id: 2, "calibration": {...}}             │ │
│   │      • {cell_id: 3, "measurement": {...}}             │ │
│   └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                    ↓ (send_request)
┌──────────────────────────────────────────────────────────────┐
│           Communication Layer                                 │
│  RequestSender → SettingsDispatcher                          │
│   - handle_glue_cells_settings()                             │
│   - Маршрутизира към съответния endpoint                     │
└──────────────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────┐
│                Repository Layer                               │
│  Settings Repository                                          │
│   - Чете/Пише glue_cell_config.json                         │
│   - Валидация на данни                                        │
│   - Persistence                                               │
└──────────────────────────────────────────────────────────────┘
```
---
## Актуализирани Методи в GlueCellSettingsTabLayout
### 1. Mode Toggle (Test/Production)
```python
def on_mode_changed(self, state):
    """Превключване на режим чрез SettingsService"""
    try:
        # Получаване на SettingsService
        controller = self.controller_service.get_controller()
        settings_service = controller.controller_service.settings
        # Определяне на новия режим
        new_mode = "test" if state else "production"
        # Актуализация чрез SettingsService
        result = settings_service.update_glue_cells_config({"MODE": new_mode})
        if result.success:
            # Актуализация на UI
            if state:
                self.mode_label.setText("Test (Mock Server)")
                self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #FF8C00; }")
            else:
                self.mode_label.setText("Production")
                self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #2E8B57; }")
            # Презареждане на data fetcher
            if self.glue_data_fetcher:
                self.glue_data_fetcher.reload_config()
                self.showToast("Режимът е променен успешно")
        else:
            raise Exception(result.message)
    except Exception as e:
        print(f"Грешка при промяна на режима: {e}")
        self.showToast(f"Грешка: {e}")
```
### 2. Cell Property Update
```python
def _update_cell_config(self, key, value):
    """Актуализация на cell property чрез SettingsService"""
    try:
        # Актуализация в паметта
        if self.current_cell in self.cell_configs:
            self.cell_configs[self.current_cell][key] = value
        # Получаване на SettingsService
        controller = self.controller_service.get_controller()
        settings_service = controller.controller_service.settings
        # Актуализация чрез SettingsService
        result = settings_service.update_glue_cell(
            self.current_cell,
            {key: value}
        )
        if not result.success:
            print(f"[Config] Грешка при актуализация на {key}: {result.message}")
    except Exception as e:
        print(f"[Config] Грешка: {e}")
```
### 3. Calibration Settings Update
```python
def _update_cell_calibration(self, key, value):
    """Актуализация на калибрация чрез SettingsService"""
    try:
        # Актуализация в паметта
        if self.current_cell in self.cell_configs:
            self.cell_configs[self.current_cell][key] = value
        # Получаване на SettingsService
        controller = self.controller_service.get_controller()
        settings_service = controller.controller_service.settings
        # Актуализация с nested структура
        result = settings_service.update_glue_cell(
            self.current_cell,
            {"calibration": {key: value}}
        )
        if not result.success:
            print(f"[Config] Грешка при калибрация {key}: {result.message}")
    except Exception as e:
        print(f"[Config] Грешка: {e}")
```
### 4. Measurement Settings Update
```python
def _update_cell_measurement(self, key, value):
    """Актуализация на measurement настройки чрез SettingsService"""
    try:
        # Актуализация в паметта
        if self.current_cell in self.cell_configs:
            self.cell_configs[self.current_cell][key] = value
        # Получаване на SettingsService
        controller = self.controller_service.get_controller()
        settings_service = controller.controller_service.settings
        # Актуализация с nested структура
        result = settings_service.update_glue_cell(
            self.current_cell,
            {"measurement": {key: value}}
        )
        if not result.success:
            print(f"[Config] Грешка при измерване {key}: {result.message}")
    except Exception as e:
        print(f"[Config] Грешка: {e}")
```
---
## Endpoints (Актуализирани)
### Glue Cells Configuration Endpoints
| Endpoint | Метод | Данни | Описание |
|----------|-------|-------|----------|
| `GLUE_CELLS_CONFIG_GET` | GET | - | Зареждане на пълна конфигурация |
| `GLUE_CELLS_CONFIG_SET` | POST | `{"MODE": "test"}` | Актуализация на глобални настройки |
| `GLUE_CELL_UPDATE` | POST | `{"cell_id": 1, "capacity": 10000}` | Актуализация на конкретна клетка |
| `GLUE_CELL_UPDATE` | POST | `{"cell_id": 1, "calibration": {...}}` | Nested калибрация |
| `GLUE_CELL_UPDATE` | POST | `{"cell_id": 1, "measurement": {...}}` | Nested измервания |
| `GLUE_CELL_CALIBRATE` | POST | `{"cell_id": 1, ...}` | Калибриране на датчик |
| `GLUE_CELL_TARE` | POST | `{"cell_id": 1}` | Tare (нулиране) |
| `GLUE_CELL_UPDATE_TYPE` | POST | `{"cell_id": 1, "type": "TypeA"}` | Промяна на glue type |
---
## Ползи от Новата Архитектура
### 1. ✅ Архитектурна Консистентност
- Следва същия pattern като Camera Settings, Robot Settings, Modbus Settings
- Всички настройки минават през SettingsService
- Няма директно манипулиране на файлове в UI кода
### 2. ✅ Separation of Concerns
- UI се грижи само за user interaction
- Service layer обработва бизнес логиката
- Repository layer управлява persistence
### 3. ✅ Testability
- Може да се mock-ва SettingsService за UI тестове
- Service логиката може да се тества независимо
- Няма file I/O в UI тестовете
### 4. ✅ Error Handling
- Централизирано обработване на грешки в service layer
- ServiceResult дава консистентни съобщения за грешки
- По-лесно добавяне на валидация
### 5. ✅ Maintainability
- Един източник на истина за settings операции
- Промени в storage формата засягат само repository
- Ясни отговорности
---
## Миграционни Забележки
### Как да Добавим Нова Настройка
1. **Добавяне на UI control** в GlueCellSettingsTabLayout
2. **Използване на съществуващ метод:**
   ```python
   self._update_cell_config("new_property", value)
   # ИЛИ за nested:
   self._update_cell_calibration("new_cal_property", value)
   self._update_cell_measurement("new_measurement", value)
   ```
3. **Не са нужни нови service методи** - съществуващите обработват всички случаи!
### Pattern за Следване
```python
# ❌ НЕ ПРАВЕТЕ ТАКА
with open(config_path, 'w') as f:
    json.dump(data, f)
# ✅ ПРАВЕТЕ ТАКА
controller = self.controller_service.get_controller()
settings_service = controller.controller_service.settings
result = settings_service.update_glue_cell(cell_id, data)
if result.success:
    # Успех
else:
    # Обработка на грешка: result.message
```
---
## Архитектурен Pattern
### Сравнение: Стар vs Нов
| Аспект | Стар Подход ❌ | Нов Подход ✅ |
|--------|----------------|---------------|
| **File Access** | Директно от UI | Само през Repository |
| **Data Flow** | UI → JSON file | UI → Service → API → Repository → JSON |
| **Error Handling** | В UI | В Service layer |
| **Testing** | Трудно (file I/O) | Лесно (mock service) |
| **Consistency** | Различен от други settings | Същият като всички settings |
| **Maintainability** | Ниска | Висока |
---
## Заключение на Актуализацията
✅ **Архитектурата е Фиксирана** - Няма повече директно писане в JSON  
✅ **Консистентен Pattern** - Съответства на останалата част от приложението  
✅ **Правилно Layering** - UI → Service → API → Repository  
✅ **Чист Код** - SOLID принципи спазени  
✅ **Maintainable** - Лесно за разширяване и тестване  
Glue Cell Settings сега следва същата чиста архитектура като Camera Settings, Robot Settings и Modbus Settings! 🎉
**Дата на актуализация:** 10 Декември 2025  
**Статус:** ✅ Завършено  
**Breaking Changes:** Няма (backward compatible)
---
## 🔄 ДОПЪЛНИТЕЛНА АКТУАЛИЗАЦИЯ (Декември 2025) - Коректен Достъп до SettingsService
### Проблем: Грешен Достъп до SettingsService
**Грешка:**
```
AttributeError: 'UIController' object has no attribute 'services'
```
**Причина:**
Кодът опитваше да достъпи SettingsService през UIController:
```python
# ❌ ГРЕШНО
controller = self.controller_service.get_controller()  # Връща UIController
settings_service = controller.services.settings  # UIController няма 'services'
```
### Решение: Директен Достъп
`GlueCellSettingsTabLayout` получава `ControllerService`, който вече има директен достъп до всички services:
```python
# ✅ ПРАВИЛНО - Директен достъп
settings_service = self.controller_service.settings
```
### Актуализирана Архитектура
```
GlueCellSettingsTabLayout
  ↓ получава при инициализация
controller_service (ControllerService)
  ↓ има директни атрибути
  .settings → SettingsService
  .robot → RobotService
  .camera → CameraService
  .workpiece → WorkpieceService
  .operations → OperationsService
  .auth → AuthService
```
### Актуализирани Методи (Финална Версия)
#### 1. on_mode_changed() - Превключване на режим
```python
def on_mode_changed(self, state):
    """Превключване на режим чрез SettingsService"""
    try:
        new_mode = "test" if state else "production"
        # ✅ Директен достъп до SettingsService
        settings_service = self.controller_service.settings
        result = settings_service.update_glue_cells_config({"MODE": new_mode})
        if result.success:
            # Актуализация на UI
            if state:
                self.mode_label.setText("Test (Mock Server)")
            else:
                self.mode_label.setText("Production")
            if self.glue_data_fetcher:
                self.glue_data_fetcher.reload_config()
                self.showToast("Режимът е променен успешно")
        else:
            raise Exception(result.message)
    except Exception as e:
        print(f"Грешка при промяна на режима: {e}")
        self.showToast(f"Грешка: {e}")
```
#### 2. _update_cell_config() - Актуализация на свойства
```python
def _update_cell_config(self, key, value):
    """Актуализация на cell property чрез SettingsService"""
    try:
        # Актуализация в паметта
        if self.current_cell in self.cell_configs:
            self.cell_configs[self.current_cell][key] = value
        # ✅ Директен достъп до SettingsService
        settings_service = self.controller_service.settings
        result = settings_service.update_glue_cell(
            self.current_cell,
            {key: value}
        )
        if not result.success:
            print(f"[Config] Грешка: {result.message}")
    except Exception as e:
        print(f"[Config] Грешка: {e}")
```
#### 3. _update_cell_calibration() - Актуализация на калибрация
```python
def _update_cell_calibration(self, key, value):
    """Актуализация на калибрация чрез SettingsService"""
    try:
        if self.current_cell in self.cell_configs:
            self.cell_configs[self.current_cell][key] = value
        # ✅ Директен достъп до SettingsService
        settings_service = self.controller_service.settings
        result = settings_service.update_glue_cell(
            self.current_cell,
            {"calibration": {key: value}}
        )
        if not result.success:
            print(f"[Config] Грешка при калибрация: {result.message}")
    except Exception as e:
        print(f"[Config] Грешка: {e}")
```
#### 4. _update_cell_measurement() - Актуализация на измервания
```python
def _update_cell_measurement(self, key, value):
    """Актуализация на measurement настройки чрез SettingsService"""
    try:
        if self.current_cell in self.cell_configs:
            self.cell_configs[self.current_cell][key] = value
        # ✅ Директен достъп до SettingsService
        settings_service = self.controller_service.settings
        result = settings_service.update_glue_cell(
            self.current_cell,
            {"measurement": {key: value}}
        )
        if not result.success:
            print(f"[Config] Грешка при измерване: {result.message}")
    except Exception as e:
        print(f"[Config] Грешка: {e}")
```
---
## API Формат: Коректна Структура на Данните
### SettingsService.update_glue_cell()
Методът преобразува данните в правилния API формат:
**Вход (от UI):**
```python
# Простo поле
settings_service.update_glue_cell(2, {"type": "TEST TYPE 2"})
# Nested поле
settings_service.update_glue_cell(1, {"calibration": {"zero_offset": 22.5}})
```
**Изход (към API):**
```python
# API очаква: {"cell_id": X, "field": "fieldname", "value": value}
# За просто поле
{
    "cell_id": 2,
    "field": "type",
    "value": "TEST TYPE 2"
}
# За nested поле
{
    "cell_id": 1,
    "field": "calibration",
    "value": {"zero_offset": 22.5}
}
```
### Имплементация в SettingsService
```python
def update_glue_cell(self, cell_id: int, cell_data: dict) -> ServiceResult:
    """
    Актуализация на конфигурация на glue cell.
    Преобразува cell_data в API формат (field/value pairs).
    """
    try:
        print(f"[SettingsService] Updating cell {cell_id}: {cell_data}")
        # API очаква: {"cell_id": X, "field": "fieldname", "value": value}
        # Преобразуваме всяко поле в отделна заявка
        for field, value in cell_data.items():
            request_data = {
                "cell_id": cell_id,
                "field": field,
                "value": value
            }
            response_dict = self.controller.requestSender.send_request(
                glue_endpoints.GLUE_CELL_UPDATE,
                data=request_data
            )
            response = Response.from_dict(response_dict)
            if response.status != Constants.RESPONSE_STATUS_SUCCESS:
                return ServiceResult.error_result(
                    f"Failed to update cell {cell_id}: {response.message}"
                )
        return ServiceResult.success_result(
            f"Cell {cell_id} updated successfully",
            data={"cell_id": cell_id, **cell_data}
        )
    except Exception as e:
        return ServiceResult.error_result(f"Failed to update: {str(e)}")
```
---
## Пълен Поток на Данните (Финален)
```
┌─────────────────────────────────────────────────────────────┐
│  GlueCellSettingsTabLayout                                  │
│  Потребителят променя "Glue Type" на Cell 2                │
│  _update_cell_config("type", "TEST TYPE 2")                 │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  settings_service = self.controller_service.settings        │
│  ✅ Директен достъп до SettingsService                      │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  SettingsService.update_glue_cell(2, {"type": "TEST TYPE 2"})│
│  Преобразува в API формат                                   │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  API Request: GLUE_CELL_UPDATE                              │
│  Data: {                                                    │
│    "cell_id": 2,                                            │
│    "field": "type",                                         │
│    "value": "TEST TYPE 2"                                   │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  SettingsDispatcher                                         │
│  handle_glue_cells_settings()                               │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  SettingsController                                         │
│  Валидира: cell_id, field, value                           │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  SettingsRepository                                         │
│  Зарежда glue_cell_config.json                             │
│  Намира cell с id=2                                         │
│  Актуализира: cell["type"] = "TEST TYPE 2"                 │
│  Записва обратно в JSON файл                                │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  Response: {"status": "success"}                            │
│  ServiceResult: result.success = True                       │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  UI актуализира in-memory config                           │
│  Toast notification: "Cell 2 glue type changed"            │
└─────────────────────────────────────────────────────────────┘
```
---
## Ключови Точки
### 1. ✅ Директен Достъп до Services
```python
# ControllerService има директни атрибути
self.controller_service.settings  # SettingsService
self.controller_service.robot     # RobotService
self.controller_service.camera    # CameraService
```
### 2. ✅ Коректен API Формат
```python
# API винаги очаква:
{
    "cell_id": int,
    "field": str,
    "value": any
}
```
### 3. ✅ SettingsService Преобразува Данните
```python
# UI изпраща просто:
{"type": "TEST TYPE 2"}
# SettingsService преобразува в:
{"cell_id": 2, "field": "type", "value": "TEST TYPE 2"}
```
### 4. ✅ Поддръжка на Nested Структури
```python
# UI изпраща:
{"calibration": {"zero_offset": 22.5}}
# SettingsService изпраща като:
{"cell_id": 1, "field": "calibration", "value": {"zero_offset": 22.5}}
```
---
## Заключение на Финалната Версия
✅ **Коректен Достъп** - Директно през `self.controller_service.settings`  
✅ **Правилен API Формат** - `field/value` структура  
✅ **Автоматично Преобразуване** - SettingsService управлява форматирането  
✅ **Поддръжка на Nested** - Калибрация и измервания работят коректно  
✅ **Опростена Архитектура** - Без излишни междинни слоеве  
Glue Cell Settings сега използва правилната архитектура с директен достъп до SettingsService и коректен API формат! 🎉
**Дата на финалната актуализация:** 10 Декември 2025  
**Статус:** ✅ Напълно Фиксирано  
**Breaking Changes:** Няма
