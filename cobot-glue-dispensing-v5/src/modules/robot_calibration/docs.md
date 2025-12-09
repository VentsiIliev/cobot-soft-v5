# Robot Calibration Module - Comprehensive Documentation

**Version:** 5.0  
**Date:** December 2025  
**Module Path:** `/src/modules/robot_calibration`

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [State Machine Design](#state-machine-design)
4. [State Definitions](#state-definitions)
5. [Execution Context](#execution-context)
6. [State Flow Diagrams](#state-flow-diagrams)
7. [Transition Rules](#transition-rules)
8. [Usage Guide](#usage-guide)
9. [Configuration](#configuration)
10. [Error Handling](#error-handling)

---

## Overview

### Purpose

The Robot Calibration Module performs **camera-to-robot coordinate system calibration** using a state machine architecture. It establishes the spatial transformation between camera pixel coordinates and robot workspace coordinates by detecting visual markers (chessboard pattern and ArUco markers) and computing a homography matrix.

### What It Does

1. **Detects a chessboard pattern** to establish a reference coordinate system
2. **Maps camera axes to robot axes** (automatic axis mapping calibration)
3. **Detects multiple ArUco markers** placed at known positions on the calibration plate
4. **Iteratively aligns the robot** to center each marker in the camera view
5. **Records corresponding points** (camera coordinates ↔ robot coordinates)
6. **Computes a homography matrix** for camera-to-robot transformation
7. **Validates calibration accuracy** through reprojection error analysis

### Why It Exists

Robot vision systems need accurate spatial calibration to:
- Convert detected object positions from camera coordinates to robot workspace coordinates
- Enable precise pick-and-place operations
- Compensate for camera mounting variations
- Account for lens distortion and perspective effects
- Adapt to different robot configurations automatically

---

## Architecture

### Core Components

```
robot_calibration/
├── newRobotCalibUsingExecutableStateMachine.py   # Main pipeline orchestrator
├── RobotCalibrationContext.py                     # Execution context (state storage)
├── CalibrationVision.py                           # Computer vision algorithms
├── robot_controller.py                            # Robot motion control
├── config_helpers.py                              # Configuration dataclasses
├── states/                                        # State handler implementations
│   ├── robot_calibration_states.py               # State enum & transition rules
│   ├── state_result.py                           # State result wrapper
│   ├── initializing.py                           # INITIALIZING state
│   ├── axis_mapping.py                           # AXIS_MAPPING state
│   ├── looking_for_chessboard_handler.py         # LOOKING_FOR_CHESSBOARD state
│   ├── chessboard_found_handler.py               # CHESSBOARD_FOUND state
│   ├── looking_for_aruco_markers_handler.py      # LOOKING_FOR_ARUCO_MARKERS state
│   ├── all_aruco_found_handler.py                # ALL_ARUCO_FOUND state
│   ├── compute_offsets_handler.py                # COMPUTE_OFFSETS state
│   ├── handle_height_sample_state.py             # SAMPLE_HEIGHT state
│   └── remaining_handlers.py                     # ALIGN_ROBOT, ITERATE_ALIGNMENT, DONE, ERROR
├── metrics.py                                     # Calibration validation
├── logging.py                                     # Structured logging utilities
├── debug.py                                       # Debug visualization
└── visualizer.py                                  # Live feed visualization
```

### Design Pattern

**Executable State Machine Pattern**
- Decouples state logic from state transitions
- Each state is a pure function: `(Context) → NextState`
- Context holds all mutable state
- Transition rules are declarative and validated
- State handlers are testable in isolation

---

## State Machine Design

### Why State Machine?

The calibration process is inherently **sequential** and **condition-dependent**:
- Each step depends on the success of previous steps
- Some states may need to retry (e.g., marker detection)
- Error conditions can occur at any stage
- Clear state transitions make the process auditable

### State Machine Components

#### 1. **States (Enum)**
```python
class RobotCalibrationStates(Enum):
    INITIALIZING = auto()
    AXIS_MAPPING = auto()
    LOOKING_FOR_CHESSBOARD = auto()
    CHESSBOARD_FOUND = auto()
    LOOKING_FOR_ARUCO_MARKERS = auto()
    ALL_ARUCO_FOUND = auto()
    COMPUTE_OFFSETS = auto()
    ALIGN_ROBOT = auto()
    ITERATE_ALIGNMENT = auto()
    SAMPLE_HEIGHT = auto()
    DONE = auto()
    ERROR = auto()
```

#### 2. **Context (Shared State)**
- `RobotCalibrationContext`: Holds all calibration data, configuration, and system components
- Passed to every state handler
- Modified by state handlers to progress calibration

#### 3. **State Handlers (Functions)**
- Pure functions: `handle_<state_name>(context) → NextState`
- Read from context, perform operations, modify context, return next state
- No side effects outside context modification

#### 4. **Transition Rules (Declarative)**
- Dict mapping: `CurrentState → Set[ValidNextStates]`
- Enforced by state machine framework
- Invalid transitions raise errors

#### 5. **ExecutableStateMachine (Orchestrator)**
- Manages state transitions
- Validates transitions against rules
- Invokes state handlers
- Broadcasts state changes via message broker
- Handles timing and performance tracking

---

## State Definitions

### 1. INITIALIZING

**Purpose:** Verify camera system is ready and initialized

**Context Reads:**
- `context.system` (VisionSystem)

**Context Writes:**
- None (validation only)

**Logic:**
```python
if frame_provider is None:
    return INITIALIZING  # Stay in state, camera not ready
else:
    return AXIS_MAPPING  # Camera ready, proceed
```

**Next States:**
- `AXIS_MAPPING` (success)
- `INITIALIZING` (retry if camera not ready)

**Failure Conditions:** None (waits until camera ready)

---

### 2. AXIS_MAPPING

**Purpose:** Automatically calibrate the mapping between camera image axes and robot movement axes

**Context Reads:**
- `context.system` (camera)
- `context.calibration_vision` (marker detection)
- `context.calibration_robot_controller` (movement)

**Context Writes:**
- `context.image_to_robot_mapping` (ImageToRobotMapping object)

**Logic:**
1. Detect reference marker (ID=4) at initial position → `(x1, y1)` pixels
2. Move robot **+100mm in X axis**
3. Detect marker at new position → `(x2, y2)` pixels
4. Calculate image delta: `(Δx_img, Δy_img) = (x2-x1, y2-y1)`
5. Determine which image axis (X or Y) changed most → Robot X maps to this image axis
6. Determine direction (PLUS or MINUS) based on sign correlation
7. Move robot back to initial position
8. Move robot **-100mm in Y axis**
9. Repeat detection and analysis for Robot Y mapping
10. Create `ImageToRobotMapping` object with both axis mappings

**Example Output:**
```
Robot X: AxisMapping(image_axis=ImageAxis.X, direction=Direction.PLUS)
Robot Y: AxisMapping(image_axis=ImageAxis.Y, direction=Direction.PLUS)
```

This means:
- Robot +X → Image -X (because direction is PLUS and image moved negative)
- Robot +Y → Image -Y

**Next States:**
- `LOOKING_FOR_CHESSBOARD` (success)
- `ERROR` (if marker not found or robot movement failed)

**Failure Conditions:**
- Marker ID=4 not visible after MAX_ATTEMPTS
- Robot movement command fails
- Vision system error

---

### 3. LOOKING_FOR_CHESSBOARD

**Purpose:** Detect chessboard calibration pattern to establish reference coordinate system and calculate pixels-per-millimeter scale

**Context Reads:**
- `context.system` (camera)
- `context.calibration_vision` (chessboard detection)
- `context.chessboard_size` (pattern dimensions)
- `context.square_size_mm` (physical square size)

**Context Writes:**
- `context.calibration_vision.PPM` (pixels per millimeter)
- `context.bottom_left_chessboard_corner_px` (reference point in pixels)

**Logic:**
1. Capture camera frame
2. Call `calibration_vision.find_chessboard_and_compute_ppm(frame)`
   - Uses OpenCV `cv2.findChessboardCorners()`
   - Calculates distance between corners in pixels
   - Divides by known physical distance → PPM
3. Store bottom-left corner as reference point
4. If not found, stay in state (retry on next iteration)

**Next States:**
- `CHESSBOARD_FOUND` (pattern detected)
- `LOOKING_FOR_CHESSBOARD` (retry if not found)

**Failure Conditions:** None (retries indefinitely until found)

**Critical Data:**
- **PPM (Pixels Per Millimeter):** Conversion factor from pixel distances to real-world millimeters
- **Bottom-Left Corner:** Reference point (0,0) in chessboard coordinate system

---

### 4. CHESSBOARD_FOUND

**Purpose:** Transition state confirming chessboard detection

**Context Reads:**
- `context.chessboard_center_px`

**Context Writes:** None

**Logic:**
- Log confirmation message
- Immediately transition to next state

**Next States:**
- `LOOKING_FOR_ARUCO_MARKERS` (always)

**Failure Conditions:** None

---

### 5. LOOKING_FOR_ARUCO_MARKERS

**Purpose:** Detect all required ArUco markers in camera view

**Context Reads:**
- `context.system` (camera)
- `context.calibration_vision.required_ids` (set of marker IDs to find)
- `context.live_visualization` (display flag)

**Context Writes:**
- `context.calibration_vision.detected_ids` (set of found marker IDs)
- `context.calibration_vision.marker_top_left_corners` (dict: marker_id → (x, y) pixels)

**Logic:**
1. Flush camera buffer (discard old frames)
2. Capture fresh frame
3. Call `calibration_vision.find_required_aruco_markers(frame)`
   - Uses OpenCV `cv2.aruco.detectMarkers()`
   - Checks if all required IDs are present
4. Show live feed visualization (optional)
5. If all markers found → proceed
6. If not all found → retry

**Next States:**
- `ALL_ARUCO_FOUND` (all required markers detected)
- `LOOKING_FOR_ARUCO_MARKERS` (retry if incomplete)

**Failure Conditions:** None (retries indefinitely)

**Performance Note:** Uses background thread for non-blocking visualization

---

### 6. ALL_ARUCO_FOUND

**Purpose:** Process detected markers and convert coordinates to millimeters

**Context Reads:**
- `context.calibration_vision.marker_top_left_corners` (pixels)
- `context.calibration_vision.PPM` (conversion factor)
- `context.bottom_left_chessboard_corner_px` (reference point)

**Context Writes:**
- `context.calibration_vision.marker_top_left_corners_mm` (dict: marker_id → (x_mm, y_mm))
- `context.camera_points_for_homography` (copy of pixel coordinates)

**Logic:**
For each detected marker:
```python
x_mm = (marker_x_px - bottom_left_x_px) / PPM
y_mm = (marker_y_px - bottom_left_y_px) / PPM
```

**Next States:**
- `COMPUTE_OFFSETS` (always)

**Failure Conditions:** None (data already validated in previous state)

---

### 7. COMPUTE_OFFSETS

**Purpose:** Calculate offset of each marker from image center (in millimeters)

**Context Reads:**
- `context.calibration_vision.marker_top_left_corners_mm`
- `context.system.camera_settings` (image dimensions)
- `context.bottom_left_chessboard_corner_px`
- `context.calibration_vision.PPM`

**Context Writes:**
- `context.markers_offsets_mm` (dict: marker_id → (offset_x_mm, offset_y_mm))

**Logic:**
1. Get image center in pixels: `(width/2, height/2)`
2. Convert image center to mm relative to chessboard:
   ```python
   center_x_mm = (center_x_px - bottom_left_x_px) / PPM
   center_y_mm = (center_y_px - bottom_left_y_px) / PPM
   ```
3. For each marker, compute offset from image center:
   ```python
   offset_x_mm = marker_x_mm - center_x_mm
   offset_y_mm = marker_y_mm - center_y_mm
   ```

**Next States:**
- `ALIGN_ROBOT` (success)
- `ERROR` (if PPM or chessboard data missing)

**Failure Conditions:**
- `PPM is None` (chessboard detection failed earlier)
- `bottom_left_chessboard_corner_px is None`

**Why Offsets Matter:** These offsets tell the robot how far to move to center each marker in the camera view

---

### 8. ALIGN_ROBOT

**Purpose:** Move robot to approximately align with current marker

**Context Reads:**
- `context.required_ids` (sorted list of markers)
- `context.current_marker_id` (index into sorted list)
- `context.markers_offsets_mm` (target offsets)
- `context.image_to_robot_mapping` (axis mapping)
- `context.calibration_robot_controller` (movement)
- `context.Z_target` (target Z height)

**Context Writes:**
- `context.iteration_count = 0` (reset for new marker)

**Logic:**
1. Get current marker ID from sorted list
2. Get marker's offset from image center (in mm)
3. Apply axis mapping to convert image offsets → robot offsets:
   ```python
   robot_offset = image_to_robot_mapping.map(offset_x_mm, offset_y_mm)
   ```
4. Calculate current robot position relative to calibration position
5. Compute target position:
   ```python
   new_x = current_x + (marker_offset_x - current_offset_x)
   new_y = current_y + (marker_offset_y - current_offset_y)
   new_z = Z_target
   ```
6. Move robot to target position (blocking)
7. If movement fails, retry from previous successful position
8. Wait 1 second for stabilization

**Next States:**
- `ITERATE_ALIGNMENT` (movement successful)
- `ERROR` (movement failed after retry)

**Failure Conditions:**
- Robot movement returns non-zero error code
- Safety limits exceeded
- Robot communication failure

**Retry Logic:** If first move fails, return to last known good position, then retry

---

### 9. ITERATE_ALIGNMENT

**Purpose:** Iteratively refine robot position until marker is centered in image within threshold

**Context Reads:**
- `context.current_marker_id`
- `context.iteration_count`
- `context.max_iterations` (default: 50)
- `context.alignment_threshold_mm` (target precision)
- `context.system` (camera)
- `context.calibration_vision` (marker detection)
- `context.image_to_robot_mapping` (axis mapping)
- `context.ppm_scale` (Z-height correction factor)

**Context Writes:**
- `context.iteration_count` (incremented)
- `context.robot_positions_for_calibration[marker_id]` (on success)
- `context.calibration_error_message` (on failure)

**Logic:**
1. **Check iteration limit:**
   ```python
   if iteration_count > max_iterations:
       return ERROR  # Failed to converge
   ```

2. **Capture and detect marker:**
   - Get fresh camera frame
   - Detect specific marker using `detect_specific_marker(frame, marker_id)`
   - If not found → stay in state (retry)

3. **Compute alignment error:**
   ```python
   image_center = (width/2, height/2)
   marker_position = marker_top_left_corner_px
   offset_px = marker_position - image_center
   error_px = sqrt(offset_x² + offset_y²)
   
   # Adjust PPM for current Z-height
   adjusted_PPM = PPM * ppm_scale
   error_mm = error_px / adjusted_PPM
   ```

4. **Check if aligned:**
   ```python
   if error_mm <= alignment_threshold_mm:
       # Success! Store robot position
       robot_positions_for_calibration[marker_id] = get_current_position()
       return SAMPLE_HEIGHT  # Measure height at this position
   ```

5. **Compute corrective movement:**
   - Convert pixel offsets to mm: `offset_mm = offset_px / adjusted_PPM`
   - Apply axis mapping: `robot_offset_mm = image_to_robot_mapping.map(offset_x_mm, offset_y_mm)`
   - Calculate iterative position with adaptive scaling (see below)
   - Move robot to new position (blocking)
   - Wait for stabilization

6. **Adaptive Movement Scaling:**
   ```python
   # Scale movement based on error magnitude
   normalized_error = min(error_mm / max_error_ref, 1.0)
   step_scale = tanh(k * normalized_error)
   max_move = min_step + step_scale * (max_step - min_step)
   
   # Near target, apply damping to prevent overshoot
   if error_mm < threshold * 2:
       damping = (error_mm / (threshold * 2))²
       max_move *= max(damping, 0.05)
   
   # Derivative control (anti-overshoot)
   if has_previous_error:
       error_change = current_error - previous_error
       derivative_factor = 1.0 / (1.0 + derivative_scaling * abs(error_change))
       max_move *= derivative_factor
   ```

**Next States:**
- `ITERATE_ALIGNMENT` (not aligned yet, retry)
- `SAMPLE_HEIGHT` (aligned, measure height)
- `ERROR` (max iterations exceeded or movement failed)

**Failure Conditions:**
- `iteration_count > max_iterations` → Calibration failed, marker cannot be aligned
- Marker not detected during iteration (stays in state)
- Robot movement fails (returns ERROR)

**Performance Timing:** Tracks capture_time, detection_time, processing_time, movement_time, stability_time

---

### 10. SAMPLE_HEIGHT

**Purpose:** Measure workpiece height at current aligned position using laser detection

**Context Reads:**
- `context.height_measuring_service` (laser height sensor)
- `context.calibration_robot_controller.robot_service` (current position)

**Context Writes:**
- Measured height data (logged, not stored in context currently)

**Logic:**
1. Get current robot position `(x, y, z, rx, ry, rz)`
2. Call `height_measuring_service.measure_at(x, y)`
3. Receive `(height_mm, pixel_data)`
4. Log measurement

**Next States:**
- `DONE` (always)

**Failure Conditions:** None (measurements logged but don't affect calibration flow)

**Future Enhancement:** Store height measurements in context for surface profiling

---

### 11. DONE

**Purpose:** Manage transition between markers and final completion

**Context Reads:**
- `context.current_marker_id`
- `context.required_ids` (total marker count)

**Context Writes:**
- `context.current_marker_id` (incremented if more markers remain)

**Logic:**
```python
if current_marker_id < len(required_ids) - 1:
    current_marker_id += 1
    return ALIGN_ROBOT  # Process next marker
else:
    return DONE  # All markers complete, finalize
```

**Next States:**
- `ALIGN_ROBOT` (more markers to process)
- `DONE` (final completion - state machine stops)

**State Machine Stop Condition:**
When `DONE` is returned and all markers are processed, the main pipeline detects this and calls `state_machine.stop_execution()`

---

### 12. ERROR

**Purpose:** Handle calibration failure, log details, notify UI, stop process

**Context Reads:**
- `context.calibration_error_message` (detailed error description)
- `context.current_marker_id`
- `context.iteration_count`
- `context.robot_positions_for_calibration` (successful markers)
- `context.broadcast_events` (UI notification flag)

**Context Writes:**
- None (terminal state)

**Logic:**
1. Retrieve specific error message from context (or use default)
2. Log detailed error with context:
   - Which marker failed
   - Current iteration count
   - How many markers were successfully calibrated
3. If UI events enabled:
   - Create structured error notification JSON
   - Publish to `CALIBRATION_STOP_TOPIC` via message broker
4. Stay in ERROR state (terminal)

**Error Notification Structure:**
```json
{
  "status": "error",
  "message": "Robot movement failed during fine alignment of marker 2.",
  "details": {
    "current_marker": 2,
    "total_markers": 4,
    "successful_markers": 1,
    "iteration_count": 15,
    "max_iterations": 50
  }
}
```

**Next States:**
- `ERROR` (stays in state, state machine stops)

**When ERROR is Triggered:**
- Robot movement fails (after retries)
- Maximum iterations exceeded without convergence
- Missing critical calibration data (PPM, chessboard)
- Vision system errors
- Any unhandled exception in state handlers

---

## Execution Context

### RobotCalibrationContext

The execution context is the **shared state container** passed to every state handler. It stores all data needed during calibration.

#### System Components
```python
context.system                          # VisionSystem (camera interface)
context.height_measuring_service        # Laser height sensor
context.calibration_robot_controller    # Robot motion control wrapper
context.calibration_vision              # Computer vision algorithms
context.debug_draw                      # Debug visualization helper
context.broker                          # MessageBroker for UI events
context.state_machine                   # Reference to state machine
```

#### Configuration
```python
context.required_ids                    # Set of ArUco marker IDs to calibrate
context.chessboard_size                 # (cols, rows) tuple
context.square_size_mm                  # Physical size of chessboard squares
context.alignment_threshold_mm          # Target precision (default: 1.0mm)
context.max_iterations                  # Max refinement iterations (default: 50)
context.debug                           # Enable debug outputs
context.step_by_step                    # Pause between steps
context.live_visualization              # Show camera feed
context.broadcast_events                # Send UI notifications
```

#### Calibration State
```python
context.bottom_left_chessboard_corner_px  # Reference point (x, y) in pixels
context.chessboard_center_px              # Chessboard center (x, y) in pixels
context.markers_offsets_mm                # Dict: marker_id → (offset_x_mm, offset_y_mm)
context.current_marker_id                 # Index of current marker being aligned
context.iteration_count                   # Current refinement iteration
```

#### Z-Axis Configuration
```python
context.Z_current                       # Robot Z position at calibration start
context.Z_target                        # Target Z height during calibration
context.ppm_scale                       # Z_current / Z_target (PPM adjustment factor)
```

#### Calibration Results
```python
context.robot_positions_for_calibration  # Dict: marker_id → [x, y, z, rx, ry, rz]
context.camera_points_for_homography     # Dict: marker_id → (x_px, y_px)
context.image_to_robot_mapping           # ImageToRobotMapping (axis mapping)
```

#### Performance Tracking
```python
context.state_timings                   # Dict: state_name → [duration1, duration2, ...]
context.current_state_start_time        # Timestamp when current state started
context.total_calibration_start_time    # Timestamp when calibration began
```

#### Methods
```python
context.start_state_timer(state_name)   # Begin timing a state
context.end_state_timer()               # End timing current state
context.flush_camera_buffer()           # Discard old camera frames
context.get_current_state_name()        # Get state name string
context.to_debug_dict()                 # Serialize to dict for debugging
context.reset()                         # Reset to initial state
```

---

## State Flow Diagrams

### High-Level Calibration Flow

```
┌─────────────────┐
│  INITIALIZING   │  Wait for camera ready
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AXIS_MAPPING   │  Calibrate image-to-robot axes
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ LOOKING_FOR_CHESSBOARD  │◄─┐ Retry until found
└────────┬────────────────┘  │
         │ Found             │
         ▼                   │
┌─────────────────────┐      │
│  CHESSBOARD_FOUND   │      │ Not found
└────────┬────────────┘      │
         │                   │
         ▼                   │
┌──────────────────────────┐ │
│ LOOKING_FOR_ARUCO_MARKERS│◄┘ Retry until all found
└────────┬─────────────────┘
         │ All found
         ▼
┌─────────────────────┐
│  ALL_ARUCO_FOUND    │  Convert to mm coordinates
└────────┬────────────┘
         │
         ▼
┌─────────────────┐
│ COMPUTE_OFFSETS │  Calculate marker offsets from center
└────────┬────────┘
         │
         ▼
    ┌────────────────────────────────┐
    │   FOR EACH MARKER (Loop)       │
    │                                 │
    │  ┌──────────────┐              │
    │  │ ALIGN_ROBOT  │  Initial move│
    │  └──────┬───────┘              │
    │         │                       │
    │         ▼                       │
    │  ┌──────────────────┐          │
    │  │ ITERATE_ALIGNMENT│◄─┐       │
    │  └──────┬───────────┘  │       │
    │         │ Not aligned  │       │
    │         │ Refine move ─┘       │
    │         │ Aligned              │
    │         ▼                       │
    │  ┌──────────────┐              │
    │  │SAMPLE_HEIGHT │  Measure Z   │
    │  └──────┬───────┘              │
    │         │                       │
    │         ▼                       │
    │  ┌──────────────┐              │
    │  │     DONE     │              │
    │  └──────┬───────┘              │
    │         │                       │
    └─────────┼───────────────────────┘
              │ More markers? → ALIGN_ROBOT
              │ All done? → DONE (final)
              ▼
    ┌─────────────────┐
    │  DONE (final)   │  Compute homography, save matrix
    └─────────────────┘

         Any error
              ↓
    ┌─────────────────┐
    │      ERROR      │  Log, notify UI, stop
    └─────────────────┘
```

### Detailed Iteration Loop (Per Marker)

```
                  ┌──────────────┐
                  │ ALIGN_ROBOT  │
                  └──────┬───────┘
                         │
                         │ 1. Get marker offset from image center
                         │ 2. Apply axis mapping
                         │ 3. Calculate target position
                         │ 4. Move robot (coarse alignment)
                         │
                         ▼
                  ┌──────────────────┐
             ┌────┤ ITERATE_ALIGNMENT├────┐
             │    └──────────────────┘    │
             │                             │
             │ 1. Capture frame            │
             │ 2. Detect marker            │ Marker not found → retry
             │ 3. Calculate error_mm       │
             │                             │
             │    error_mm ≤ threshold?    │
             │           │                 │
             │          YES                │
             │           │                 │
             │           ▼                 │
             │    ┌──────────────┐        │
             │    │SAMPLE_HEIGHT │        │
             │    └──────┬───────┘        │
             │           │                 │
             │           ▼                 │
             │    ┌──────────────┐        │
             │    │     DONE     │        │ Max iterations
             │    └──────────────┘        │ exceeded?
             │                             │    │
             │                             │   YES
             │          NO                 │    │
             │           │                 │    ▼
             │           ▼                 │ ┌───────┐
             │    4. Calculate move        │ │ ERROR │
             │    5. Apply adaptive        │ └───────┘
             │       scaling               │
             │    6. Move robot ───────────┘
             │       (fine adjustment)
             │    7. Wait for stability
             │
             └──► Back to step 1 (next iteration)
```

### Decision Tree for Next State Selection

```
ITERATE_ALIGNMENT:
│
├─ iteration_count > max_iterations? ──YES──► ERROR
│                                              (calibration_error_message set)
├─ NO
│
├─ Marker detected?
│  ├─ NO ──────────────────────────────────► ITERATE_ALIGNMENT (retry)
│  │
│  └─ YES
│     │
│     └─ Calculate error_mm
│        │
│        ├─ error_mm ≤ alignment_threshold? ──YES──► SAMPLE_HEIGHT
│        │                                            (store robot position)
│        │
│        └─ NO
│           │
│           └─ Robot move successful?
│              ├─ YES ──────────────────────► ITERATE_ALIGNMENT (next iteration)
│              │
│              └─ NO ────────────────────────► ERROR
│                                              (movement failed)

SAMPLE_HEIGHT:
│
└─ Always ──────────────────────────────────► DONE

DONE:
│
├─ current_marker_id < total_markers - 1? ──YES──► ALIGN_ROBOT
│                                                   (increment current_marker_id)
│
└─ NO ──────────────────────────────────────────► DONE (final)
                                                   (stop state machine)
```

---

## Transition Rules

### Complete Transition Table

| Current State               | Valid Next States                                                     |
|----------------------------|-----------------------------------------------------------------------|
| `INITIALIZING`             | `AXIS_MAPPING`, `ERROR`                                               |
| `AXIS_MAPPING`             | `LOOKING_FOR_CHESSBOARD`, `ERROR`                                     |
| `LOOKING_FOR_CHESSBOARD`   | `CHESSBOARD_FOUND`, `LOOKING_FOR_CHESSBOARD` (retry), `ERROR`        |
| `CHESSBOARD_FOUND`         | `LOOKING_FOR_ARUCO_MARKERS`, `ALIGN_TO_CHESSBOARD_CENTER`, `ERROR`   |
| `ALIGN_TO_CHESSBOARD_CENTER` | `LOOKING_FOR_ARUCO_MARKERS`, `ERROR`                                |
| `LOOKING_FOR_ARUCO_MARKERS`| `ALL_ARUCO_FOUND`, `LOOKING_FOR_ARUCO_MARKERS` (retry), `ERROR`      |
| `ALL_ARUCO_FOUND`          | `COMPUTE_OFFSETS`, `ERROR`                                            |
| `COMPUTE_OFFSETS`          | `ALIGN_ROBOT`, `ERROR`                                                |
| `ALIGN_ROBOT`              | `ITERATE_ALIGNMENT`, `ERROR`                                          |
| `ITERATE_ALIGNMENT`        | `ITERATE_ALIGNMENT` (retry), `SAMPLE_HEIGHT`, `ALIGN_ROBOT`, `DONE`, `ERROR` |
| `SAMPLE_HEIGHT`            | `DONE`, `ERROR`                                                       |
| `DONE`                     | `ALIGN_ROBOT` (next marker), `DONE` (final), `ERROR`                 |
| `ERROR`                    | `ERROR` (terminal)                                                    |

### Transition Enforcement

The `ExecutableStateMachine` validates every transition:

```python
def transition_to(self, next_state):
    current = self.current_state
    allowed = self.transition_rules[current]
    
    if next_state not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition from {current} to {next_state}. "
            f"Allowed: {allowed}"
        )
    
    self.current_state = next_state
```

This prevents:
- Logic errors (skipping required states)
- Invalid state sequences
- Unintended state transitions

---

## Usage Guide

### Basic Usage

```python
from modules.robot_calibration.config_helpers import (
    RobotCalibrationConfig,
    AdaptiveMovementConfig,
    RobotCalibrationEventsConfig
)
from modules.robot_calibration.newRobotCalibUsingExecutableStateMachine import (
    RefactoredRobotCalibrationPipeline
)

# Configure calibration
config = RobotCalibrationConfig(
    vision_system=my_vision_system,
    robot_service=my_robot_service,
    height_measuring_service=my_laser_service,
    required_ids=[0, 1, 2, 3],  # ArUco marker IDs
    z_target=400.0,  # Target Z height in mm
    debug=False,
    step_by_step=False,
    live_visualization=True
)

# Configure adaptive movement (optional)
adaptive_config = AdaptiveMovementConfig(
    target_error_mm=0.5,        # Target precision
    min_step_mm=0.1,            # Minimum movement
    max_step_mm=10.0,           # Maximum movement
    max_error_ref=20.0,         # Error at max step
    k=1.5,                      # Responsiveness
    derivative_scaling=0.3       # Anti-overshoot
)

# Configure event broadcasting (optional)
events_config = RobotCalibrationEventsConfig(
    broker=message_broker,
    calibration_log_topic="calibration/log",
    calibration_start_topic="calibration/start",
    calibration_stop_topic="calibration/stop",
    calibration_image_topic="calibration/image"
)

# Create pipeline
pipeline = RefactoredRobotCalibrationPipeline(
    config=config,
    adaptive_movement_config=adaptive_config,
    events_config=events_config
)

# Run calibration
success = pipeline.run()

if success:
    print("Calibration successful!")
    context = pipeline.get_context()
    print(f"Calibrated {len(context.robot_positions_for_calibration)} markers")
else:
    print("Calibration failed!")
    context = pipeline.get_context()
    print(f"Error: {context.calibration_error_message}")
```

### Accessing Results

```python
context = pipeline.get_context()

# Get robot positions for each marker
for marker_id, position in context.robot_positions_for_calibration.items():
    x, y, z, rx, ry, rz = position
    print(f"Marker {marker_id}: ({x:.2f}, {y:.2f}, {z:.2f})")

# Get camera points
for marker_id, point in context.camera_points_for_homography.items():
    x_px, y_px = point
    print(f"Marker {marker_id}: ({x_px:.2f}, {y_px:.2f}) pixels")

# Get timing statistics
for state_name, durations in context.state_timings.items():
    avg_duration = sum(durations) / len(durations)
    print(f"{state_name}: {avg_duration:.2f}s average")
```

### Monitoring State Machine

```python
state_machine = pipeline.get_state_machine()

# Get current state
current = state_machine.current_state
print(f"Current state: {current.name}")

# Check if running
if state_machine.is_running:
    print("Calibration in progress...")
```

---

## Configuration

### RobotCalibrationConfig

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vision_system` | VisionSystem | Yes | Camera interface |
| `robot_service` | RobotService | Yes | Robot control interface |
| `height_measuring_service` | HeightMeasuringService | Yes | Laser height sensor |
| `required_ids` | List[int] | Yes | ArUco marker IDs to calibrate |
| `z_target` | float | Yes | Target Z height (mm) |
| `debug` | bool | No | Enable debug outputs (default: False) |
| `step_by_step` | bool | No | Pause between steps (default: False) |
| `live_visualization` | bool | No | Show camera feed (default: True) |

### AdaptiveMovementConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_error_mm` | float | 1.0 | Target alignment precision (mm) |
| `min_step_mm` | float | 0.1 | Minimum movement step (mm) |
| `max_step_mm` | float | 10.0 | Maximum movement step (mm) |
| `max_error_ref` | float | 20.0 | Error magnitude at max step (mm) |
| `k` | float | 1.5 | Responsiveness factor (1.0=smooth, 2.0=aggressive) |
| `derivative_scaling` | float | 0.3 | Anti-overshoot damping |

### RobotCalibrationEventsConfig

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `broker` | MessageBroker | Yes | Event publisher |
| `calibration_log_topic` | str | Yes | Topic for log messages |
| `calibration_start_topic` | str | Yes | Topic for start event |
| `calibration_stop_topic` | str | Yes | Topic for stop/error events |
| `calibration_image_topic` | str | Yes | Topic for camera images |

---

## Error Handling

### Error Categories

#### 1. **System Errors**
- Camera not initialized → Wait in `INITIALIZING` state
- Camera feed failure → Retry frame capture
- Robot communication failure → Transition to `ERROR`

#### 2. **Detection Errors**
- Chessboard not found → Retry in `LOOKING_FOR_CHESSBOARD`
- Not all ArUco markers found → Retry in `LOOKING_FOR_ARUCO_MARKERS`
- Marker lost during alignment → Retry in `ITERATE_ALIGNMENT`

#### 3. **Movement Errors**
- Robot movement failed → Retry once, then `ERROR`
- Safety limits exceeded → Immediate `ERROR`
- Position unreachable → `ERROR`

#### 4. **Convergence Errors**
- Max iterations exceeded → `ERROR` with detailed message
- Alignment oscillation → Handled by adaptive movement + derivative control

#### 5. **Data Errors**
- Missing PPM (chessboard detection failed) → `ERROR` in `COMPUTE_OFFSETS`
- Invalid marker data → `ERROR` with description

### Error Messages

All errors set `context.calibration_error_message` with details:

```python
# Example error messages
"Calibration failed during offset computation. Missing required data: pixels-per-mm (PPM). Chessboard detection may have failed."

"Robot movement failed for marker 2. Could not reach target position after retry. Check robot safety limits and workspace boundaries."

"Calibration failed: Could not align with marker 3 after 50 iterations. Required precision: 1.0mm"

"Iterative robot movement failed for marker 1 during iteration 23. Check robot connectivity and safety systems."
```

### UI Notifications

When `broadcast_events=True`, errors are published to UI:

```json
{
  "status": "error",
  "message": "Could not align with marker 3 after 50 iterations",
  "details": {
    "current_marker": 3,
    "total_markers": 4,
    "successful_markers": 2,
    "iteration_count": 50,
    "max_iterations": 50
  }
}
```

### Recovery Strategies

| Error Type | Recovery | State Transition |
|------------|----------|------------------|
| Camera frame capture fails | Retry immediately | Stay in state |
| Chessboard not detected | Retry indefinitely | `LOOKING_FOR_CHESSBOARD` |
| Marker not detected | Retry indefinitely | `LOOKING_FOR_ARUCO_MARKERS` |
| Robot move fails (first attempt) | Retry from last position | Stay in state |
| Robot move fails (second attempt) | Stop calibration | `ERROR` |
| Marker lost during iteration | Continue trying | `ITERATE_ALIGNMENT` |
| Max iterations exceeded | Stop calibration | `ERROR` |

---

## Performance Optimization

### Camera Buffer Flushing

```python
context.min_camera_flush = 5  # Discard 5 old frames
```

Ensures fresh, stable frames for critical detections (chessboard, markers).

### Non-Blocking Visualization

Live camera feed uses background thread to avoid blocking state machine execution.

### Adaptive Movement

Progressive movement scaling:
- **Large errors** → Large steps (fast convergence)
- **Medium errors** → Scaled steps (balanced)
- **Small errors** → Tiny steps with damping (precision)

Prevents:
- Slow convergence (too cautious)
- Overshoot (too aggressive)
- Oscillation (derivative control)

### State Timing

Every state execution is timed:
```python
context.state_timings = {
    'INITIALIZING': [0.15],
    'AXIS_MAPPING': [8.23],
    'LOOKING_FOR_CHESSBOARD': [0.42, 0.38],
    'ITERATE_ALIGNMENT': [0.25, 0.23, 0.21, 0.19, 0.18],
    ...
}
```

Use for:
- Performance analysis
- Bottleneck identification
- Calibration optimization

---

## Homography Computation (Final Step)

After all markers are aligned, the pipeline computes the homography matrix:

```python
def _finalize_calibration(self):
    # Sort by marker ID
    sorted_robot_items = sorted(context.robot_positions_for_calibration.items())
    sorted_camera_items = sorted(context.camera_points_for_homography.items())
    
    # Extract coordinates
    robot_positions = [pos[:2] for _, pos in sorted_robot_items]  # (x, y)
    camera_points = [pt for _, pt in sorted_camera_items]  # (x_px, y_px)
    
    # Compute homography
    src_pts = np.array(camera_points, dtype=np.float32)
    dst_pts = np.array(robot_positions, dtype=np.float32)
    H, status = cv2.findHomography(src_pts, dst_pts)
    
    # Validate
    avg_error, _ = metrics.test_calibration(H, src_pts, dst_pts)
    
    # Save if accurate
    if avg_error <= 1.0:
        np.save(camera_to_robot_matrix_path, H)
        log_info("Calibration successful, matrix saved")
    else:
        log_warning(f"High error ({avg_error:.2f}mm), recalibration suggested")
```

### Homography Matrix

The 3x3 homography matrix `H` transforms camera coordinates to robot coordinates:

```python
# Camera point (in pixels)
camera_point = [x_px, y_px, 1]

# Transform to robot coordinates (in mm)
robot_point_homogeneous = H @ camera_point
robot_x = robot_point_homogeneous[0] / robot_point_homogeneous[2]
robot_y = robot_point_homogeneous[1] / robot_point_homogeneous[2]
```

---

## Troubleshooting

### Calibration Fails at Chessboard Detection

**Symptoms:** Stuck in `LOOKING_FOR_CHESSBOARD`

**Solutions:**
1. Ensure chessboard is flat, well-lit, in camera view
2. Check `chessboard_size` matches physical pattern
3. Check `square_size_mm` is correct
4. Reduce glare/reflections on chessboard
5. Ensure camera focus is correct

### Calibration Fails at ArUco Detection

**Symptoms:** Stuck in `LOOKING_FOR_ARUCO_MARKERS`

**Solutions:**
1. Ensure all required markers are visible
2. Check marker IDs match `required_ids`
3. Ensure markers are not occluded
4. Check lighting conditions
5. Verify marker print quality (sharp edges)

### Alignment Iterations Never Converge

**Symptoms:** `ERROR` with "max iterations exceeded"

**Solutions:**
1. Increase `max_iterations` (default: 50)
2. Relax `alignment_threshold_mm` (e.g., 1.5mm instead of 1.0mm)
3. Check robot movement precision
4. Verify axis mapping is correct (check AXIS_MAPPING logs)
5. Reduce `derivative_scaling` if oscillating
6. Check camera stability (vibrations)

### High Reprojection Error

**Symptoms:** `avg_error > 1.0mm` after calibration completes

**Solutions:**
1. Re-run calibration
2. Check marker placement accuracy
3. Verify chessboard is truly flat
4. Ensure robot positions were stable during alignment
5. Check for camera lens distortion
6. Use more markers (better coverage of workspace)

### Robot Movement Failures

**Symptoms:** `ERROR` with "Robot movement failed"

**Solutions:**
1. Check robot safety limits
2. Verify workspace boundaries
3. Check robot communication
4. Ensure target positions are reachable
5. Check for obstacles
6. Verify robot calibration

---

## Summary

The Robot Calibration Module uses a **state machine architecture** to perform systematic camera-to-robot calibration:

1. **Initialize** camera system
2. **Map axes** automatically (image ↔ robot)
3. **Detect chessboard** to establish reference and compute PPM
4. **Detect ArUco markers** and convert to millimeters
5. **Compute offsets** from image center
6. **Align robot** to each marker iteratively with adaptive movement
7. **Measure height** at each position (optional)
8. **Compute homography** matrix from corresponding points
9. **Validate and save** calibration data

**Key Features:**
- Fully automated (no manual intervention)
- Robust error handling and retry logic
- Adaptive movement for fast, precise convergence
- Real-time UI feedback via message broker
- Performance tracking and timing analysis
- Declarative state transitions (validated)
- Comprehensive logging and debugging

**Result:** Accurate camera-to-robot transformation enabling precise vision-guided robotic operations.

---

**End of Documentation**

