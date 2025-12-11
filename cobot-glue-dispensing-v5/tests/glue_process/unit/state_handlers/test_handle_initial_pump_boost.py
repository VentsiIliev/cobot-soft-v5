import pytest
from unittest.mock import Mock, patch

from applications.glue_dispensing_application.glue_process.state_handlers.initial_pump_boost_state_handler import \
    handle_pump_initial_boost
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState


class TestHandlePumpInitialBoost:
    """Unit tests for handle_pump_initial_boost."""

    def test_spray_on_motor_not_started_success(self, context_with_paths, logger_context):
        """Motor starts successfully when spray is on and motor not started."""
        context = context_with_paths
        context.spray_on = True
        context.motor_started = False

        # Patch motor address and pump_on
        with patch.object(context, "get_motor_address_for_current_path", return_value=1):
            mock_pump_controller = Mock()
            mock_pump_controller.pump_on.return_value = True
            context.pump_controller = mock_pump_controller

            next_state = handle_pump_initial_boost(context, logger_context)

        assert next_state == GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD
        assert context.motor_started is True
        mock_pump_controller.pump_on.assert_called_once_with(
            context.service, context.robot_service, 1, context.current_settings
        )

    def test_spray_on_motor_not_started_invalid_motor_address(self, context_with_paths, logger_context):
        """Should go to ERROR when motor address is invalid."""
        context = context_with_paths
        context.spray_on = True
        context.motor_started = False

        with patch.object(context, "get_motor_address_for_current_path", return_value=-1):
            next_state = handle_pump_initial_boost(context, logger_context)

        assert next_state == GlueProcessState.ERROR
        assert context.motor_started is False

    def test_spray_on_motor_not_started_motor_fails(self, context_with_paths, logger_context):
        """Should go to ERROR if pump_on returns False."""
        context = context_with_paths
        context.spray_on = True
        context.motor_started = False

        with patch.object(context, "get_motor_address_for_current_path", return_value=1):
            mock_pump_controller = Mock()
            mock_pump_controller.pump_on.return_value = False
            context.pump_controller = mock_pump_controller

            next_state = handle_pump_initial_boost(context, logger_context)

        assert next_state == GlueProcessState.ERROR
        assert context.motor_started is False
        mock_pump_controller.pump_on.assert_called_once_with(
            context.service, context.robot_service, 1, context.current_settings
        )

    def test_spray_off_or_motor_already_started(self, context_with_paths, logger_context):
        """Should skip boost when spray is off or motor already started."""
        context = context_with_paths
        context.spray_on = False
        context.motor_started = False

        next_state = handle_pump_initial_boost(context, logger_context)
        assert next_state == GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD
        assert context.motor_started is False

        # Case: motor already started
        context.motor_started = True
        context.spray_on = True
        next_state = handle_pump_initial_boost(context, logger_context)
        assert next_state == GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD
        assert context.motor_started is True
