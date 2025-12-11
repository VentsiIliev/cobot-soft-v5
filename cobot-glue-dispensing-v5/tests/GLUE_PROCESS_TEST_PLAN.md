# Test Suite Plan: Glue Process Module

**Module**: `/src/applications/glue_dispensing_application/glue_process`
**Test Framework**: pytest
**Target Coverage**: 85%+
**Estimated Effort**: 4-5 weeks

---

## Executive Summary

This document outlines a comprehensive test suite for the glue dispensing process module, covering:
- **23 State Machine States** with full transition testing
- **5 Pause/Resume Scenarios** with context preservation
- **Multi-Path Operations** with configuration variants
- **Motor/Pump Control** with segment and global settings
- **Thread Management** for dynamic pump adjustment
- **Error Handling** and edge cases

**Test Distribution**:
- Unit Tests: ~100 tests
- Integration Tests: ~50 tests
- End-to-End Tests: ~30 tests
- **Total**: ~150-200 tests across 25 files

---

## Module Architecture Overview

### Core Components

```
glue_process/
├── glue_dispensing_operation.py          # Main entry (GlueDispensingOperation)
├── ExecutionContext.py                   # State/context holder
├── PumpController.py                     # Motor control
├── dynamicPumpSpeedAdjustment.py         # Pump speed thread
├── state_machine/
│   ├── ExecutableStateMachine.py         # Generic state machine engine
│   └── GlueProcessState.py               # 23 states, transition rules
└── state_handlers/                       # 11 handler modules
    ├── start_state_handler.py
    ├── moving_to_first_point_state_handler.py
    ├── initial_pump_boost_state_handler.py
    ├── start_pump_adjustment_thread_handler.py
    ├── sending_path_to_robot_state_handler.py
    ├── wait_for_path_completion_state_handler.py
    ├── transition_between_paths_state_handler.py
    ├── pause_operation.py
    ├── resume_operation.py
    ├── stop_operation.py
    └── compleated_state_handler.py
```

### State Machine Flow

```
IDLE → STARTING → MOVING_TO_FIRST_POINT → EXECUTING_PATH
     → PUMP_INITIAL_BOOST → STARTING_PUMP_ADJUSTMENT_THREAD
     → SENDING_PATH_POINTS → WAIT_FOR_PATH_COMPLETION
     → TRANSITION_BETWEEN_PATHS → [STARTING (next path) OR COMPLETED]

PAUSED ↔ Any pausable state
ERROR ← Any state (on failure)
```

### Critical Business Logic

1. **State Machine**: 23 states with transition rules and handler execution
2. **Pause/Resume**: Context preservation across 5 different pause points
3. **Motor Control**: Pump startup/shutdown with ramp settings and motor address resolution
4. **Multi-Path Execution**: Batch operations with per-path settings switching
5. **Thread Management**: Dynamic pump speed adjustment thread lifecycle
6. **Configuration**: Multiple flags affecting behavior (USE_SEGMENT_SETTINGS, TURN_OFF_PUMP_BETWEEN_PATHS, etc.)

---

## Test Suite Directory Structure

```
tests/glue_process/
├── README.md                            # This file
├── conftest.py                          # Shared fixtures (CRITICAL)
├── pytest.ini                           # Pytest configuration
│
├── unit/                                # Unit tests (isolated components)
│   ├── __init__.py
│   ├── test_execution_context.py        # ExecutionContext (CRITICAL)
│   ├── test_pump_controller.py          # PumpController motor control
│   ├── test_state_machine.py            # ExecutableStateMachine core
│   ├── test_state_transitions.py        # GlueProcessState transition rules
│   ├── test_dynamic_pump_adjustment.py  # Pump speed calculation
│   └── state_handlers/                  # Individual handler tests
│       ├── __init__.py
│       ├── test_start_state_handler.py
│       ├── test_moving_to_first_point_handler.py
│       ├── test_pump_boost_handler.py
│       ├── test_send_path_handler.py
│       ├── test_wait_completion_handler.py
│       ├── test_transition_handler.py
│       ├── test_pause_operation.py
│       ├── test_resume_operation.py
│       ├── test_stop_operation.py
│       └── test_completed_handler.py
│
├── integration/                         # Integration tests (multi-component)
│   ├── __init__.py
│   ├── test_state_machine_flow.py       # State transitions (CRITICAL)
│   ├── test_pause_resume_scenarios.py   # All pause cases (CRITICAL)
│   ├── test_multi_path_execution.py     # Multi-path operations
│   ├── test_pump_thread_lifecycle.py    # Thread coordination
│   └── test_configuration_variants.py   # Config combinations
│
├── e2e/                                 # End-to-end workflow tests
│   ├── __init__.py
│   ├── test_complete_operation.py       # Full operation lifecycle
│   ├── test_error_scenarios.py          # Error handling and recovery
│   └── test_edge_cases.py               # Boundary conditions
│
├── fixtures/                            # Test data factories
│   ├── __init__.py
│   ├── mock_services.py                 # Mock services (CRITICAL)
│   ├── test_data_factory.py             # Path/settings generators
│   └── context_factory.py               # ExecutionContext builders
│
└── utils/                               # Testing utilities
    ├── __init__.py
    ├── assertions.py                    # Custom assertion helpers
    └── helpers.py                       # Test helper functions
```

---

## Pytest Configuration

### pytest.ini

```ini
[tool:pytest]
testpaths = tests/glue_process
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    --verbose
    --tb=short
    --strict-markers
    --color=yes
    -ra
    --durations=10
    --cov=glue_process
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85

markers =
    unit: Unit tests for individual components
    integration: Integration tests for component interactions
    e2e: End-to-end workflow tests
    slow: Tests that take longer to run
    pause_resume: Tests focused on pause/resume functionality
    multi_path: Tests for multi-path operations
    config_variant: Tests for different configuration combinations
    thread_safety: Tests for thread-related functionality

log_cli = false
log_cli_level = INFO
```

---

## Core Fixtures (conftest.py)

### Mock Services

```python
@pytest.fixture
def mock_robot_service():
    """Mock RobotService with configurable behavior."""
    robot = MagicMock()
    robot.robot.move_cartesian.return_value = 0  # Success
    robot.robot.move_liner.return_value = 0
    robot.get_current_position.return_value = [0, 0, 0, 0, 0, 0]
    robot.get_current_velocity.return_value = 100.0
    robot.stop_motion.return_value = None
    return robot

@pytest.fixture
def mock_glue_service():
    """Mock GlueSprayService with motor/generator control."""
    service = MagicMock()
    service.motorOn.return_value = True
    service.motorOff.return_value = None
    service.generatorOn.return_value = None
    service.generatorState.return_value = False
    return service

@pytest.fixture
def mock_message_broker():
    """Mock MessageBroker for state publishing."""
    broker = MagicMock()
    broker.publish.return_value = None
    return broker
```

### Execution Contexts

```python
@pytest.fixture
def empty_context():
    """Empty ExecutionContext for testing."""
    return ExecutionContext()

@pytest.fixture
def basic_context(mock_robot_service, mock_glue_service):
    """ExecutionContext with basic setup."""
    context = ExecutionContext()
    context.robot_service = mock_robot_service
    context.service = mock_glue_service
    context.spray_on = True
    return context

@pytest.fixture
def context_with_paths(basic_context, simple_path_data):
    """ExecutionContext with paths configured."""
    basic_context.paths = simple_path_data
    basic_context.current_path = simple_path_data[0][0]
    basic_context.current_settings = simple_path_data[0][1]
    return basic_context
```

### Test Data

```python
@pytest.fixture
def simple_path_data():
    """Single path with 3 points."""
    path = [
        [100.0, 200.0, 300.0, 0.0, 0.0, 0.0],
        [110.0, 210.0, 310.0, 0.0, 0.0, 0.0],
        [120.0, 220.0, 320.0, 0.0, 0.0, 0.0],
    ]
    settings = {
        "GLUE_TYPE": "TypeA",
        "MOTOR_SPEED": 10000,
        "FORWARD_RAMP_STEPS": 1,
        "INITIAL_RAMP_SPEED": 5000,
        # ... other settings
    }
    return [(path, settings)]

@pytest.fixture
def multi_path_data():
    """3 paths with different glue types."""
    # Returns list of (path, settings) tuples

@pytest.fixture
def complex_path_data():
    """50-point path for stress testing."""
    # Returns single path with many points
```

### Parametrization

```python
@pytest.fixture(params=[True, False])
def spray_on_variant(request):
    """Parametrize spray_on flag."""
    return request.param

@pytest.fixture(params=[
    GlueProcessState.MOVING_TO_FIRST_POINT,
    GlueProcessState.EXECUTING_PATH,
    GlueProcessState.WAIT_FOR_PATH_COMPLETION,
    GlueProcessState.SENDING_PATH_POINTS,
    GlueProcessState.TRANSITION_BETWEEN_PATHS,
])
def pausable_state(request):
    """States from which pause can occur."""
    return request.param
```

---

## Test Categories

### 1. Unit Tests: ExecutionContext

**File**: `unit/test_execution_context.py`
**Coverage**: State management, progress tracking, validation

**Test Classes**:
- `TestExecutionContextInitialization` - Default values, reset
- `TestProgressManagement` - Save/retrieve progress, validation
- `TestMotorAddressResolution` - Glue type → motor address mapping
- `TestDebugSerialization` - Debug dictionary output

**Key Tests**:
```python
test_context_default_initialization()
test_context_reset()
test_save_progress()
test_has_valid_context_with_paths()
test_motor_address_successful_resolution()
test_to_debug_dict_with_data()
```

**Assertions**:
- Default values are correct
- Reset clears all state
- Progress saves correctly
- Motor address resolution works
- Debug output is complete

---

### 2. Unit Tests: PumpController

**File**: `unit/test_pump_controller.py`
**Coverage**: Motor control with segment/global settings

**Test Classes**:
- `TestPumpStartup` - Motor on with different configurations
- `TestPumpShutdown` - Motor off with reverse
- `TestSettingsSelection` - Segment vs global settings
- `TestMotorAddressHandling` - Address validation

**Key Tests**:
```python
test_pump_on_with_segment_settings()
test_pump_on_with_global_settings()
test_pump_on_with_initial_boost()
test_pump_off_with_reverse()
test_invalid_motor_address_handling()
```

**Assertions**:
- Correct motor speed applied
- Ramp settings used correctly
- Initial boost works
- Reverse speed applied on shutdown
- Invalid addresses handled gracefully

---

### 3. Unit Tests: State Handlers

**Files**: `unit/state_handlers/test_*.py` (11 files)
**Coverage**: Individual handler logic, transitions, service calls

**Per-Handler Tests** (~10 tests each):
- Input validation
- State transition logic
- Service method calls
- Error handling
- Return value verification

**Example: test_start_state_handler.py**:
```python
test_start_with_valid_paths()
test_start_resumes_from_executing_path()
test_start_resumes_from_wait_completion()
test_start_resumes_from_transition_between_paths()
test_start_with_empty_paths_returns_completed()
test_start_with_out_of_bounds_index()
test_start_moves_robot_to_first_point()
```

---

### 4. Integration Tests: Pause/Resume

**File**: `integration/test_pause_resume_scenarios.py`
**Coverage**: All 5 pause scenarios + resume logic

**Test Classes**:
- `TestPauseFromDifferentStates` - Each pausable state
- `TestResumeScenarios` - Resume validation and transitions
- `TestPauseResumeRoundTrip` - Complete pause/resume cycles

**5 Pause Scenarios**:
1. **MOVING_TO_FIRST_POINT**: Save state, retry movement
2. **EXECUTING_PATH**: Save point index, continue path
3. **WAIT_FOR_PATH_COMPLETION**: Capture pump thread progress
4. **SENDING_PATH_POINTS**: Save point being sent
5. **TRANSITION_BETWEEN_PATHS**: Skip to next path

**Key Tests**:
```python
test_pause_from_moving_to_first_point()
test_pause_from_executing_path()
test_pause_with_active_pump_thread()
test_resume_from_paused_state()
test_resume_not_in_paused_state()
test_pause_resume_preserves_progress()
```

**Assertions**:
- Paused state reached
- `paused_from_state` saved correctly
- Robot motion stopped
- Pump/generator stopped
- Progress preserved
- Resume restores correct state

---

### 5. Integration Tests: State Machine Flow

**File**: `integration/test_state_machine_flow.py`
**Coverage**: State transitions through complete workflow

**Test Classes**:
- `TestNormalExecutionFlow` - IDLE → COMPLETED sequence
- `TestStateTransitionValidation` - Transition rules enforcement
- `TestMessageBrokerIntegration` - State publishing
- `TestErrorStateHandling` - Error transitions

**Key Tests**:
```python
test_complete_state_sequence()
test_state_transitions_follow_rules()
test_invalid_transitions_rejected()
test_message_broker_publishes_states()
test_error_state_from_any_state()
```

**Assertions**:
- All expected states reached
- Transitions follow rules
- Invalid transitions rejected
- Message broker called
- Error state accessible

---

### 6. Integration Tests: Multi-Path

**File**: `integration/test_multi_path_execution.py`
**Coverage**: Multiple path operations, settings switching

**Test Classes**:
- `TestMultiPathIteration` - Path index management
- `TestSettingsSwitching` - Per-path configuration
- `TestMotorAddressChanges` - Different glue types
- `TestPumpBehaviorBetweenPaths` - Configuration-dependent

**Key Tests**:
```python
test_three_path_execution()
test_settings_switch_per_path()
test_motor_address_changes_with_glue_type()
test_pump_off_between_paths_enabled()
test_pump_off_between_paths_disabled()
test_generator_persists_across_paths()
```

**Assertions**:
- Path index increments correctly
- Settings change per path
- Motor address updates
- Pump on/off behavior correct
- Generator state maintained

---

### 7. E2E Tests: Complete Operations

**File**: `e2e/test_complete_operation.py`
**Coverage**: Full operation lifecycle

**Test Classes**:
- `TestCompleteOperationWorkflow` - Success cases
- `TestOperationVariants` - Different configurations

**Key Tests**:
```python
test_single_path_operation_success()
test_multi_path_operation_success()
test_operation_without_spray()
test_operation_with_complex_path()
```

**Assertions**:
- Operation completes successfully
- Final state is IDLE/COMPLETED
- Robot commands executed
- Pump lifecycle correct
- All paths processed

---

### 8. E2E Tests: Error Scenarios

**File**: `e2e/test_error_scenarios.py`
**Coverage**: Error handling and recovery

**Test Classes**:
- `TestRobotFailures` - Movement errors
- `TestPumpFailures` - Motor/generator errors
- `TestConfigurationErrors` - Invalid settings
- `TestTimeouts` - Timeout handling

**Key Tests**:
```python
test_robot_movement_failure()
test_pump_startup_failure()
test_invalid_motor_address()
test_empty_path_handling()
test_timeout_waiting_for_robot()
test_thread_join_failure()
```

**Assertions**:
- Error state reached
- Services stopped gracefully
- Error messages logged
- Resources cleaned up

---

## Mock Strategy

### RobotService Mock Behavior

```python
# Successful movement
mock_robot.robot.move_cartesian.return_value = 0
mock_robot.robot.move_liner.return_value = 0

# Failed movement
mock_robot.robot.move_cartesian.return_value = -1

# Position tracking
mock_robot.get_current_position.return_value = [100, 200, 300, 0, 0, 0]

# Simulate movement
def simulate_movement(start, end, steps=10):
    positions = [interpolate(start, end, i/steps) for i in range(steps+1)]
    mock_robot.get_current_position.side_effect = positions
```

### GlueSprayService Mock Behavior

```python
# Normal operation
mock_service.motorOn.return_value = True
mock_service.motorOff.return_value = None

# Pump failure
mock_service.motorOn.return_value = False
mock_service.motorOn.side_effect = Exception("Motor error")

# Track calls
assert mock_service.motorOn.call_count == expected_count
assert mock_service.motorOn.call_args[1]['speed'] == expected_speed
```

### Thread Mock Behavior

```python
def create_pump_thread_mock(success=True, final_progress=10, alive_iterations=5):
    thread = Mock()
    alive_count = [0]

    def is_alive():
        alive_count[0] += 1
        return alive_count[0] <= alive_iterations

    thread.is_alive.side_effect = is_alive
    thread.result = (success, final_progress)
    return thread
```

---

## Parametrization Strategy

### Configuration Matrix

```python
@pytest.mark.parametrize("use_segment,turn_off_pump,adjust_speed,spray_on", [
    (True, True, True, True),    # All features enabled
    (True, False, True, True),   # Keep pump on between paths
    (False, True, False, False), # Global settings, no spray
    (True, True, False, True),   # No dynamic adjustment
    (False, False, False, False), # Minimal configuration
])
def test_configuration_combinations(use_segment, turn_off_pump, adjust_speed, spray_on):
    with patch('USE_SEGMENT_SETTINGS', use_segment), \
         patch('TURN_OFF_PUMP_BETWEEN_PATHS', turn_off_pump), \
         patch('ADJUST_PUMP_SPEED_WHILE_SPRAY', adjust_speed):
        # Test operation with configuration
```

### State Transition Matrix

```python
@pytest.mark.parametrize("from_state,to_state,is_valid", [
    (IDLE, STARTING, True),
    (STARTING, MOVING_TO_FIRST_POINT, True),
    (MOVING_TO_FIRST_POINT, EXECUTING_PATH, True),
    (IDLE, COMPLETED, False),  # Invalid
    (PAUSED, STARTING, True),  # Resume
    (ANY_STATE, ERROR, True),  # Error always valid
])
def test_state_transitions(from_state, to_state, is_valid):
    # Test transition validity
```

---

## Implementation Priority

### Phase 1: Foundation (Week 1)

**Priority**: CRITICAL
**Goal**: Establish testing infrastructure

1. ✅ Create directory structure (`tests/glue_process/...`)
2. ✅ Write `pytest.ini` configuration
3. ✅ Implement `conftest.py` with core fixtures
4. ✅ Create `fixtures/mock_services.py`
5. ✅ Write `unit/test_execution_context.py` (15 tests)
6. ✅ Write `unit/test_pump_controller.py` (12 tests)

**Deliverables**:
- Basic test infrastructure working
- Can run: `pytest tests/glue_process/unit/`
- Mock services validated

---

### Phase 2: State Machine (Week 2)

**Priority**: HIGH
**Goal**: Test state machine core and handlers

7. ✅ `unit/test_state_machine.py` (10 tests)
8. ✅ `unit/test_state_transitions.py` (20 tests)
9. ✅ `unit/state_handlers/test_completed_handler.py` (8 tests)
10. ✅ `unit/state_handlers/test_start_state_handler.py` (15 tests)
11. ✅ `unit/state_handlers/test_moving_to_first_point_handler.py` (12 tests)
12. ✅ Remaining 8 state handler test files (~80 tests total)

**Deliverables**:
- All state handlers tested individually
- State machine core logic validated
- Can run: `pytest tests/glue_process/unit/state_handlers/`

---

### Phase 3: Integration (Week 3)

**Priority**: CRITICAL
**Goal**: Test multi-component interactions

13. ✅ `integration/test_state_machine_flow.py` (15 tests)
14. ✅ `integration/test_pause_resume_scenarios.py` (20 tests) **[MOST CRITICAL]**
15. ✅ `integration/test_multi_path_execution.py` (15 tests)
16. ✅ `integration/test_pump_thread_lifecycle.py` (10 tests)
17. ✅ `integration/test_configuration_variants.py` (12 tests)

**Deliverables**:
- All pause/resume scenarios tested
- Multi-path operations validated
- Configuration matrix coverage
- Can run: `pytest tests/glue_process/integration/`

---

### Phase 4: E2E & Edge Cases (Week 4)

**Priority**: MEDIUM
**Goal**: Complete workflow testing

18. ✅ `e2e/test_complete_operation.py` (12 tests)
19. ✅ `e2e/test_error_scenarios.py` (15 tests)
20. ✅ `e2e/test_edge_cases.py` (10 tests)
21. ✅ `fixtures/test_data_factory.py` (helper methods)
22. ✅ `utils/assertions.py` (custom assertions)

**Deliverables**:
- End-to-end workflows tested
- Error handling validated
- Edge cases covered
- Can run: `pytest tests/glue_process/ --cov`

---

### Phase 5: Refinement (Week 5)

**Priority**: LOW
**Goal**: Polish and documentation

23. ✅ Coverage analysis and gap filling
24. ✅ Performance optimization (test speed)
25. ✅ Documentation updates
26. ✅ CI/CD integration (if applicable)
27. ✅ Code review and cleanup

**Deliverables**:
- 85%+ code coverage achieved
- All tests fast (<10s total)
- Documentation complete
- Ready for production use

---

## Success Criteria

### Coverage Targets

| Component | Target | Critical |
|-----------|--------|----------|
| **Overall** | 85%+ | ✓ |
| ExecutionContext | 95%+ | ✓ |
| PumpController | 90%+ | ✓ |
| State Handlers | 90%+ | ✓ |
| State Machine | 85%+ | ✓ |
| Dynamic Adjustment | 80%+ | - |

### Quality Metrics

✅ All 23 states have test coverage
✅ All 5 pause/resume scenarios tested
✅ All configuration combinations tested
✅ No flaky tests (deterministic mocking)
✅ Fast execution (<10 seconds full suite)
✅ Clear, descriptive test names
✅ Informative failure messages

### Documentation

✅ Each test has docstring explaining purpose
✅ Complex tests include inline comments
✅ README with execution instructions
✅ Coverage reports generated

---

## Running Tests

### Basic Commands

```bash
# Install dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest tests/glue_process/

# Run with verbose output
pytest tests/glue_process/ -v

# Run with coverage
pytest tests/glue_process/ --cov=glue_process --cov-report=html

# View coverage report
open htmlcov/index.html
```

### By Category

```bash
# Unit tests only
pytest tests/glue_process/unit/ -m unit

# Integration tests only
pytest tests/glue_process/integration/ -m integration

# E2E tests only
pytest tests/glue_process/e2e/ -m e2e

# Pause/resume tests
pytest tests/glue_process/ -m pause_resume

# Multi-path tests
pytest tests/glue_process/ -m multi_path

# Configuration variants
pytest tests/glue_process/ -m config_variant
```

### Specific Tests

```bash
# Single test file
pytest tests/glue_process/integration/test_pause_resume_scenarios.py -v

# Single test class
pytest tests/glue_process/unit/test_execution_context.py::TestProgressManagement -v

# Single test function
pytest tests/glue_process/unit/test_execution_context.py::test_save_progress -v

# Tests matching pattern
pytest tests/glue_process/ -k "pause" -v
```

### Advanced Options

```bash
# Show slowest tests
pytest tests/glue_process/ --durations=10

# Stop on first failure
pytest tests/glue_process/ -x

# Run last failed tests
pytest tests/glue_process/ --lf

# Run in parallel (requires pytest-xdist)
pytest tests/glue_process/ -n auto

# Generate JUnit XML report
pytest tests/glue_process/ --junitxml=test-results.xml

# Skip slow tests
pytest tests/glue_process/ -m "not slow"
```

---

## Key Design Decisions

### 1. Full Mocking Strategy
**Decision**: Mock all external services (RobotService, GlueSprayService, MessageBroker)
**Rationale**:
- No hardware dependencies
- Fast, deterministic tests
- Complete control over service behavior
- Easy failure simulation

### 2. Fixture-Based Test Data
**Decision**: Use pytest fixtures for all test data
**Rationale**:
- Reusable across tests
- Clear, declarative test setup
- Easy parametrization
- Reduces code duplication

### 3. Layered Test Strategy
**Decision**: Unit → Integration → E2E progression
**Rationale**:
- Build confidence incrementally
- Isolate failures quickly
- Easy to debug
- Clear test ownership

### 4. State-Focused Testing
**Decision**: Heavy emphasis on state machine correctness
**Rationale**:
- State machine is core architecture
- State bugs cause system failures
- Complex transition logic needs validation
- Pause/resume depends on state

### 5. Parametrization Over Duplication
**Decision**: Use `@pytest.mark.parametrize` for variants
**Rationale**:
- Test all configuration combinations
- Avoid copy-paste tests
- Clear test coverage matrix
- Easy to add new variants

### 6. Explicit Thread Testing
**Decision**: Dedicated tests for pump thread lifecycle
**Rationale**:
- Threading is error-prone
- Race conditions need verification
- Thread cleanup is critical
- Pause must coordinate with thread

### 7. Pause/Resume Priority
**Decision**: Most complex logic gets dedicated integration test file
**Rationale**:
- 5 pause scenarios × resume logic = complex
- Critical for system reliability
- User-facing feature
- High bug risk area

---

## Testing Anti-Patterns to Avoid

❌ **Don't test implementation details**
✅ Test behavior and outcomes, not internal method calls

❌ **Don't use real services/hardware**
✅ Use mocks for all external dependencies

❌ **Don't write flaky tests**
✅ Ensure deterministic behavior with controlled mocks

❌ **Don't duplicate test code**
✅ Use fixtures and parametrization

❌ **Don't ignore coverage gaps**
✅ Aim for 85%+ coverage, investigate uncovered code

❌ **Don't write slow tests**
✅ Keep full suite under 10 seconds

❌ **Don't skip error cases**
✅ Test failure paths as thoroughly as success paths

---

## Common Testing Patterns

### Pattern 1: Setup-Execute-Assert

```python
def test_operation_success(mock_robot_service, simple_path_data):
    # Setup
    operation = GlueDispensingOperation(robot_service=mock_robot_service)

    # Execute
    result = operation.start(paths=simple_path_data, spray_on=True)

    # Assert
    assert result.success is True
    assert mock_robot_service.robot.move_cartesian.called
```

### Pattern 2: Context Manager for Configuration

```python
def test_with_configuration():
    with patch('USE_SEGMENT_SETTINGS', True):
        # Test with segment settings enabled
        pass
```

### Pattern 3: Parametrized Fixtures

```python
@pytest.fixture(params=[True, False])
def spray_variant(request):
    return request.param

def test_operation(spray_variant):
    # Test runs twice: spray_on=True and spray_on=False
    pass
```

### Pattern 4: Custom Assertions

```python
def assert_state_transition(state_machine, expected_state):
    assert state_machine.state == expected_state, \
        f"Expected {expected_state}, got {state_machine.state}"
```

---

## Maintenance Guidelines

### Adding New Tests

1. Identify appropriate category (unit/integration/e2e)
2. Use existing fixtures where possible
3. Follow naming convention: `test_<what>_<scenario>()`
4. Add docstring explaining purpose
5. Use appropriate markers (`@pytest.mark.unit`, etc.)
6. Verify coverage with: `pytest --cov`

### Updating Existing Tests

1. Understand original test intent
2. Preserve test isolation
3. Update fixtures if needed
4. Run affected tests: `pytest -k "pattern"`
5. Verify coverage hasn't decreased

### Debugging Test Failures

1. Run single test: `pytest path/to/test.py::test_name -v`
2. Add `--pdb` flag to drop into debugger on failure
3. Check mock call history: `mock.call_args_list`
4. Verify fixture setup with print statements
5. Use `pytest --lf` to run last failed

---

## Appendix: File Checklist

### Must Create (Priority 1)

- [ ] `tests/glue_process/conftest.py`
- [ ] `tests/glue_process/pytest.ini`
- [ ] `tests/glue_process/fixtures/mock_services.py`
- [ ] `tests/glue_process/unit/test_execution_context.py`
- [ ] `tests/glue_process/integration/test_pause_resume_scenarios.py`
- [ ] `tests/glue_process/integration/test_state_machine_flow.py`

### Should Create (Priority 2)

- [ ] `tests/glue_process/unit/test_pump_controller.py`
- [ ] `tests/glue_process/unit/test_state_machine.py`
- [ ] `tests/glue_process/unit/state_handlers/test_start_state_handler.py`
- [ ] `tests/glue_process/integration/test_multi_path_execution.py`
- [ ] `tests/glue_process/e2e/test_complete_operation.py`

### Nice to Have (Priority 3)

- [ ] `tests/glue_process/fixtures/test_data_factory.py`
- [ ] `tests/glue_process/utils/assertions.py`
- [ ] `tests/glue_process/e2e/test_error_scenarios.py`
- [ ] `tests/glue_process/e2e/test_edge_cases.py`

### All State Handler Tests (11 files)

- [ ] `test_start_state_handler.py`
- [ ] `test_moving_to_first_point_handler.py`
- [ ] `test_pump_boost_handler.py`
- [ ] `test_start_pump_adjustment_thread_handler.py`
- [ ] `test_send_path_handler.py`
- [ ] `test_wait_completion_handler.py`
- [ ] `test_transition_handler.py`
- [ ] `test_pause_operation.py`
- [ ] `test_resume_operation.py`
- [ ] `test_stop_operation.py`
- [ ] `test_completed_handler.py`

---

## Contact & Support

**Questions?** Contact the test suite maintainer or open an issue.

**Coverage Issues?** Run `pytest --cov --cov-report=html` and check `htmlcov/index.html`

**CI/CD Integration?** See `.github/workflows/test.yml` (if applicable)

---

**Last Updated**: 2025-12-11
**Version**: 1.0
**Status**: Planning Complete, Ready for Implementation