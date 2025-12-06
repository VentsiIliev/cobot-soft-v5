# Controller Service Usage Examples

This document shows how to use the new clean service architecture - no callbacks, no global state!

## 🚀 Basic Setup

```python
# In main application startup:
from frontend.core.services import ControllerService

controller = Controller(request_sender)
service = ControllerService(controller)

# In UI components - inject the service:
widget = SomeAppWidget(parent, controller_service=service)
```

## 🔧 Settings Service Examples

### Update Settings (Clean Pattern)
```python
# Before (callback mess):
def updateSettingsCallback(key, value, className):
    try:
        self.controller.updateSettings(key, value, className)
    except Exception as e:
        print(f"ERROR: {e}")

# After (clean & explicit):
result = self.service.settings.update_setting(key, value, className)
if result:
    self.show_success(f"✅ {result.message}")
else:
    self.show_error(f"❌ {result.message}")
```

### Load All Settings
```python
result = self.service.settings.get_all_settings()
if result:
    settings_data = result.data
    self.update_ui_with_settings(settings_data)
else:
    self.show_error(f"Failed to load settings: {result.message}")
```

## 🤖 Robot Service Examples

### Move Robot Home
```python
result = self.service.robot.move_to_home()
if result:
    self.show_success("Robot homed successfully!")
else:
    self.show_error(f"Failed to home robot: {result.message}")
```

### Jog Robot
```python
result = self.service.robot.jog_robot("x", "+", 10.0)
if result:
    print(f"Robot moved: {result.message}")
else:
    print(f"Movement failed: {result.message}")
```

### Robot Calibration
```python
result = self.service.robot.calibrate_robot()
if result:
    self.show_calibration_success(result.message)
else:
    self.show_calibration_error(result.message)
```

## 📷 Camera Service Examples

### Get Camera Frame
```python
result = self.service.camera.get_latest_frame()
if result:
    frame = result.data
    self.display_frame(frame)
else:
    print(f"No frame available: {result.message}")
```

### Toggle Raw Mode
```python
# Enable raw mode
result = self.service.camera.enable_raw_mode()
if result:
    print("Raw mode enabled")

# Disable raw mode  
result = self.service.camera.disable_raw_mode()
if result:
    print("Raw mode disabled")
```

### Camera Calibration
```python
result = self.service.camera.calibrate_camera()
if result:
    self.show_success(f"Camera calibrated: {result.message}")
else:
    self.show_error(f"Calibration failed: {result.message}")
```

## 📋 Workpiece Service Examples

### Get All Workpieces
```python
result = self.service.workpiece.get_all_workpieces()
if result:
    workpieces = result.data
    self.populate_workpiece_list(workpieces)
    print(f"Loaded {len(workpieces)} workpieces")
else:
    self.show_error(f"Failed to load workpieces: {result.message}")
```

### Delete Workpiece
```python
result = self.service.workpiece.delete_workpiece(workpiece_id)
if result:
    self.refresh_workpiece_list()
    self.show_success("Workpiece deleted successfully")
else:
    self.show_error(f"Delete failed: {result.message}")
```

### Create Workpiece
```python
# Step 1
result = self.service.workpiece.create_workpiece_step1()
if result:
    print("Step 1 completed, proceed to step 2")
    
    # Step 2
    result = self.service.workpiece.create_workpiece_step2()
    if result:
        step2_data = result.data
        self.process_step2_data(step2_data)
```

## ⚙️ Operations Service Examples

### Control Operations
```python
# Start operation
result = self.service.operations.start()
if result:
    self.update_operation_status("Running")

# Pause operation
result = self.service.operations.pause()
if result:
    self.update_operation_status("Paused")

# Stop operation
result = self.service.operations.stop()
if result:
    self.update_operation_status("Stopped")
```

### Demo Operations
```python
# Run demo
result = self.service.operations.run_demo()
if result:
    self.show_demo_started()
else:
    self.show_error(f"Demo failed to start: {result.message}")

# Stop demo
result = self.service.operations.stop_demo()
if result:
    self.show_demo_stopped()
```

## 🔐 Auth Service Examples

### User Login
```python
result = self.service.auth.login(username, password)
if result:
    user_data = result.data
    self.handle_successful_login(user_data)
    self.show_success(f"Welcome {user_data['username']}!")
else:
    self.show_login_error(result.message)
```

### QR Login
```python
result = self.service.auth.qr_login()
if result:
    qr_data = result.data
    self.display_qr_code(qr_data)
else:
    self.show_error(f"QR login failed: {result.message}")
```

## 💡 Best Practices

### 1. Always Check Results
```python
# ✅ Good - always check the result
result = service.some_operation()
if result:
    # Handle success
    process_data(result.data)
else:
    # Handle failure
    show_error(result.message)

# ❌ Bad - don't ignore results
service.some_operation()  # What if it fails?
```

### 2. Use Data from Results
```python
# ✅ Good - use the returned data
result = service.get_something()
if result:
    data = result.data
    if data:
        process_data(data)

# ❌ Bad - don't assume data exists
result = service.get_something()
process_data(result.data)  # What if data is None?
```

### 3. Handle Specific Error Cases
```python
result = service.robot.jog_robot("invalid_axis", "+", 10)
if result:
    print("Movement successful")
else:
    if "Invalid axis" in result.message:
        self.show_axis_selection_dialog()
    else:
        self.show_generic_error(result.message)
```

### 4. Dependency Injection in UI Components
```python
class MyAppWidget(AppWidget):
    def __init__(self, parent=None, controller_service=None):
        # Always accept the service as a parameter
        self.service = controller_service
        super().__init__("My App", parent)
    
    def some_action(self):
        # Use the injected service
        result = self.service.operations.start()
        if result:
            self.update_ui_success()
```

## 🎯 Key Benefits

1. **No Callbacks** - Just clean method calls with explicit results
2. **No Global State** - Services are passed explicitly where needed  
3. **Type Safety** - Clear method signatures and return types
4. **Error Handling** - Consistent error responses across all operations
5. **Testing** - Easy to mock individual services
6. **Debugging** - Clear logging and error tracing

This architecture makes the codebase much more maintainable and easier to understand!