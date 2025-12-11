"""
Unit tests for pause_operation.
Tests pause functionality, robot stop, motor shutdown, and resume toggle.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from applications.glue_dispensing_application.glue_process.ExecutionContext import ExecutionContext
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from applications.glue_dispensing_application.glue_process.state_handlers.pause_operation import pause_operation
from applications.glue_dispensing_application.glue_process.PumpController import PumpController
from applications.glue_dispensing_application.settings.enums.GlueSettingKey import GlueSettingKey
from modules.utils.custom_logging import LoggerContext


# ============================================================================
# TEST PAUSE OPERATION
# ============================================================================

class TestPauseOperation:
    """Test pause_operation basic functionality."""

    def test_pause_from_executing_state(self, context_with_paths, mock_glue_service, mock_robot_service, logger_context):
        """pause_operation should pause from EXECUTING_PATH state."""
        context = context_with_paths
        context.service = mock_glue_service
        context.robot_service = mock_robot_service

        # Setup state machine
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        # Setup pump controller
        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        # Mock glue dispensing operation
        mock_operation = Mock()
        mock_operation.resume = Mock(return_value=(True, "Resumed"))

        success, message = pause_operation(mock_operation, context, logger_context)

        assert success is True
        assert "paused" in message.lower()
        mock_sm.transition.assert_called_once_with(GlueProcessState.PAUSED)
        assert context.paused_from_state == GlueProcessState.EXECUTING_PATH

    def test_pause_stops_robot_motion(self, context_with_paths, mock_robot_service, logger_context):
        """pause_operation should stop robot motion."""
        context = context_with_paths
        context.robot_service = mock_robot_service

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.MOVING_TO_FIRST_POINT
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        mock_operation = Mock()
        pause_operation(mock_operation, context, logger_context)

        mock_robot_service.stop_motion.assert_called_once()

    def test_pause_turns_off_pump_and_generator(self, context_with_paths, mock_glue_service, logger_context):
        """pause_operation should turn off pump and generator."""
        context = context_with_paths
        context.service = mock_glue_service

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        mock_operation = Mock()
        pause_operation(mock_operation, context, logger_context)

        # Verify pump off was called
        mock_glue_service.motorOff.assert_called()
        # Verify generator off was called
        mock_glue_service.generatorOff.assert_called_once()

    def test_pause_when_already_paused_calls_resume(self, basic_context, logger_context):
        """pause_operation when already PAUSED should call resume."""
        context = basic_context

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.PAUSED
        context.state_machine = mock_sm

        mock_operation = Mock()
        mock_operation.resume = Mock(return_value=(True, "Resumed successfully"))

        success, message = pause_operation(mock_operation, context, logger_context)

        mock_operation.resume.assert_called_once()
        assert success is True
        assert "Resumed" in message

    def test_pause_saves_paused_from_state(self, context_with_paths, logger_context):
        """pause_operation should save the state from which pause was triggered."""
        context = context_with_paths

        test_states = [
            GlueProcessState.MOVING_TO_FIRST_POINT,
            GlueProcessState.EXECUTING_PATH,
            GlueProcessState.WAIT_FOR_PATH_COMPLETION,
            GlueProcessState.SENDING_PATH_POINTS,
        ]

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        for state in test_states:
            mock_sm = Mock()
            mock_sm.state = state
            mock_sm.transition = Mock(return_value=True)
            context.state_machine = mock_sm

            mock_operation = Mock()
            pause_operation(mock_operation, context, logger_context)

            assert context.paused_from_state == state


# ============================================================================
# TEST PUMP THREAD HANDLING
# ============================================================================

class TestPauseWithPumpThread:
    """Test pause_operation with active pump adjustment thread."""

    def test_pause_with_active_pump_thread(self, context_with_paths, logger_context):
        """pause_operation should capture pump thread progress."""
        context = context_with_paths

        # Create active pump thread mock
        mock_thread = Mock()
        mock_thread.is_alive = Mock(return_value=True)
        context.pump_thread = mock_thread

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.WAIT_FOR_PATH_COMPLETION
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        mock_operation = Mock()
        success, message = pause_operation(mock_operation, context, logger_context)

        assert success is True
        # Pump thread should still be alive (will be stopped by thread itself detecting PAUSED state)
        assert mock_thread.is_alive.called

    def test_pause_with_no_pump_thread(self, context_with_paths, logger_context):
        """pause_operation should work without pump thread."""
        context = context_with_paths
        context.pump_thread = None

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        mock_operation = Mock()
        success, message = pause_operation(mock_operation, context, logger_context)

        assert success is True

    def test_pause_with_inactive_pump_thread(self, context_with_paths, logger_context):
        """pause_operation should handle inactive pump thread."""
        context = context_with_paths

        mock_thread = Mock()
        mock_thread.is_alive = Mock(return_value=False)  # Thread not active
        context.pump_thread = mock_thread

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        mock_operation = Mock()
        success, message = pause_operation(mock_operation, context, logger_context)

        assert success is True


# ============================================================================
# TEST ERROR HANDLING
# ============================================================================

class TestPauseOperationErrorHandling:
    """Test pause_operation error handling."""

    def test_pause_without_state_machine(self, basic_context, logger_context):
        """pause_operation should fail gracefully without state machine."""
        context = basic_context
        context.state_machine = None

        mock_operation = Mock()
        success, message = pause_operation(mock_operation, context, logger_context)

        assert success is False
        assert "not initialized" in message.lower()

    def test_pause_with_invalid_motor_address(self, context_with_paths, logger_context):
        """pause_operation should raise error for invalid motor address."""
        context = context_with_paths
        context.current_settings = {GlueSettingKey.GLUE_TYPE.value: "InvalidType"}

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        mock_operation = Mock()

        with pytest.raises(RuntimeError, match="Invalid motor address"):
            pause_operation(mock_operation, context, logger_context)

    def test_pause_robot_stop_exception(self, context_with_paths, mock_robot_service, logger_context):
        """pause_operation should handle robot stop exceptions gracefully."""
        context = context_with_paths
        context.robot_service = mock_robot_service

        # Mock robot stop to raise exception
        mock_robot_service.stop_motion.side_effect = Exception("Robot communication error")

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        mock_operation = Mock()

        # Should not raise - exception is caught and logged
        success, message = pause_operation(mock_operation, context, logger_context)

        # Pause should still succeed despite robot stop error
        assert success is True

    def test_pause_cannot_transition_to_paused(self, context_with_paths, logger_context):
        """pause_operation should fail if transition to PAUSED is not allowed."""
        context = context_with_paths

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.COMPLETED
        mock_sm.transition = Mock(return_value=False)  # Transition fails
        context.state_machine = mock_sm

        mock_operation = Mock()
        success, message = pause_operation(mock_operation, context, logger_context)

        assert success is False
        assert "cannot pause" in message.lower()


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

class TestPauseOperationParametrized:
    """Parametrized tests for pause_operation."""

    @pytest.mark.parametrize("state", [
        GlueProcessState.MOVING_TO_FIRST_POINT,
        GlueProcessState.EXECUTING_PATH,
        GlueProcessState.WAIT_FOR_PATH_COMPLETION,
        GlueProcessState.SENDING_PATH_POINTS,
        GlueProcessState.TRANSITION_BETWEEN_PATHS,
    ])
    def test_pause_from_various_states(self, context_with_paths, state, logger_context):
        """pause_operation should work from all pausable states."""
        context = context_with_paths

        mock_sm = Mock()
        mock_sm.state = state
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        context.pump_controller = pump_controller

        mock_operation = Mock()
        success, message = pause_operation(mock_operation, context, logger_context)

        assert success is True
        assert context.paused_from_state == state
        mock_sm.transition.assert_called_once_with(GlueProcessState.PAUSED)
