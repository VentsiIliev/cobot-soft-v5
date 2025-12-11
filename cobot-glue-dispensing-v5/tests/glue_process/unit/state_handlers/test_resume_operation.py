import pytest
from unittest.mock import Mock

from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from applications.glue_dispensing_application.glue_process.state_handlers.resume_operation import resume_operation


class TestResumeOperation:
    """Unit tests for resume_operation."""

    def test_resume_without_state_machine(self, basic_context, logger_context):
        """Should fail if state machine is not initialized."""
        context = basic_context
        context.state_machine = None

        success, message = resume_operation(context, logger_context)
        assert success is False
        assert "not initialized" in message.lower()

    def test_resume_not_paused_state(self, basic_context, logger_context):
        """Should fail if current state is not PAUSED."""
        context = basic_context
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.EXECUTING_PATH
        context.state_machine = mock_sm

        success, message = resume_operation(context, logger_context)
        assert success is False
        assert "not in paused state" in message.lower()

    def test_resume_invalid_context(self, basic_context, logger_context):
        """Should fail if execution context is invalid."""
        context = basic_context
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.PAUSED
        context.state_machine = mock_sm

        # Patch has_valid_context to return False
        context.has_valid_context = Mock(return_value=False)

        success, message = resume_operation(context, logger_context)
        assert success is False
        assert "no execution context" in message.lower()

    def test_resume_successful_transition(self, basic_context, logger_context):
        """Should resume successfully when state is PAUSED and context is valid."""
        context = basic_context
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.PAUSED
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        context.has_valid_context = Mock(return_value=True)

        success, message = resume_operation(context, logger_context)

        assert success is True
        assert "resumed" in message.lower()
        assert context.is_resuming is True
        mock_sm.transition.assert_called_once_with(GlueProcessState.STARTING)

    def test_resume_failed_transition(self, basic_context, logger_context):
        """Should fail if transition to STARTING is not allowed."""
        context = basic_context
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.PAUSED
        mock_sm.transition = Mock(return_value=False)
        context.state_machine = mock_sm

        context.has_valid_context = Mock(return_value=True)

        success, message = resume_operation(context, logger_context)

        assert success is False
        assert "invalid state transition" in message.lower()
        assert context.is_resuming is True  # Flag is set even if transition fails

    def test_resume_preserves_context(self, basic_context, logger_context):
        """
        Simulate resuming operation and ensure context is preserved.
        - State machine is PAUSED
        - Execution context is valid
        - After resume, is_resuming is True
        - State machine transitions to STARTING
        """
        context = basic_context

        # Mock state machine and valid context
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.PAUSED
        mock_sm.transition = Mock(return_value=True)
        context.state_machine = mock_sm

        # Simulate context check
        context.has_valid_context = Mock(return_value=True)

        # Pre-set some context values
        context.some_data = "important_value"

        # Call resume_operation
        success, message = resume_operation(context, logger_context)

        # Assertions
        assert success is True
        assert "resumed" in message.lower()
        assert context.is_resuming is True
        # Context data is preserved
        assert context.some_data == "important_value"
        # State machine was instructed to transition to STARTING
        mock_sm.transition.assert_called_once_with(GlueProcessState.STARTING)
