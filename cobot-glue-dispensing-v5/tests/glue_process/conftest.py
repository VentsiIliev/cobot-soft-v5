"""
Shared fixtures for glue_process testing.
Provides mock services, test data, and execution contexts.
"""

import pytest
import threading
import sys
import os
from unittest.mock import Mock, MagicMock, PropertyMock, patch
from typing import List, Tuple, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Import modules under test
from applications.glue_dispensing_application.glue_process.ExecutionContext import ExecutionContext
from applications.glue_dispensing_application.glue_process.PumpController import PumpController
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import (
    GlueProcessState, GlueProcessTransitionRules
)
from applications.glue_dispensing_application.glue_process.state_machine.ExecutableStateMachine import (
    ExecutableStateMachine, StateRegistry, State, ExecutableStateMachineBuilder
)
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from modules.utils.custom_logging import LoggerContext


# ============================================================================
# MOCK SERVICES
# ============================================================================

@pytest.fixture
def mock_robot_service():
    """Mock RobotService with configurable behavior."""
    robot = MagicMock()

    # Robot instance methods
    robot.robot = MagicMock()
    robot.robot.move_cartesian = MagicMock(return_value=0)  # Success
    robot.robot.move_liner = MagicMock(return_value=0)  # Success
    robot.get_current_position = MagicMock(return_value=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    robot.get_current_velocity = MagicMock(return_value=100.0)
    robot.get_current_acceleration = MagicMock(return_value=0.0)
    robot.stop_motion = MagicMock(return_value=None)
    robot.is_motion_complete = MagicMock(return_value=False)

    # Robot configuration
    robot.robot_config = MagicMock()
    robot.robot_config.robot_tool = 1
    robot.robot_config.robot_user = 0
    robot.robot_config.global_motion_settings = MagicMock()
    robot.robot_config.global_motion_settings.global_velocity = 100.0
    robot.robot_config.global_motion_settings.global_acceleration = 100.0
    robot.robot_state_manager_cycle_time = 0.01  # Fast for testing

    # Logger context
    robot.logger_context = LoggerContext(enabled=False, logger=None)

    return robot


@pytest.fixture
def mock_glue_service():
    """Mock GlueSprayService with motor/generator control."""
    service = MagicMock()

    # Motor control
    service.motorOn = MagicMock(return_value=True)
    service.motorOff = MagicMock(return_value=None)
    service.adjustMotorSpeed = MagicMock(return_value=None)

    # Generator control
    service.generatorOn = MagicMock(return_value=None)
    service.generatorOff = MagicMock(return_value=None)
    service.generatorState = MagicMock(return_value=False)

    # Settings
    service.settings = None

    return service


@pytest.fixture
def mock_message_broker():
    """Mock MessageBroker for state publishing."""
    broker = MagicMock()
    broker.publish = MagicMock(return_value=None)
    return broker


@pytest.fixture
def mock_glue_application():
    """Mock glue application with settings."""
    app = MagicMock()
    app.get_glue_settings = MagicMock(return_value=GlueSettings())
    return app


# ============================================================================
# EXECUTION CONTEXT FIXTURES
# ============================================================================

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
    context.current_path_index = 0
    context.current_point_index = 0
    return context


@pytest.fixture
def context_with_paths(basic_context, simple_path_data):
    """ExecutionContext with paths configured."""
    basic_context.paths = simple_path_data
    basic_context.current_path = simple_path_data[0][0]
    basic_context.current_settings = simple_path_data[0][1]
    return basic_context


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def simple_path_data():
    """Single path with settings."""
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
        "INITIAL_RAMP_SPEED_DURATION": 1.0,
        "SPEED_REVERSE": 1000,
        "REVERSE_DURATION": 1.0,
        "REVERSE_RAMP_STEPS": 1,
        "GLUE_SPEED_COEFFICIENT": 100.0,
        "GLUE_ACCELERATION_COEFFICIENT": 50.0,
        "REACH_START_THRESHOLD": 1.0,
        "REACH_END_THRESHOLD": 1.0,
        "VELOCITY": 10.0,
        "ACCELERATION": 30.0,
    }
    return [(path, settings)]


@pytest.fixture
def multi_path_data():
    """Multiple paths with different settings."""
    paths = []
    for i in range(3):
        path = [
            [100.0 + i*50, 200.0, 300.0, 0.0, 0.0, 0.0],
            [110.0 + i*50, 210.0, 310.0, 0.0, 0.0, 0.0],
            [120.0 + i*50, 220.0, 320.0, 0.0, 0.0, 0.0],
        ]
        settings = {
            "GLUE_TYPE": f"Type{chr(65+i)}",  # TypeA, TypeB, TypeC
            "MOTOR_SPEED": 10000 + i*1000,
            "FORWARD_RAMP_STEPS": 1,
            "INITIAL_RAMP_SPEED": 5000,
            "INITIAL_RAMP_SPEED_DURATION": 1.0,
            "SPEED_REVERSE": 1000,
            "REVERSE_DURATION": 1.0,
            "REVERSE_RAMP_STEPS": 1,
            "GLUE_SPEED_COEFFICIENT": 100.0,
            "GLUE_ACCELERATION_COEFFICIENT": 50.0,
            "REACH_START_THRESHOLD": 1.0,
            "REACH_END_THRESHOLD": 1.0,
            "VELOCITY": 10.0 + i*5,
            "ACCELERATION": 30.0,
        }
        paths.append((path, settings))
    return paths


@pytest.fixture
def complex_path_data():
    """Complex path with many points for stress testing."""
    path = [[100.0 + i*10, 200.0, 300.0, 0.0, 0.0, 0.0] for i in range(50)]
    settings = {
        "GLUE_TYPE": "TypeA",
        "MOTOR_SPEED": 10000,
        "FORWARD_RAMP_STEPS": 5,
        "INITIAL_RAMP_SPEED": 5000,
        "INITIAL_RAMP_SPEED_DURATION": 2.0,
        "SPEED_REVERSE": 1000,
        "REVERSE_DURATION": 1.0,
        "REVERSE_RAMP_STEPS": 3,
        "GLUE_SPEED_COEFFICIENT": 100.0,
        "GLUE_ACCELERATION_COEFFICIENT": 50.0,
        "REACH_START_THRESHOLD": 1.0,
        "REACH_END_THRESHOLD": 1.0,
        "VELOCITY": 10.0,
        "ACCELERATION": 30.0,
    }
    return [(path, settings)]


# ============================================================================
# STATE MACHINE FIXTURES
# ============================================================================

@pytest.fixture
def state_registry():
    """Empty StateRegistry for testing."""
    return StateRegistry()


@pytest.fixture
def transition_rules():
    """GlueProcessState transition rules."""
    return GlueProcessTransitionRules.get_glue_transition_rules()


@pytest.fixture
def mock_state_machine(basic_context, transition_rules):
    """Mock state machine with basic setup."""
    registry = StateRegistry()

    # Register simple handlers for all states
    for state in GlueProcessState:
        handler = lambda ctx, s=state: s  # Return same state
        registry.register_state(State(state, handler))

    machine = (
        ExecutableStateMachineBuilder()
        .with_initial_state(GlueProcessState.IDLE)
        .with_transition_rules(transition_rules)
        .with_state_registry(registry)
        .with_context(basic_context)
        .build()
    )

    return machine


# ============================================================================
# PUMP CONTROLLER FIXTURES
# ============================================================================

@pytest.fixture
def pump_controller():
    """PumpController with segment settings enabled."""
    logger_context = LoggerContext(enabled=False, logger=None)
    glue_settings = GlueSettings()
    return PumpController(
        use_segment_settings=True,
        logger_context=logger_context,
        glue_settings=glue_settings
    )


@pytest.fixture
def pump_controller_global():
    """PumpController with global settings."""
    logger_context = LoggerContext(enabled=False, logger=None)
    glue_settings = GlueSettings()
    return PumpController(
        use_segment_settings=False,
        logger_context=logger_context,
        glue_settings=glue_settings
    )


# ============================================================================
# THREAD FIXTURES
# ============================================================================

@pytest.fixture
def mock_pump_thread():
    """Mock pump adjustment thread."""
    thread = MagicMock(spec=threading.Thread)
    thread.is_alive = MagicMock(return_value=False)
    thread.result = (True, 10)  # Success, reached point 10
    return thread


@pytest.fixture
def pump_ready_event():
    """Threading event for pump readiness."""
    return threading.Event()


# ============================================================================
# PARAMETRIZATION DATA
# ============================================================================

@pytest.fixture(params=[True, False])
def spray_on_variant(request):
    """Parametrize spray_on flag."""
    return request.param


@pytest.fixture(params=[True, False])
def use_segment_settings_variant(request):
    """Parametrize USE_SEGMENT_SETTINGS flag."""
    return request.param


@pytest.fixture(params=[True, False])
def turn_off_pump_variant(request):
    """Parametrize TURN_OFF_PUMP_BETWEEN_PATHS flag."""
    return request.param


@pytest.fixture(params=[True, False])
def adjust_pump_speed_variant(request):
    """Parametrize ADJUST_PUMP_SPEED_WHILE_SPRAY flag."""
    return request.param


# ============================================================================
# PAUSE/RESUME TEST FIXTURES
# ============================================================================

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


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def logger_context():
    """Disabled logger context for testing."""
    return LoggerContext(enabled=False, logger=None)


@pytest.fixture
def glue_settings():
    """Default GlueSettings instance."""
    return GlueSettings()


# ============================================================================
# ASSERTION HELPERS
# ============================================================================

class GlueProcessAssertions:
    """Custom assertions for glue process testing."""

    @staticmethod
    def assert_context_valid(context: ExecutionContext):
        """Assert ExecutionContext has valid state."""
        assert context is not None
        assert isinstance(context, ExecutionContext)

    @staticmethod
    def assert_state_transition_valid(from_state, to_state, transition_rules):
        """Assert state transition is valid."""
        assert to_state in transition_rules.get(from_state, set()), \
            f"Invalid transition: {from_state} -> {to_state}"

    @staticmethod
    def assert_pump_called_with_settings(mock_service, expected_speed):
        """Assert pump was called with expected settings."""
        assert mock_service.motorOn.called
        call_kwargs = mock_service.motorOn.call_args[1]
        assert call_kwargs['speed'] == expected_speed

    @staticmethod
    def assert_path_progress(context, expected_path_idx, expected_point_idx):
        """Assert context has expected progress."""
        assert context.current_path_index == expected_path_idx
        assert context.current_point_index == expected_point_idx


@pytest.fixture
def assertions():
    """Provide assertion helpers."""
    return GlueProcessAssertions()
