# Modbus Device Registry Implementation Plan

## Overview

Implement a **Modbus Device Registry** system that manages device configurations for Motors, Generators, Fans, and Lasers. The registry provides a centralized configuration layer that existing device controllers (MotorControl, GeneratorControl, FanControl) can query instead of using hardcoded values.

### Key Design Decisions
- **Registry as Configuration Layer**: Devices query registry for config, minimal refactoring required
- **Predefined Templates**: Each device type (Motor, Generator, Fan, Laser) has fixed register schemas
- **Multi-Instance Support**: Multiple devices of same type with unique IDs and slave addresses
- **UI-Based Registration**: Users manage devices via ModbusDevicesTab with add/edit dialogs
- **Backward Compatible**: Controllers fallback to hardcoded values if registry is empty

---

## Architecture

```
UI Layer (ModbusDevicesTab + AddDeviceDialog)
    ↓ controller_service.settings
SettingsService (add/remove/update/get devices)
    ↓ RequestSender
API Dispatcher (handle_modbus_devices)
    ↓ Repository
ModbusDeviceRegistryRepository
    ↓ JSON Storage
modbus_devices.json
```

---

## Phase 1: Data Models

### 1.1 Device Type Enum
**New File**: `src/core/model/settings/modbusConfig/ModbusDeviceType.py`

```python
class ModbusDeviceType(Enum):
    MOTOR = "motor"
    GENERATOR = "generator"
    FAN = "fan"
    LASER = "laser"  # Future support
```

### 1.2 Device Configuration Model
**New File**: `src/core/model/settings/modbusConfig/ModbusDeviceConfig.py`

```python
@dataclass
class ModbusDeviceConfig:
    device_id: str           # Unique ID (e.g., "motor_1", "generator_1")
    device_type: str         # "motor", "generator", "fan", "laser"
    slave_id: int            # Modbus slave address
    base_address: Optional[int]  # For motors (0, 2, 4, 6)
    name: Optional[str]      # Human-readable name
    enabled: bool            # Whether device is active
    metadata: Dict[str, Any] # Additional device-specific config
```

### 1.3 Register Templates
**New File**: `src/core/model/settings/modbusConfig/DeviceRegisterTemplate.py`

```python
@dataclass
class RegisterDefinition:
    address: int
    name: str
    description: str
    access: str  # "read", "write", "read_write"
    data_type: str  # "uint16", "int32", "float32", "bool"
    default_value: Optional[Any]

@dataclass
class DeviceRegisterTemplate:
    device_type: str
    description: str
    registers: List[RegisterDefinition]
    requires_base_address: bool  # For motors
    default_slave_id: int
```

### 1.4 Device Templates Definition
**New File**: `src/core/model/settings/modbusConfig/DeviceTemplates.py`

Predefined templates for each device type:
- **Motor**: Registers 0,1 (speed), 17 (health check), 20 (error count), 21+ (errors)
- **Generator**: Register 9 (relay), 10 (state), 11 (error)
- **Fan**: Register 8 (speed control)
- **Laser**: Registers 100-102 (future support)

### 1.5 Registry Container
**New File**: `src/core/model/settings/modbusConfig/ModbusDevicesRegistry.py`

```python
@dataclass
class ModbusDevicesRegistry:
    devices: List[ModbusDeviceConfig]
    version: str = "1.0"

    # Methods: add_device, remove_device, get_device_by_id,
    # get_devices_by_type, update_device, device_exists
```

---

## Phase 2: Repository Layer

**New File**: `src/core/database/settings/ModbusDeviceRegistryRepository.py`

Extends `BaseJsonSettingsRepository[ModbusDevicesRegistry]` following existing pattern.

**Storage**: `~/.cache/cobot-glue-dispensing-v5/glue_dispensing_application/storage/settings/modbus_devices.json`

**JSON Structure**:
```json
{
  "version": "1.0",
  "devices": [
    {
      "device_id": "motor_1",
      "device_type": "motor",
      "slave_id": 1,
      "base_address": 0,
      "name": "Glue Pump Motor 1",
      "enabled": true,
      "metadata": {}
    }
  ]
}
```

---

## Phase 3: API & Service Layer

### 3.1 API Endpoints
**Modify**: `src/communication_layer/api/v1/endpoints/modbus_endpoints.py`

Add endpoints:
```python
MODBUS_DEVICES_GET = "/api/v1/settings/modbus/devices"
MODBUS_DEVICE_ADD = "/api/v1/settings/modbus/devices/add"
MODBUS_DEVICE_REMOVE = "/api/v1/settings/modbus/devices/remove"
MODBUS_DEVICE_UPDATE = "/api/v1/settings/modbus/devices/update"
MODBUS_DEVICE_GET_BY_ID = "/api/v1/settings/modbus/devices/get"
MODBUS_DEVICE_TEMPLATES_GET = "/api/v1/settings/modbus/devices/templates"
```

### 3.2 Settings Dispatcher
**Modify**: `src/communication_layer/api_gateway/dispatch/settings_dispatcher.py`

Add method `handle_modbus_devices(parts, request, data)` implementing:
- GET all devices
- ADD device (validate no duplicate device_id)
- REMOVE device by ID
- UPDATE device fields
- GET single device by ID
- GET all templates

Update `dispatch()` method to route device registry requests.

### 3.3 Settings Service
**Modify**: `src/frontend/core/services/domain/SettingsService.py`

Add methods:
```python
def get_modbus_devices() -> ServiceResult
def add_modbus_device(device_data: dict) -> ServiceResult
def remove_modbus_device(device_id: str) -> ServiceResult
def update_modbus_device(device_id: str, updates: dict) -> ServiceResult
def get_modbus_device_templates() -> ServiceResult
```

All methods follow existing pattern: call RequestSender, wrap Response in ServiceResult.

---

## Phase 4: UI Layer

### 4.1 Add Device Dialog
**New File**: `src/plugins/core/modbus_settings_plugin/ui/AddModbusDeviceDialog.py`

Features:
- Form fields: Device ID, Device Type (dropdown), Display Name, Slave ID, Base Address (conditional)
- Device type dropdown triggers template info display
- Base Address field shown only for motors (requires_base_address)
- Edit mode: Device ID is read-only
- Validation: Device ID required

### 4.2 Update Devices Tab
**Modify**: `src/plugins/core/modbus_settings_plugin/ui/ModbusDevicesTab.py`

Replace placeholder implementation with:
- Load devices via `controller_service.settings.get_modbus_devices()`
- Load templates via `controller_service.settings.get_modbus_device_templates()`
- Table columns: Device ID, Type, Name, Slave ID, Base Addr, Status (Enabled/Disabled)
- Buttons: Add Device, Edit Device, Remove Device, Refresh
- Add: Opens AddModbusDeviceDialog, calls `add_modbus_device()`
- Edit: Opens dialog with existing data, calls `update_modbus_device()`
- Remove: Confirmation dialog, calls `remove_modbus_device()`
- Double-click row to edit

---

## Phase 5: Integration with Existing Controllers

### 5.1 Device Registry Helper
**New File**: `src/modules/modbusCommunication/ModbusDeviceRegistryHelper.py`

Singleton helper providing:
```python
def get_motors() -> List[ModbusDeviceConfig]
def get_motor_by_address(base_address) -> Optional[ModbusDeviceConfig]
def get_motor_addresses() -> List[int]
def get_generators() -> List[ModbusDeviceConfig]
def get_first_generator() -> Optional[ModbusDeviceConfig]
def get_fans() -> List[ModbusDeviceConfig]
def get_first_fan() -> Optional[ModbusDeviceConfig]
def has_devices() -> bool
```

### 5.2 Update MotorControl
**Modify**: `src/applications/glue_dispensing_application/services/glueSprayService/motorControl/MotorControl.py`

In `__init__`:
```python
self.motor_addresses = self._load_motor_addresses()

def _load_motor_addresses():
    helper = ModbusDeviceRegistryHelper.get_instance()
    addresses = helper.get_motor_addresses()
    if addresses:
        return sorted(addresses)
    else:
        # Fallback to hardcoded
        return [0, 2, 4, 6]
```

Update `getAllMotorStates()` to use `self.motor_addresses` instead of hardcoded list.

### 5.3 Update GeneratorControl
**Modify**: `src/applications/glue_dispensing_application/services/glueSprayService/generatorControl/GeneratorControl.py`

In `__init__`:
```python
generator_config = self._load_generator_config()
if generator_config:
    self.generator_relay_address = generator_config['relay_address']
    self.relaysId = generator_config['slave_id']
else:
    # Fallback to parameters
    self.generator_relay_address = generator_address
    self.relaysId = generator_id

def _load_generator_config():
    helper = ModbusDeviceRegistryHelper.get_instance()
    generator = helper.get_first_generator()
    if generator:
        return {
            'slave_id': generator.slave_id,
            'relay_address': generator.metadata.get('relay_address', 9)
        }
    return None
```

### 5.4 Update FanControl
**Modify**: `src/applications/glue_dispensing_application/services/glueSprayService/fanControl/fanControl.py`

Similar pattern to GeneratorControl:
```python
fan_config = self._load_fan_config()
if fan_config:
    self.fanId = fan_config['slave_id']
    self.fanSpeed_address = fan_config['speed_address']
else:
    # Fallback to parameters
    self.fanId = fanSlaveId
    self.fanSpeed_address = fanSpeed_address
```

---

## Phase 6: Migration & Testing

### 6.1 Initial Registry Population

Create initial `modbus_devices.json` with current hardcoded config:
```json
{
  "version": "1.0",
  "devices": [
    {"device_id": "motor_cell1", "device_type": "motor", "slave_id": 1, "base_address": 0, "name": "Glue Cell 1 Motor", "enabled": true},
    {"device_id": "motor_cell2", "device_type": "motor", "slave_id": 1, "base_address": 2, "name": "Glue Cell 2 Motor", "enabled": true},
    {"device_id": "motor_cell3", "device_type": "motor", "slave_id": 1, "base_address": 4, "name": "Glue Cell 3 Motor", "enabled": true},
    {"device_id": "generator_main", "device_type": "generator", "slave_id": 1, "name": "Main HV Generator", "enabled": true, "metadata": {"relay_address": 9}},
    {"device_id": "fan_exhaust", "device_type": "fan", "slave_id": 1, "name": "Exhaust Fan", "enabled": true, "metadata": {"speed_address": 8}}
  ]
}
```

### 6.2 Testing Checklist
- [ ] Unit tests for data models (ModbusDeviceConfig, ModbusDevicesRegistry, templates)
- [ ] Repository load/save operations
- [ ] API endpoint CRUD operations
- [ ] UI add/edit/remove workflows
- [ ] Device controller initialization from registry
- [ ] Fallback to hardcoded values when registry empty
- [ ] Multi-instance scenarios (6 motors, 2 generators)
- [ ] End-to-end testing

---

## Implementation Checklist

### Phase 1: Data Models (2-3 hours)
- [ ] `ModbusDeviceType.py` - Device type enum
- [ ] `DeviceRegisterTemplate.py` - Register definitions
- [ ] `ModbusDeviceConfig.py` - Device instance config
- [ ] `ModbusDevicesRegistry.py` - Registry container with CRUD methods
- [ ] `DeviceTemplates.py` - Predefined templates for Motor/Generator/Fan/Laser
- [ ] Unit tests for models

### Phase 2: Repository (1-2 hours)
- [ ] `ModbusDeviceRegistryRepository.py` - JSON storage repository
- [ ] Test load/save operations
- [ ] Create initial `modbus_devices.json`

### Phase 3: API & Service (2-3 hours)
- [ ] Add endpoints to `modbus_endpoints.py`
- [ ] Implement `handle_modbus_devices()` in `settings_dispatcher.py`
- [ ] Update dispatcher routing
- [ ] Add 5 methods to `SettingsService.py`
- [ ] Test API endpoints

### Phase 4: UI (3-4 hours)
- [ ] `AddModbusDeviceDialog.py` - Add/edit dialog
- [ ] Update `ModbusDevicesTab.py` - Table view and CRUD operations
- [ ] Test dialog validation
- [ ] Test add/edit/remove workflows

### Phase 5: Controller Integration (2-3 hours)
- [ ] `ModbusDeviceRegistryHelper.py` - Query helper
- [ ] Update `MotorControl.__init__()` - Load from registry
- [ ] Update `GeneratorControl.__init__()` - Load from registry
- [ ] Update `FanControl.__init__()` - Load from registry
- [ ] Test backward compatibility

### Phase 6: Testing (2-3 hours)
- [ ] Integration tests
- [ ] Multi-instance scenarios
- [ ] Fallback behavior testing
- [ ] End-to-end validation

**Total Estimated Time**: 12-18 hours

---

## Critical Files Summary

### New Files (8 files)
1. `src/core/model/settings/modbusConfig/ModbusDeviceType.py`
2. `src/core/model/settings/modbusConfig/DeviceRegisterTemplate.py`
3. `src/core/model/settings/modbusConfig/ModbusDeviceConfig.py`
4. `src/core/model/settings/modbusConfig/ModbusDevicesRegistry.py`
5. `src/core/model/settings/modbusConfig/DeviceTemplates.py`
6. `src/core/database/settings/ModbusDeviceRegistryRepository.py`
7. `src/plugins/core/modbus_settings_plugin/ui/AddModbusDeviceDialog.py`
8. `src/modules/modbusCommunication/ModbusDeviceRegistryHelper.py`

### Modified Files (6 files)
1. `src/communication_layer/api/v1/endpoints/modbus_endpoints.py` - Add 6 endpoints
2. `src/communication_layer/api_gateway/dispatch/settings_dispatcher.py` - Add handle_modbus_devices()
3. `src/frontend/core/services/domain/SettingsService.py` - Add 5 methods
4. `src/plugins/core/modbus_settings_plugin/ui/ModbusDevicesTab.py` - Full implementation
5. `src/applications/glue_dispensing_application/services/glueSprayService/motorControl/MotorControl.py` - Add registry loading
6. `src/applications/glue_dispensing_application/services/glueSprayService/generatorControl/GeneratorControl.py` - Add registry loading
7. `src/applications/glue_dispensing_application/services/glueSprayService/fanControl/fanControl.py` - Add registry loading

---

## Benefits

✅ **Centralized Device Management**: Single source of truth for device configurations
✅ **Flexible Scaling**: Easy to add new motors, generators, or fans via UI
✅ **Type Safety**: Predefined templates prevent configuration errors
✅ **Backward Compatible**: Existing code continues to work with fallback values
✅ **Future-Ready**: Laser and other device types can be added easily
✅ **User-Friendly**: No code changes needed to reconfigure devices
✅ **Follows Existing Patterns**: Consistent with settings architecture (Repository, Service, API)
