"""
Unit tests for ExecutableStateMachine core components.
Tests State, StateRegistry, ExecutableStateMachine, and Builder.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from enum import Enum

from applications.glue_dispensing_application.glue_process.ExecutionContext import ExecutionContext, Context
from applications.glue_dispensing_application.glue_process.state_machine.ExecutableStateMachine import (
    State, StateRegistry, ExecutableStateMachine, ExecutableStateMachineBuilder
)
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import (
    GlueProcessState, GlueProcessTransitionRules
)
from modules.shared.MessageBroker import MessageBroker


# ============================================================================
# TEST STATE CLASS
# ============================================================================

class TestStateClass:
    """Test State class behavior."""

    def test_state_initialization(self):
        """State should initialize with state enum and handler."""
        def handler(ctx):
            return GlueProcessState.IDLE

        state = State(
            state=GlueProcessState.STARTING,
            handler=handler
        )

        assert state.state == GlueProcessState.STARTING
        assert state.handler == handler
        assert state.on_enter is None
        assert state.on_exit is None

    def test_state_with_enter_exit_handlers(self):
        """State should accept on_enter and on_exit callbacks."""
        def handler(ctx):
            return GlueProcessState.IDLE

        def on_enter(ctx):
            pass

        def on_exit(ctx):
            pass

        state = State(
            state=GlueProcessState.STARTING,
            handler=handler,
            on_enter=on_enter,
            on_exit=on_exit
        )

        assert state.on_enter == on_enter
        assert state.on_exit == on_exit

    def test_state_execute_calls_handler(self):
        """execute() should call the handler with context."""
        context = ExecutionContext()
        handler_mock = Mock(return_value=GlueProcessState.IDLE)

        state = State(
            state=GlueProcessState.STARTING,
            handler=handler_mock
        )

        result = state.execute(context)

        handler_mock.assert_called_once_with(context)
        assert result == GlueProcessState.IDLE

    def test_state_execute_returns_next_state(self):
        """execute() should return the next state from handler."""
        context = ExecutionContext()

        def handler(ctx):
            return GlueProcessState.MOVING_TO_FIRST_POINT

        state = State(
            state=GlueProcessState.STARTING,
            handler=handler
        )

        next_state = state.execute(context)

        assert next_state == GlueProcessState.MOVING_TO_FIRST_POINT

    def test_state_execute_with_no_handler(self):
        """execute() should return None if no handler."""
        context = ExecutionContext()

        state = State(
            state=GlueProcessState.IDLE,
            handler=None
        )

        result = state.execute(context)

        assert result is None

    @patch('applications.glue_dispensing_application.glue_process.state_machine.ExecutableStateMachine.log_if_enabled')
    def test_state_execute_exception_handling(self, mock_log):
        """execute() should catch exceptions and return None."""
        context = ExecutionContext()

        def failing_handler(ctx):
            raise ValueError("Handler error")

        state = State(
            state=GlueProcessState.STARTING,
            handler=failing_handler
        )

        result = state.execute(context)

        assert result is None  # Exception caught, returns None
        # Verify logging was called
        assert mock_log.called


# ============================================================================
# TEST STATE REGISTRY
# ============================================================================

class TestStateRegistry:
    """Test StateRegistry management."""

    def test_registry_initialization(self):
        """StateRegistry should initialize with empty registry."""
        registry = StateRegistry()

        assert isinstance(registry.registry, dict)
        assert len(registry.registry) == 0

    def test_register_state(self):
        """register_state() should add state to registry."""
        registry = StateRegistry()

        def handler(ctx):
            return GlueProcessState.IDLE

        state = State(
            state=GlueProcessState.STARTING,
            handler=handler
        )

        registry.register_state(state)

        assert GlueProcessState.STARTING in registry.registry
        assert registry.registry[GlueProcessState.STARTING] == state

    def test_get_registered_state(self):
        """get() should return registered state."""
        registry = StateRegistry()

        def handler(ctx):
            return GlueProcessState.IDLE

        state = State(
            state=GlueProcessState.STARTING,
            handler=handler
        )
        registry.register_state(state)

        retrieved = registry.get(GlueProcessState.STARTING)

        assert retrieved == state

    def test_get_unregistered_state_returns_none(self):
        """get() should return None for unregistered state."""
        registry = StateRegistry()

        result = registry.get(GlueProcessState.STARTING)

        assert result is None

    def test_register_multiple_states(self):
        """register_state() should handle multiple states."""
        registry = StateRegistry()

        state1 = State(GlueProcessState.IDLE, lambda ctx: None)
        state2 = State(GlueProcessState.STARTING, lambda ctx: None)
        state3 = State(GlueProcessState.COMPLETED, lambda ctx: None)

        registry.register_state(state1)
        registry.register_state(state2)
        registry.register_state(state3)

        assert len(registry.registry) == 3
        assert registry.get(GlueProcessState.IDLE) == state1
        assert registry.get(GlueProcessState.STARTING) == state2
        assert registry.get(GlueProcessState.COMPLETED) == state3


# ============================================================================
# TEST EXECUTABLE STATE MACHINE
# ============================================================================

class TestExecutableStateMachine:
    """Test ExecutableStateMachine core functionality."""

    def test_state_machine_initialization(self, state_registry, transition_rules):
        """ExecutableStateMachine should initialize with initial state."""
        context = ExecutionContext()
        broker = MessageBroker()

        machine = ExecutableStateMachine(
            initial_state=GlueProcessState.IDLE,
            transition_rules=transition_rules,
            state_registry=state_registry,
            broker=broker,
            context=context
        )

        assert machine.current_state == GlueProcessState.IDLE
        assert machine.state == GlueProcessState.IDLE
        assert machine.transition_rules == transition_rules
        assert machine.state_registry == state_registry
        assert machine.broker == broker
        assert machine.context == context

    def test_state_property_returns_current_state(self, mock_state_machine):
        """state property should return current_state."""
        assert mock_state_machine.state == GlueProcessState.IDLE

    def test_can_transition_valid(self, mock_state_machine):
        """can_transition() should return True for valid transitions."""
        # IDLE -> STARTING is valid transition
        assert mock_state_machine.can_transition(GlueProcessState.STARTING) is True

    def test_can_transition_invalid(self, mock_state_machine):
        """can_transition() should return False for invalid transitions."""
        # IDLE -> COMPLETED is invalid (not in transition rules)
        assert mock_state_machine.can_transition(GlueProcessState.COMPLETED) is False

    def test_transition_valid_changes_state(self, mock_state_machine):
        """transition() should change state for valid transitions."""
        initial_state = mock_state_machine.state

        result = mock_state_machine.transition(GlueProcessState.STARTING)

        assert result is True
        assert mock_state_machine.state == GlueProcessState.STARTING
        assert mock_state_machine.state != initial_state

    def test_transition_invalid_keeps_state(self, mock_state_machine):
        """transition() should keep state for invalid transitions."""
        initial_state = mock_state_machine.state

        result = mock_state_machine.transition(GlueProcessState.COMPLETED)

        assert result is False
        assert mock_state_machine.state == initial_state

    def test_transition_publishes_to_broker(self):
        """transition() should publish state to message broker."""
        registry = StateRegistry()
        state = State(GlueProcessState.STARTING, lambda ctx: None)
        registry.register_state(state)

        broker = Mock()
        broker.publish = Mock()

        transition_rules = {
            GlueProcessState.IDLE: {GlueProcessState.STARTING},
        }

        machine = ExecutableStateMachine(
            initial_state=GlueProcessState.IDLE,
            transition_rules=transition_rules,
            state_registry=registry,
            broker=broker,
            context=ExecutionContext()
        )

        machine.transition(GlueProcessState.STARTING)

        broker.publish.assert_called_once_with("STATE MACHINE", GlueProcessState.STARTING)

    def test_transition_calls_exit_handler(self):
        """transition() should call on_exit handler of old state."""
        registry = StateRegistry()

        on_exit_mock = Mock()
        idle_state = State(
            GlueProcessState.IDLE,
            handler=lambda ctx: None,
            on_exit=on_exit_mock
        )
        starting_state = State(GlueProcessState.STARTING, lambda ctx: None)

        registry.register_state(idle_state)
        registry.register_state(starting_state)

        transition_rules = {
            GlueProcessState.IDLE: {GlueProcessState.STARTING},
        }

        context = ExecutionContext()
        machine = ExecutableStateMachine(
            initial_state=GlueProcessState.IDLE,
            transition_rules=transition_rules,
            state_registry=registry,
            context=context
        )

        machine.transition(GlueProcessState.STARTING)

        on_exit_mock.assert_called_once_with(context)

    def test_transition_calls_enter_handler(self):
        """transition() should call on_enter handler of new state."""
        registry = StateRegistry()

        on_enter_mock = Mock()
        idle_state = State(GlueProcessState.IDLE, lambda ctx: None)
        starting_state = State(
            GlueProcessState.STARTING,
            handler=lambda ctx: None,
            on_enter=on_enter_mock
        )

        registry.register_state(idle_state)
        registry.register_state(starting_state)

        transition_rules = {
            GlueProcessState.IDLE: {GlueProcessState.STARTING},
        }

        context = ExecutionContext()
        machine = ExecutableStateMachine(
            initial_state=GlueProcessState.IDLE,
            transition_rules=transition_rules,
            state_registry=registry,
            context=context
        )

        machine.transition(GlueProcessState.STARTING)

        on_enter_mock.assert_called_once_with(context)

    def test_stop_execution_sets_flag(self, mock_state_machine):
        """stop_execution() should set _stop_requested flag."""
        assert mock_state_machine._stop_requested is False

        mock_state_machine.stop_execution()

        assert mock_state_machine._stop_requested is True


# ============================================================================
# TEST EXECUTABLE STATE MACHINE BUILDER
# ============================================================================

class TestExecutableStateMachineBuilder:
    """Test ExecutableStateMachineBuilder pattern."""

    def test_builder_initialization(self):
        """Builder should initialize with None values."""
        builder = ExecutableStateMachineBuilder()

        assert builder._initial_state is None
        assert builder._transition_rules == {}
        assert builder._registry is None
        assert builder._broker is None
        assert builder._context is None

    def test_builder_with_initial_state(self):
        """with_initial_state() should set initial state."""
        builder = ExecutableStateMachineBuilder()

        result = builder.with_initial_state(GlueProcessState.IDLE)

        assert result is builder  # Fluent interface
        assert builder._initial_state == GlueProcessState.IDLE

    def test_builder_with_transition_rules(self, transition_rules):
        """with_transition_rules() should set transition rules."""
        builder = ExecutableStateMachineBuilder()

        result = builder.with_transition_rules(transition_rules)

        assert result is builder
        assert builder._transition_rules == transition_rules

    def test_builder_with_state_registry(self, state_registry):
        """with_state_registry() should set registry."""
        builder = ExecutableStateMachineBuilder()

        result = builder.with_state_registry(state_registry)

        assert result is builder
        assert builder._registry == state_registry

    def test_builder_with_context(self):
        """with_context() should set context."""
        builder = ExecutableStateMachineBuilder()
        context = ExecutionContext()

        result = builder.with_context(context)

        assert result is builder
        assert builder._context == context

    def test_builder_with_message_broker(self):
        """with_message_broker() should set broker."""
        builder = ExecutableStateMachineBuilder()
        broker = MessageBroker()

        result = builder.with_message_broker(broker)

        assert result is builder
        assert builder._broker == broker

    def test_builder_build_creates_machine(self, state_registry, transition_rules):
        """build() should create ExecutableStateMachine."""
        context = ExecutionContext()

        machine = (
            ExecutableStateMachineBuilder()
            .with_initial_state(GlueProcessState.IDLE)
            .with_transition_rules(transition_rules)
            .with_state_registry(state_registry)
            .with_context(context)
            .build()
        )

        assert isinstance(machine, ExecutableStateMachine)
        assert machine.state == GlueProcessState.IDLE
        assert machine.transition_rules == transition_rules
        assert machine.state_registry == state_registry
        assert machine.context == context

    def test_builder_build_requires_initial_state(self, state_registry):
        """build() should raise ValueError if initial_state not set."""
        builder = ExecutableStateMachineBuilder()
        builder.with_state_registry(state_registry)

        with pytest.raises(ValueError, match="Initial state must be set"):
            builder.build()

    def test_builder_build_requires_registry(self):
        """build() should raise ValueError if registry not set."""
        builder = ExecutableStateMachineBuilder()
        builder.with_initial_state(GlueProcessState.IDLE)

        with pytest.raises(ValueError, match="StateRegistry must be set"):
            builder.build()

    def test_builder_fluent_interface(self, state_registry, transition_rules):
        """Builder should support fluent interface chaining."""
        machine = (
            ExecutableStateMachineBuilder()
            .with_initial_state(GlueProcessState.IDLE)
            .with_transition_rules(transition_rules)
            .with_state_registry(state_registry)
            .with_context(ExecutionContext())
            .with_message_broker(MessageBroker())
            .build()
        )

        assert machine.state == GlueProcessState.IDLE


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

class TestStateMachineParametrized:
    """Parametrized tests for state machine behavior."""

    @pytest.mark.parametrize("from_state,to_state,should_succeed", [
        (GlueProcessState.IDLE, GlueProcessState.STARTING, True),
        (GlueProcessState.STARTING, GlueProcessState.MOVING_TO_FIRST_POINT, True),
        (GlueProcessState.IDLE, GlueProcessState.COMPLETED, False),  # Invalid
        (GlueProcessState.IDLE, GlueProcessState.ERROR, True),  # Error always valid
    ])
    def test_various_transitions(self, from_state, to_state, should_succeed, transition_rules, state_registry):
        """Test various state transitions."""
        machine = ExecutableStateMachine(
            initial_state=from_state,
            transition_rules=transition_rules,
            state_registry=state_registry,
            context=ExecutionContext()
        )

        result = machine.can_transition(to_state)

        assert result == should_succeed
