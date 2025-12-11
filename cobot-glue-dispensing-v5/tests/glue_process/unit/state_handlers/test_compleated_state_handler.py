"""
Unit tests for compleated_state_handler (completed state handler).
Tests state completion logic and cleanup operations.
"""

import pytest
from unittest.mock import Mock, MagicMock

from applications.glue_dispensing_application.glue_process.ExecutionContext import ExecutionContext
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from applications.glue_dispensing_application.glue_process.state_handlers.compleated_state_handler import (
    handle_completed_state
)


# ============================================================================
# TEST COMPLETED STATE HANDLER
# ============================================================================

class TestCompletedStateHandler:
    """Test handle_completed_state functionality."""

    def test_completed_state_sets_completion_flag(self, basic_context):
        """handle_completed_state should set operation_just_completed flag."""
        context = basic_context

        handle_completed_state(context)

        assert hasattr(context, 'operation_just_completed')
        assert context.operation_just_completed is True

    def test_completed_state_turns_off_generator(self, basic_context, mock_glue_service):
        """handle_completed_state should turn off generator."""
        context = basic_context
        context.service = mock_glue_service

        handle_completed_state(context)

        mock_glue_service.generatorOff.assert_called_once()

    def test_completed_state_returns_idle(self, basic_context):
        """handle_completed_state should return IDLE as next state."""
        context = basic_context

        next_state = handle_completed_state(context)

        assert next_state == GlueProcessState.IDLE

    def test_completed_state_with_generator_already_off(self, basic_context, mock_glue_service):
        """handle_completed_state should call generatorOff even if generator is already off."""
        context = basic_context
        context.service = mock_glue_service
        mock_glue_service.generatorState.return_value = False  # Already off

        next_state = handle_completed_state(context)

        # Should still call generatorOff (idempotent operation)
        mock_glue_service.generatorOff.assert_called_once()
        assert next_state == GlueProcessState.IDLE

    def test_completed_state_with_state_machine(self, basic_context):
        """handle_completed_state should work with state machine in context."""
        context = basic_context

        # Add state machine mock
        mock_sm = Mock()
        mock_sm.state = GlueProcessState.COMPLETED
        context.state_machine = mock_sm

        next_state = handle_completed_state(context)

        assert next_state == GlueProcessState.IDLE
        assert context.operation_just_completed is True

    def test_completed_state_idempotency(self, basic_context):
        """handle_completed_state should be idempotent (safe to call multiple times)."""
        context = basic_context

        # Call multiple times
        result1 = handle_completed_state(context)
        result2 = handle_completed_state(context)
        result3 = handle_completed_state(context)

        # Should return same result each time
        assert result1 == GlueProcessState.IDLE
        assert result2 == GlueProcessState.IDLE
        assert result3 == GlueProcessState.IDLE
        assert context.operation_just_completed is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestCompletedStateHandlerIntegration:
    """Integration tests for completed state handler."""

    def test_completed_state_full_cleanup(self, basic_context, mock_glue_service):
        """handle_completed_state should perform full cleanup."""
        context = basic_context
        context.service = mock_glue_service
        context.generator_started = True
        context.motor_started = True

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.COMPLETED
        context.state_machine = mock_sm

        next_state = handle_completed_state(context)

        # Verify all cleanup steps
        assert next_state == GlueProcessState.IDLE
        assert context.operation_just_completed is True
        mock_glue_service.generatorOff.assert_called_once()

    def test_completed_state_with_paused_context(self, basic_context):
        """handle_completed_state should work even if operation was paused."""
        context = basic_context
        context.paused_from_state = GlueProcessState.EXECUTING_PATH

        next_state = handle_completed_state(context)

        assert next_state == GlueProcessState.IDLE
        assert context.operation_just_completed is True
        # Paused state doesn't affect completion

    def test_completed_state_after_error_recovery(self, basic_context):
        """handle_completed_state should work after error state."""
        context = basic_context

        mock_sm = Mock()
        mock_sm.state = GlueProcessState.ERROR
        context.state_machine = mock_sm

        next_state = handle_completed_state(context)

        # Should still complete normally
        assert next_state == GlueProcessState.IDLE
        assert context.operation_just_completed is True


# ============================================================================
# EDGE CASES
# ============================================================================

class TestCompletedStateHandlerEdgeCases:
    """Edge case tests for completed state handler."""

    def test_completed_state_without_service(self):
        """handle_completed_state should handle missing service gracefully."""
        context = ExecutionContext()
        context.service = None
        context.state_machine = Mock()

        # This will raise AttributeError trying to call generatorOff on None
        with pytest.raises(AttributeError):
            handle_completed_state(context)

    def test_completed_state_generator_off_exception(self, basic_context, mock_glue_service):
        """handle_completed_state should propagate generatorOff exceptions."""
        context = basic_context
        context.service = mock_glue_service

        # Mock generatorOff to raise exception
        mock_glue_service.generatorOff.side_effect = Exception("Generator hardware fault")

        with pytest.raises(Exception, match="Generator hardware fault"):
            handle_completed_state(context)

    def test_completed_state_minimal_context(self):
        """handle_completed_state should work with minimal context."""
        context = ExecutionContext()
        mock_service = Mock()
        mock_service.generatorOff = Mock()
        context.service = mock_service
        context.state_machine = Mock()

        next_state = handle_completed_state(context)

        assert next_state == GlueProcessState.IDLE
        assert context.operation_just_completed is True
        mock_service.generatorOff.assert_called_once()
