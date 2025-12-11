import pytest
from unittest.mock import Mock, patch

from applications.glue_dispensing_application.glue_process.state_handlers.moving_to_first_point_state_handler import (
    handle_moving_to_first_point_state,
    update_context_after_moving_to_first_point
)
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from applications.glue_dispensing_application.settings.enums import GlueSettingKey


class TestHandleMovingToFirstPointState:

    def test_no_settings_goes_to_error(self, context_with_paths):
        """Should return ERROR if current_settings is None"""
        context = context_with_paths
        context.current_settings = None
        next_state = handle_moving_to_first_point_state(context, resume=False)
        assert next_state == GlueProcessState.ERROR

    @patch(
        "applications.glue_dispensing_application.glue_process.state_handlers.moving_to_first_point_state_handler.CancellationToken")
    def test_robot_reaches_first_point(self, mock_token_cls, context_with_paths):
        """Robot reaches start point -> EXECUTING_PATH"""
        context = context_with_paths
        context.current_settings = {GlueSettingKey.REACH_START_THRESHOLD.value: 1.0}

        # Patch robot_service method
        context.robot_service._waitForRobotToReachPosition = Mock(return_value=True)

        # Setup cancellation token that is never cancelled
        mock_token = Mock()
        mock_token.is_cancelled.return_value = False
        mock_token.get_cancellation_reason.return_value = ""
        mock_token_cls.return_value = mock_token

        next_state = handle_moving_to_first_point_state(context, resume=False)
        assert next_state == GlueProcessState.EXECUTING_PATH

    @patch(
        "applications.glue_dispensing_application.glue_process.state_handlers.moving_to_first_point_state_handler.CancellationToken")
    def test_robot_does_not_reach_first_point(self, mock_token_cls, context_with_paths):
        """Robot does not reach start -> ERROR"""
        context = context_with_paths
        context.current_settings = {GlueSettingKey.REACH_START_THRESHOLD.value: 1.0}

        # Always False so cancellation does not trigger
        mock_token = Mock()
        mock_token.is_cancelled.return_value = False
        mock_token.get_cancellation_reason.return_value = ""
        mock_token_cls.return_value = mock_token

        context.robot_service._waitForRobotToReachPosition = Mock(return_value=False)

        next_state = handle_moving_to_first_point_state(context, resume=False)
        assert next_state == GlueProcessState.ERROR

    @patch(
        "applications.glue_dispensing_application.glue_process.state_handlers.moving_to_first_point_state_handler.CancellationToken")
    def test_movement_cancelled_due_to_paused(self, mock_token_cls, context_with_paths):
        """Movement cancelled due to PAUSED -> should resume with PAUSED"""
        context = context_with_paths
        context.current_settings = {GlueSettingKey.REACH_START_THRESHOLD.value: 1.0}

        mock_token = Mock()
        mock_token.is_cancelled.return_value = True
        mock_token.get_cancellation_reason.return_value = "State changed to PAUSED"
        mock_token_cls.return_value = mock_token

        context.robot_service._waitForRobotToReachPosition = Mock(return_value=True)
        next_state = handle_moving_to_first_point_state(context, resume=True)
        assert next_state == GlueProcessState.PAUSED

    @patch(
        "applications.glue_dispensing_application.glue_process.state_handlers.moving_to_first_point_state_handler.CancellationToken")
    def test_movement_cancelled_due_to_stopped(self, mock_token_cls, context_with_paths):
        """Movement cancelled due to STOPPED -> should go to STOPPED"""
        context = context_with_paths
        context.current_settings = {GlueSettingKey.REACH_START_THRESHOLD.value: 1.0}

        mock_token = Mock()
        mock_token.is_cancelled.return_value = True
        mock_token.get_cancellation_reason.return_value = "State changed to STOPPED"
        mock_token_cls.return_value = mock_token

        context.robot_service._waitForRobotToReachPosition = Mock(return_value=True)
        next_state = handle_moving_to_first_point_state(context, resume=True)
        assert next_state == GlueProcessState.STOPPED

