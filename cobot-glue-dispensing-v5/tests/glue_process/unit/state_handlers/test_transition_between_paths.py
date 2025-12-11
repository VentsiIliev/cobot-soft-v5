import pytest
from unittest.mock import Mock, patch

from applications.glue_dispensing_application.glue_process.state_handlers.transition_between_paths_state_handler import \
    handle_transition_between_paths
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState



class TestHandleTransitionBetweenPaths:
    """Unit tests for handle_transition_between_paths."""

    @pytest.fixture
    def base_context(self):
        """Setup a basic context mock."""
        context = Mock()
        context.current_path_index = 0
        context.current_point_index = 0
        context.paths = ["path1", "path2"]
        context.motor_started = True
        context.spray_on = True
        context.current_settings = {"some_setting": 1}
        context.pump_controller = Mock()
        context.service = Mock()
        context.robot_service = Mock()
        context.robot_service.message_publisher.publish_trajectory_break_topic = Mock()
        context.get_motor_address_for_current_path = Mock(return_value=1)
        return context

    def test_turn_off_motor_between_paths_success(self, base_context, logger_context):
        """Motor should be turned off if motor started and spray is on."""
        context = base_context

        next_state = handle_transition_between_paths(context, logger_context, turn_off_pump_between_paths=True)

        # Motor turned off
        context.pump_controller.pump_off.assert_called_once_with(
            context.service, context.robot_service, 1, context.current_settings
        )
        # Motor started flag reset
        assert context.motor_started is False
        # Next state is STARTING (next path exists)
        assert next_state == GlueProcessState.STARTING
        # Path index incremented
        assert context.current_path_index == 1
        # Point index reset
        assert context.current_point_index == 0
        # Trajectory break topic called
        context.robot_service.message_publisher.publish_trajectory_break_topic.assert_called_once()

    def test_turn_off_motor_between_paths_skipped_if_not_started(self, base_context, logger_context):
        """Motor off should not be called if motor_started is False."""
        context = base_context
        context.motor_started = False

        next_state = handle_transition_between_paths(context, logger_context, turn_off_pump_between_paths=True)

        context.pump_controller.pump_off.assert_not_called()
        assert next_state == GlueProcessState.STARTING

    def test_turn_off_motor_between_paths_skipped_if_spray_off(self, base_context, logger_context):
        """Motor off should not be called if spray_on is False."""
        context = base_context
        context.spray_on = False

        next_state = handle_transition_between_paths(context, logger_context, turn_off_pump_between_paths=True)

        context.pump_controller.pump_off.assert_not_called()
        assert next_state == GlueProcessState.STARTING

    def test_motor_address_invalid(self, base_context, logger_context):
        """Should log error and raise RuntimeError if the motor address is invalid (-1)."""
        context = base_context
        context.get_motor_address_for_current_path = Mock(return_value=-1)

        # RuntimeError should be raised
        with pytest.raises(RuntimeError, match="Invalid motor address"):
            handle_transition_between_paths(context, logger_context, turn_off_pump_between_paths=True)

        # Pump off should not be called
        context.pump_controller.pump_off.assert_not_called()

    def test_turn_off_pump_between_paths_false(self, base_context, logger_context):
        """Motor off is skipped if turn_off_pump_between_paths is False."""
        context = base_context

        next_state = handle_transition_between_paths(context, logger_context, turn_off_pump_between_paths=False)

        context.pump_controller.pump_off.assert_not_called()
        # Path index incremented
        assert context.current_path_index == 1
        assert next_state == GlueProcessState.STARTING

    def test_all_paths_completed_transitions_to_completed(self, base_context, logger_context):
        """Should transition to COMPLETED if next_path_index >= len(paths)."""
        context = base_context
        context.current_path_index = len(context.paths) - 1  # last path

        next_state = handle_transition_between_paths(context, logger_context, turn_off_pump_between_paths=True)

        assert next_state == GlueProcessState.COMPLETED
        # Path index incremented
        assert context.current_path_index == len(context.paths)
