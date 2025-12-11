import pytest
from unittest.mock import Mock, patch
from applications.glue_dispensing_application.glue_process.state_handlers.sending_path_to_robot_state_handler import (
    handle_send_path_to_robot, update_context_from_handler_result
)
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from core.model.settings.RobotConfigKey import RobotSettingKey

class TestHandleSendingPathToRobotState:

    def test_sending_path_happy_path(self, context_with_paths, logger_context):
        context = context_with_paths
        context.current_settings = {RobotSettingKey.VELOCITY.value: 10, RobotSettingKey.ACCELERATION.value: 30}

        # Mock state_machine
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        context.state_machine = mock_sm

        # Patch move_liner to succeed
        context.robot_service.robot.move_liner = Mock(return_value=0)

        next_state = handle_send_path_to_robot(context, logger_context)
        assert next_state == GlueProcessState.WAIT_FOR_PATH_COMPLETION
        context.robot_service.robot.move_liner.assert_called()

    def test_robot_service_exception(self, context_with_paths, logger_context):
        context = context_with_paths
        context.current_settings = {RobotSettingKey.VELOCITY.value: 10, RobotSettingKey.ACCELERATION.value: 30}

        # Mock state_machine
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        context.state_machine = mock_sm

        # Patch move_liner to raise exception
        context.robot_service.robot.move_liner = Mock(side_effect=Exception("Robot error"))

        next_state = handle_send_path_to_robot(context, logger_context)
        assert next_state == GlueProcessState.ERROR

    def test_move_liner_nonzero_return(self, context_with_paths, logger_context):
        context = context_with_paths
        context.current_settings = {RobotSettingKey.VELOCITY.value: 10, RobotSettingKey.ACCELERATION.value: 30}

        # Mock state_machine
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        context.state_machine = mock_sm

        # Patch move_liner to return error code
        context.robot_service.robot.move_liner = Mock(return_value=1)

        next_state = handle_send_path_to_robot(context, logger_context)
        assert next_state == GlueProcessState.ERROR

    def test_empty_path(self, context_with_paths, logger_context):
        context = context_with_paths
        context.paths = []
        context.current_path = []
        context.current_settings = {RobotSettingKey.VELOCITY.value: 10, RobotSettingKey.ACCELERATION.value: 30}

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        context.state_machine = mock_sm

        next_state = handle_send_path_to_robot(context, logger_context)
        # Empty path sends nothing, handler still returns WAIT_FOR_PATH_COMPLETION
        assert next_state == GlueProcessState.WAIT_FOR_PATH_COMPLETION

    def test_paused_mid_path(self, context_with_paths, logger_context):
        context = context_with_paths
        context.current_settings = {RobotSettingKey.VELOCITY.value: 10, RobotSettingKey.ACCELERATION.value: 30}

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.PAUSED
        context.state_machine = mock_sm

        # Patch move_liner
        context.robot_service.robot.move_liner = Mock(return_value=0)

        next_state = handle_send_path_to_robot(context, logger_context)
        assert next_state == GlueProcessState.PAUSED

    def test_stopped_mid_path(self, context_with_paths, logger_context):
        context = context_with_paths
        context.current_settings = {RobotSettingKey.VELOCITY.value: 10, RobotSettingKey.ACCELERATION.value: 30}

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.STOPPED
        context.state_machine = mock_sm

        # Patch move_liner
        context.robot_service.robot.move_liner = Mock(return_value=0)

        next_state = handle_send_path_to_robot(context, logger_context)
        assert next_state == GlueProcessState.STOPPED

    def test_update_context_function(self, context_with_paths):
        context = context_with_paths
        result = Mock()
        result.next_point_index = 5
        result.next_path_index = 1
        result.next_path = ["dummy"]
        result.next_settings = {"velocity": 5}
        update_context_from_handler_result(context, result)

        assert context.current_point_index == 5
        assert context.current_path_index == 1
        assert context.current_path == ["dummy"]
        assert context.current_settings == {"velocity": 5}
