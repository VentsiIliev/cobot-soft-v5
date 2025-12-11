"""
Unit tests for ExecutionContext.
Tests context initialization, reset, progress management, and motor address resolution.
"""

import pytest
import threading
from unittest.mock import Mock, MagicMock, patch

from applications.glue_dispensing_application.glue_process.ExecutionContext import ExecutionContext
from applications.glue_dispensing_application.settings.enums import GlueSettingKey


# ============================================================================
# TEST INITIALIZATION
# ============================================================================

class TestExecutionContextInitialization:
    """Test ExecutionContext initialization and default values."""

    def test_context_initializes_with_reset(self):
        """Context should call reset() during initialization."""
        context = ExecutionContext()

        # Verify default values from reset()
        assert context.paths is None
        assert context.spray_on is False
        assert context.service is None
        assert context.robot_service is None
        assert context.state_machine is None
        assert context.current_path_index == 0
        assert context.current_point_index == 0
        assert context.target_point_index == 0
        assert context.is_resuming is False
        assert context.generator_started is False
        assert context.motor_started is False
        assert context.current_settings is None
        assert context.current_path is None
        assert context.pump_controller is None
        assert context.pump_thread is None
        assert context.pump_ready_event is None

    def test_paused_from_state_initialized_to_none(self):
        """paused_from_state should be set to None after __init__."""
        context = ExecutionContext()
        assert context.paused_from_state is None

    def test_generator_delay_initialized_to_zero(self):
        """generator_to_glue_delay should be 0 by default."""
        context = ExecutionContext()
        assert context.generator_to_glue_delay == 0


# ============================================================================
# TEST RESET FUNCTIONALITY
# ============================================================================

class TestResetFunctionality:
    """Test ExecutionContext reset() method."""

    def test_reset_clears_all_state(self):
        """reset() should clear all context state to defaults."""
        context = ExecutionContext()

        # Set some state
        context.paths = [([1, 2, 3], {})]
        context.spray_on = True
        context.current_path_index = 5
        context.current_point_index = 10
        context.is_resuming = True
        context.motor_started = True
        context.generator_started = True

        # Reset
        context.reset()

        # Verify all cleared
        assert context.paths is None
        assert context.spray_on is False
        assert context.current_path_index == 0
        assert context.current_point_index == 0
        assert context.is_resuming is False
        assert context.motor_started is False
        assert context.generator_started is False
        assert context.paused_from_state is None

    def test_reset_can_be_called_multiple_times(self):
        """reset() should be idempotent."""
        context = ExecutionContext()

        context.reset()
        context.reset()
        context.reset()

        assert context.paths is None
        assert context.current_path_index == 0

    def test_reset_preserves_object_identity(self):
        """reset() should not create a new object."""
        context = ExecutionContext()
        original_id = id(context)

        context.reset()

        assert id(context) == original_id


# ============================================================================
# TEST PROGRESS MANAGEMENT
# ============================================================================

class TestProgressManagement:
    """Test progress saving and validation."""

    def test_save_progress_sets_indices(self):
        """save_progress() should update path and point indices."""
        context = ExecutionContext()

        context.save_progress(path_index=2, point_index=15)

        assert context.current_path_index == 2
        assert context.current_point_index == 15

    def test_save_progress_with_zero_indices(self):
        """save_progress() should accept zero values."""
        context = ExecutionContext()

        context.save_progress(path_index=0, point_index=0)

        assert context.current_path_index == 0
        assert context.current_point_index == 0

    def test_has_valid_context_returns_true_with_paths(self):
        """has_valid_context() should return True when paths exist."""
        context = ExecutionContext()
        context.paths = [([1, 2, 3], {"GLUE_TYPE": "TypeA"})]

        assert context.has_valid_context() is True

    def test_has_valid_context_returns_false_without_paths(self):
        """has_valid_context() should return False when paths is None."""
        context = ExecutionContext()
        context.paths = None

        assert context.has_valid_context() is False

    def test_has_valid_context_returns_false_with_empty_paths(self):
        """has_valid_context() should return False for empty paths list."""
        context = ExecutionContext()
        context.paths = []

        assert context.has_valid_context() is False

    def test_has_valid_context_with_multiple_paths(self):
        """has_valid_context() should return True for multiple paths."""
        context = ExecutionContext()
        context.paths = [
            ([1, 2], {"GLUE_TYPE": "TypeA"}),
            ([3, 4], {"GLUE_TYPE": "TypeB"}),
        ]

        assert context.has_valid_context() is True


# ============================================================================
# TEST MOTOR ADDRESS RESOLUTION
# ============================================================================

class TestMotorAddressResolution:
    """Test motor address resolution from glue cell configuration."""

    def test_motor_address_with_no_settings_returns_default(self):
        """get_motor_address_for_current_path() returns 0 when no settings."""
        context = ExecutionContext()
        context.current_settings = None

        result = context.get_motor_address_for_current_path()

        assert result == 0

    def test_motor_address_with_missing_glue_type_returns_minus_one(self):
        """get_motor_address_for_current_path() returns -1 when no glue type in settings."""
        context = ExecutionContext()
        context.current_settings = {"MOTOR_SPEED": 10000}  # No GLUE_TYPE

        result = context.get_motor_address_for_current_path()

        assert result == -1

    @patch('modules.shared.tools.glue_monitor_system.glue_cells_manager.GlueCellsManagerSingleton')
    def test_motor_address_resolution_success(self, mock_cells_manager):
        """get_motor_address_for_current_path() returns correct address for valid glue type."""
        context = ExecutionContext()
        context.current_settings = {GlueSettingKey.GLUE_TYPE.value: "TypeA"}

        # Mock glue cells
        mock_cell_a = Mock()
        mock_cell_a.glueType = "TypeA"
        mock_cell_a.motor_address = 42

        mock_cell_b = Mock()
        mock_cell_b.glueType = "TypeB"
        mock_cell_b.motor_address = 99

        mock_manager = Mock()
        mock_manager.cells = [mock_cell_a, mock_cell_b]
        mock_cells_manager.get_instance.return_value = mock_manager

        result = context.get_motor_address_for_current_path()

        assert result == 42

    @patch('modules.shared.tools.glue_monitor_system.glue_cells_manager.GlueCellsManagerSingleton')
    def test_motor_address_glue_type_not_found(self, mock_cells_manager):
        """get_motor_address_for_current_path() returns -1 when glue type not in cells."""
        context = ExecutionContext()
        context.current_settings = {GlueSettingKey.GLUE_TYPE.value: "TypeX"}  # Not in cells

        # Mock glue cells (without TypeX)
        mock_cell = Mock()
        mock_cell.glueType = "TypeA"
        mock_cell.motor_address = 42

        mock_manager = Mock()
        mock_manager.cells = [mock_cell]
        mock_cells_manager.get_instance.return_value = mock_manager

        result = context.get_motor_address_for_current_path()

        assert result == -1

    @patch('modules.shared.tools.glue_monitor_system.glue_cells_manager.GlueCellsManagerSingleton')
    def test_motor_address_exception_handling(self, mock_cells_manager):
        """get_motor_address_for_current_path() returns 0 on exception."""
        context = ExecutionContext()
        context.current_settings = {GlueSettingKey.GLUE_TYPE.value: "TypeA"}

        # Mock exception
        mock_cells_manager.get_instance.side_effect = Exception("Cell manager error")

        result = context.get_motor_address_for_current_path()

        assert result == 0


# ============================================================================
# TEST DEBUG SERIALIZATION
# ============================================================================

class TestDebugSerialization:
    """Test to_debug_dict() serialization for debugging."""

    def test_to_debug_dict_with_empty_context(self):
        """to_debug_dict() should work with empty/default context."""
        context = ExecutionContext()

        debug_dict = context.to_debug_dict()

        assert isinstance(debug_dict, dict)
        assert debug_dict["current_path_index"] == 0
        assert debug_dict["current_point_index"] == 0
        assert debug_dict["target_point_index"] == 0
        assert debug_dict["total_paths"] == 0
        assert debug_dict["current_path_length"] == 0
        assert debug_dict["spray_on"] is False
        assert debug_dict["motor_started"] is False
        assert debug_dict["generator_started"] is False
        assert debug_dict["is_resuming"] is False
        assert debug_dict["current_state"] == "None"
        assert debug_dict["paused_from_state"] == "None"
        assert debug_dict["pump_thread_alive"] is False
        assert debug_dict["pump_ready_event_set"] is False
        assert debug_dict["has_current_settings"] is False
        assert debug_dict["settings_keys"] == []
        assert debug_dict["has_glue_service"] is False
        assert debug_dict["has_robot_service"] is False
        assert debug_dict["has_pump_controller"] is False

    def test_to_debug_dict_with_populated_context(self, context_with_paths, mock_robot_service, mock_glue_service):
        """to_debug_dict() should include all populated data."""
        context = context_with_paths
        context.spray_on = True
        context.motor_started = True
        context.generator_started = True
        context.is_resuming = True
        context.current_path_index = 1
        context.current_point_index = 2
        context.target_point_index = 3

        # Add services
        context.robot_service = mock_robot_service
        context.service = mock_glue_service
        context.pump_controller = Mock()

        debug_dict = context.to_debug_dict()

        assert debug_dict["current_path_index"] == 1
        assert debug_dict["current_point_index"] == 2
        assert debug_dict["target_point_index"] == 3
        assert debug_dict["total_paths"] == 1
        assert debug_dict["current_path_length"] == 3
        assert debug_dict["spray_on"] is True
        assert debug_dict["motor_started"] is True
        assert debug_dict["generator_started"] is True
        assert debug_dict["is_resuming"] is True
        assert debug_dict["has_current_settings"] is True
        assert debug_dict["has_glue_service"] is True
        assert debug_dict["has_robot_service"] is True
        assert debug_dict["has_pump_controller"] is True

    def test_to_debug_dict_includes_settings_keys(self):
        """to_debug_dict() should list current_settings keys."""
        context = ExecutionContext()
        context.current_settings = {
            "GLUE_TYPE": "TypeA",
            "MOTOR_SPEED": 10000,
            "VELOCITY": 50.0
        }

        debug_dict = context.to_debug_dict()

        assert debug_dict["has_current_settings"] is True
        assert "GLUE_TYPE" in debug_dict["settings_keys"]
        assert "MOTOR_SPEED" in debug_dict["settings_keys"]
        assert "VELOCITY" in debug_dict["settings_keys"]

    def test_to_debug_dict_with_state_machine(self):
        """to_debug_dict() should serialize state_machine state."""
        from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState

        context = ExecutionContext()
        context.state_machine = Mock()
        context.state_machine.state = GlueProcessState.EXECUTING_PATH
        context.paused_from_state = GlueProcessState.MOVING_TO_FIRST_POINT

        debug_dict = context.to_debug_dict()

        assert "EXECUTING_PATH" in debug_dict["current_state"]
        assert "MOVING_TO_FIRST_POINT" in debug_dict["paused_from_state"]

    def test_to_debug_dict_with_pump_thread(self):
        """to_debug_dict() should include pump thread status."""
        context = ExecutionContext()

        # Create real thread and event for testing
        context.pump_thread = Mock()
        context.pump_thread.is_alive.return_value = True

        context.pump_ready_event = threading.Event()
        context.pump_ready_event.set()

        debug_dict = context.to_debug_dict()

        assert debug_dict["pump_thread_alive"] is True
        assert debug_dict["pump_ready_event_set"] is True

    def test_to_debug_dict_all_keys_present(self):
        """to_debug_dict() should include all expected keys."""
        context = ExecutionContext()
        debug_dict = context.to_debug_dict()

        expected_keys = [
            "current_path_index", "current_point_index", "target_point_index",
            "total_paths", "current_path_length",
            "spray_on", "motor_started", "generator_started", "is_resuming",
            "current_state", "paused_from_state",
            "pump_thread_alive", "pump_ready_event_set",
            "has_current_settings", "settings_keys",
            "has_glue_service", "has_robot_service", "has_pump_controller",
            "glue_type", "generator_to_glue_delay"
        ]

        for key in expected_keys:
            assert key in debug_dict, f"Missing key: {key}"


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

class TestParametrizedProgressSaving:
    """Parametrized tests for save_progress()."""

    @pytest.mark.parametrize("path_idx,point_idx", [
        (0, 0),
        (1, 5),
        (10, 20),
        (999, 9999),
    ])
    def test_save_progress_various_indices(self, path_idx, point_idx):
        """save_progress() should handle various index combinations."""
        context = ExecutionContext()

        context.save_progress(path_index=path_idx, point_index=point_idx)

        assert context.current_path_index == path_idx
        assert context.current_point_index == point_idx
