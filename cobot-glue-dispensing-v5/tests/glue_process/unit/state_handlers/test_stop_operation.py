import pytest
from unittest.mock import Mock, patch

from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from applications.glue_dispensing_application.glue_process.state_handlers.stop_operation import stop_operation
from applications.glue_dispensing_application.glue_process.PumpController import PumpController


class TestStopOperation:
    """Unit tests for stop_operation."""

    def test_stop_from_executing_state(self, context_with_paths, mock_robot_service, mock_glue_service, logger_context):
        """stop_operation should stop from a normal state."""
        context = context_with_paths
        context.robot_service = mock_robot_service
        context.service = mock_glue_service

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        context.pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)

        mock_operation = Mock()

        with patch.object(context, "get_motor_address_for_current_path", return_value=1):
            success, message = stop_operation(mock_operation, context, logger_context)

        assert success is True
        assert "stopped" in message.lower()
        assert context.operation_just_completed is True
        mock_robot_service.stop_motion.assert_called_once()
        mock_glue_service.generatorOff.assert_called()

    def test_stop_without_state_machine(self, basic_context, logger_context):
        """stop_operation should fail if state machine not initialized."""
        context = basic_context
        context.state_machine = None
        mock_operation = Mock()

        success, message = stop_operation(mock_operation, context, logger_context)

        assert success is False
        assert "not initialized" in message.lower()

    def test_stop_robot_stop_exception(self, context_with_paths, mock_robot_service, mock_glue_service, logger_context):
        """stop_operation should handle robot stop exceptions gracefully."""
        context = context_with_paths
        context.robot_service = mock_robot_service
        context.service = mock_glue_service

        # Robot stop raises exception
        mock_robot_service.stop_motion.side_effect = Exception("Robot error")

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        context.pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        mock_operation = Mock()

        with patch.object(context, "get_motor_address_for_current_path", return_value=1):
            success, message = stop_operation(mock_operation, context, logger_context)

        assert success is True  # Exception is caught
        assert context.operation_just_completed is True

    def test_stop_invalid_motor_address(self, context_with_paths, logger_context):
        """stop_operation should raise RuntimeError for invalid motor address."""
        context = context_with_paths

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        context.pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        mock_operation = Mock()

        # Patch motor address to -1 to trigger RuntimeError
        with patch.object(context, "get_motor_address_for_current_path", return_value=-1):
            with pytest.raises(RuntimeError, match="Invalid motor address"):
                stop_operation(mock_operation, context, logger_context)

    def test_stop_transition_fails(self, context_with_paths, logger_context):
        """stop_operation should return False if transition to STOPPED fails."""
        context = context_with_paths

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.COMPLETED
        mock_sm.transition = Mock(return_value=False)  # Transition fails
        context.state_machine = mock_sm

        context.pump_controller = PumpController(use_segment_settings=True, logger_context=logger_context)
        mock_operation = Mock()

        success, message = stop_operation(mock_operation, context, logger_context)

        assert success is False
        assert "cannot stop" in message.lower()

    def test_motor_and_generator_off_called(self, context_with_paths, mock_robot_service, mock_glue_service,
                                            logger_context):
        """Verify that pump_off and generatorOff are called when stopping operation."""
        context = context_with_paths
        context.robot_service = mock_robot_service
        context.service = mock_glue_service

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        # Patch pump_controller to track pump_off calls
        mock_pump_controller = Mock(spec=PumpController)
        context.pump_controller = mock_pump_controller

        mock_operation = Mock()

        # Patch motor address to a valid value
        with patch.object(context, "get_motor_address_for_current_path", return_value=1):
            success, message = stop_operation(mock_operation, context, logger_context)

        assert success is True
        # Check that pump_off was called with correct arguments
        mock_pump_controller.pump_off.assert_called_with(
            context.service, context.robot_service, 1, context.current_settings
        )
        # Check that generatorOff was called
        mock_glue_service.generatorOff.assert_called()

    def test_motor_off_called_multiple_times(self, context_with_paths, mock_robot_service, mock_glue_service,
                                             logger_context):
        """stop_operation calls pump_off twice as in original implementation."""
        context = context_with_paths
        context.robot_service = mock_robot_service
        context.service = mock_glue_service

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        mock_pump_controller = Mock(spec=PumpController)
        context.pump_controller = mock_pump_controller

        mock_operation = Mock()

        with patch.object(context, "get_motor_address_for_current_path", return_value=1):
            stop_operation(mock_operation, context, logger_context)

        # pump_off should be called **twice** according to the implementation
        assert mock_pump_controller.pump_off.call_count == 2
        # generatorOff should also be called at least once
        assert mock_glue_service.generatorOff.call_count >= 1

    def test_generator_off_called_even_on_invalid_motor(self, context_with_paths, mock_robot_service, mock_glue_service,
                                                        logger_context):
        """Ensure generatorOff is called even if the motor address is invalid (RuntimeError)."""
        context = context_with_paths
        context.robot_service = mock_robot_service
        context.service = mock_glue_service

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        mock_pump_controller = Mock(spec=PumpController)
        context.pump_controller = mock_pump_controller

        mock_operation = Mock()

        # Patch motor address to -1 to trigger RuntimeError
        with patch.object(context, "get_motor_address_for_current_path", return_value=-1):
            # Use try/except to catch the expected RuntimeError
            with pytest.raises(RuntimeError):
                stop_operation(mock_operation, context, logger_context)

        # GeneratorOff should still be called
        mock_glue_service.generatorOff.assert_called()

