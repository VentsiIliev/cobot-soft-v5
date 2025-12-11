"""
Unit tests for PumpController.
Tests pump startup/shutdown with segment and global settings.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from applications.glue_dispensing_application.glue_process.PumpController import PumpController
from applications.glue_dispensing_application.settings.enums.GlueSettingKey import GlueSettingKey
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from modules.utils.custom_logging import LoggerContext


# ============================================================================
# TEST INITIALIZATION
# ============================================================================

class TestPumpControllerInitialization:
    """Test PumpController initialization."""

    def test_initialization_with_segment_settings_enabled(self):
        """PumpController should initialize with segment settings enabled."""
        logger_context = LoggerContext(enabled=False, logger=None)
        glue_settings = GlueSettings()

        controller = PumpController(
            use_segment_settings=True,
            logger_context=logger_context,
            glue_settings=glue_settings
        )

        assert controller.use_segment_settings is True
        assert controller.logger_context == logger_context
        assert controller.glue_settings == glue_settings

    def test_initialization_with_segment_settings_disabled(self):
        """PumpController should initialize with global settings."""
        logger_context = LoggerContext(enabled=False, logger=None)
        glue_settings = GlueSettings()

        controller = PumpController(
            use_segment_settings=False,
            logger_context=logger_context,
            glue_settings=glue_settings
        )

        assert controller.use_segment_settings is False
        assert controller.logger_context == logger_context
        assert controller.glue_settings == glue_settings

    def test_initialization_without_logger(self):
        """PumpController should accept None logger_context."""
        controller = PumpController(
            use_segment_settings=True,
            logger_context=None,
            glue_settings=None
        )

        assert controller.use_segment_settings is True
        assert controller.logger_context is None
        assert controller.glue_settings is None


# ============================================================================
# TEST PUMP ON - SEGMENT SETTINGS
# ============================================================================

class TestPumpOnSegmentSettings:
    """Test pump_on() with segment settings."""

    def test_pump_on_with_segment_settings(self, pump_controller):
        """pump_on() should use segment settings when use_segment_settings=True."""
        mock_service = MagicMock()
        mock_service.motorOn = MagicMock(return_value=True)
        mock_robot = MagicMock()

        settings = {
            GlueSettingKey.MOTOR_SPEED.value: 15000,
            GlueSettingKey.FORWARD_RAMP_STEPS.value: 3,
            GlueSettingKey.INITIAL_RAMP_SPEED.value: 7500,
            GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: 2.0,
        }

        result = pump_controller.pump_on(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        # Verify motorOn was called with segment settings
        mock_service.motorOn.assert_called_once()
        call_kwargs = mock_service.motorOn.call_args[1]
        assert call_kwargs['motorAddress'] == 42
        assert call_kwargs['speed'] == 15000.0
        assert call_kwargs['ramp_steps'] == 3
        assert call_kwargs['initial_ramp_speed'] == 7500.0
        assert call_kwargs['initial_ramp_speed_duration'] == 2.0
        assert result is True

    def test_pump_on_segment_settings_with_missing_keys(self, pump_controller):
        """pump_on() should use default 0 for missing segment settings."""
        mock_service = MagicMock()
        mock_service.motorOn = MagicMock(return_value=True)
        mock_robot = MagicMock()

        settings = {
            GlueSettingKey.MOTOR_SPEED.value: 10000,
            # Missing other keys
        }

        result = pump_controller.pump_on(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        # Verify defaults were used
        call_kwargs = mock_service.motorOn.call_args[1]
        assert call_kwargs['speed'] == 10000.0
        assert call_kwargs['ramp_steps'] == 0  # Default from .get()
        assert call_kwargs['initial_ramp_speed'] == 0.0
        assert call_kwargs['initial_ramp_speed_duration'] == 0.0

    def test_pump_on_returns_service_result(self, pump_controller):
        """pump_on() should return the result from motorOn."""
        mock_service = MagicMock()
        mock_service.motorOn = MagicMock(return_value=True)
        mock_robot = MagicMock()

        settings = {GlueSettingKey.MOTOR_SPEED.value: 10000}

        result = pump_controller.pump_on(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        assert result is True

        # Test with False return
        mock_service.motorOn.return_value = False
        result = pump_controller.pump_on(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        assert result is False


# ============================================================================
# TEST PUMP ON - GLOBAL SETTINGS
# ============================================================================

class TestPumpOnGlobalSettings:
    """Test pump_on() with global settings."""

    def test_pump_on_with_global_settings(self, pump_controller_global):
        """pump_on() should use global settings when use_segment_settings=False."""
        mock_service = MagicMock()
        mock_service.motorOn = MagicMock(return_value=True)
        mock_robot = MagicMock()

        # Even if segment settings are provided, they should be ignored
        segment_settings = {
            GlueSettingKey.MOTOR_SPEED.value: 99999,  # Should be ignored
        }

        result = pump_controller_global.pump_on(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=segment_settings  # Ignored
        )

        # Verify motorOn was called with global settings
        mock_service.motorOn.assert_called_once()
        call_kwargs = mock_service.motorOn.call_args[1]
        assert call_kwargs['motorAddress'] == 42
        # Should use global settings from glue_settings, not segment settings
        assert call_kwargs['speed'] != 99999  # Not the segment value

    def test_pump_on_global_with_no_glue_settings(self, logger_context):
        """pump_on() should use hardcoded defaults when glue_settings is None."""
        controller = PumpController(
            use_segment_settings=False,
            logger_context=logger_context,  # Use disabled logger
            glue_settings=None  # No global settings
        )

        mock_service = MagicMock()
        mock_service.motorOn = MagicMock(return_value=True)
        mock_robot = MagicMock()

        result = controller.pump_on(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=None
        )

        # Verify hardcoded defaults were used
        call_kwargs = mock_service.motorOn.call_args[1]
        assert call_kwargs['speed'] == 10000  # Hardcoded default
        assert call_kwargs['ramp_steps'] == 1
        assert call_kwargs['initial_ramp_speed'] == 5000
        assert call_kwargs['initial_ramp_speed_duration'] == 1


# ============================================================================
# TEST PUMP OFF - SEGMENT SETTINGS
# ============================================================================

class TestPumpOffSegmentSettings:
    """Test pump_off() with segment settings."""

    def test_pump_off_with_segment_settings(self, pump_controller):
        """pump_off() should use segment settings when use_segment_settings=True."""
        mock_service = MagicMock()
        mock_service.motorOff = MagicMock(return_value=None)
        mock_robot = MagicMock()

        settings = {
            GlueSettingKey.SPEED_REVERSE.value: 2000,
            GlueSettingKey.REVERSE_DURATION.value: 1.5,
            GlueSettingKey.REVERSE_RAMP_STEPS.value: 2,
        }

        pump_controller.pump_off(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        # Verify motorOff was called with segment settings
        mock_service.motorOff.assert_called_once()
        call_kwargs = mock_service.motorOff.call_args[1]
        assert call_kwargs['motorAddress'] == 42
        assert call_kwargs['speedReverse'] == 2000.0
        assert call_kwargs['reverse_time'] == 1.5
        assert call_kwargs['ramp_steps'] == 2

    def test_pump_off_segment_with_missing_keys(self, pump_controller):
        """pump_off() should use default 0 for missing segment settings."""
        mock_service = MagicMock()
        mock_service.motorOff = MagicMock(return_value=None)
        mock_robot = MagicMock()

        settings = {
            GlueSettingKey.SPEED_REVERSE.value: 1500,
            # Missing other keys
        }

        pump_controller.pump_off(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        # Verify defaults were used
        call_kwargs = mock_service.motorOff.call_args[1]
        assert call_kwargs['speedReverse'] == 1500.0
        assert call_kwargs['reverse_time'] == 0.0  # Default
        assert call_kwargs['ramp_steps'] == 0  # Default


# ============================================================================
# TEST PUMP OFF - GLOBAL SETTINGS
# ============================================================================

class TestPumpOffGlobalSettings:
    """Test pump_off() with global settings."""

    def test_pump_off_with_global_settings(self, pump_controller_global):
        """pump_off() should use global settings when use_segment_settings=False."""
        mock_service = MagicMock()
        mock_service.motorOff = MagicMock(return_value=None)
        mock_robot = MagicMock()

        # Segment settings should be ignored
        segment_settings = {
            GlueSettingKey.SPEED_REVERSE.value: 99999,  # Ignored
        }

        pump_controller_global.pump_off(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=segment_settings  # Ignored
        )

        # Verify motorOff was called with global settings
        mock_service.motorOff.assert_called_once()
        call_kwargs = mock_service.motorOff.call_args[1]
        assert call_kwargs['motorAddress'] == 42
        # Should NOT use segment setting
        assert call_kwargs['speedReverse'] != 99999

    def test_pump_off_global_with_no_glue_settings(self, logger_context):
        """pump_off() should use hardcoded defaults when glue_settings is None."""
        controller = PumpController(
            use_segment_settings=False,
            logger_context=logger_context,  # Use disabled logger
            glue_settings=None
        )

        mock_service = MagicMock()
        mock_service.motorOff = MagicMock(return_value=None)
        mock_robot = MagicMock()

        controller.pump_off(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=None
        )

        # Verify hardcoded defaults
        call_kwargs = mock_service.motorOff.call_args[1]
        assert call_kwargs['speedReverse'] == 1000  # Hardcoded default
        assert call_kwargs['reverse_time'] == 1
        assert call_kwargs['ramp_steps'] == 1


# ============================================================================
# TEST EXCEPTION HANDLING
# ============================================================================

class TestPumpControllerExceptionHandling:
    """Test exception handling in pump operations."""

    def test_pump_on_exception_returns_false(self, pump_controller):
        """pump_on() should return False and log error on exception."""
        mock_service = MagicMock()
        mock_service.motorOn.side_effect = Exception("Motor failure")
        mock_robot = MagicMock()

        settings = {GlueSettingKey.MOTOR_SPEED.value: 10000}

        result = pump_controller.pump_on(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        assert result is False

    def test_pump_off_exception_handled(self, pump_controller):
        """pump_off() should handle exceptions gracefully."""
        mock_service = MagicMock()
        mock_service.motorOff.side_effect = Exception("Motor failure")
        mock_robot = MagicMock()

        settings = {GlueSettingKey.SPEED_REVERSE.value: 1000}

        # Should not raise exception
        pump_controller.pump_off(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================

class TestPumpControllerParametrized:
    """Parametrized tests for different configurations."""

    @pytest.mark.parametrize("use_segment_settings", [True, False])
    def test_pump_controller_both_modes(self, use_segment_settings):
        """Test PumpController initialization with both settings modes."""
        controller = PumpController(
            use_segment_settings=use_segment_settings,
            logger_context=None,
            glue_settings=None
        )

        assert controller.use_segment_settings == use_segment_settings

    @pytest.mark.parametrize("motor_speed,expected", [
        (5000, 5000.0),
        (10000, 10000.0),
        (20000, 20000.0),
        (0, 0.0),
    ])
    def test_pump_on_various_speeds(self, pump_controller, motor_speed, expected):
        """Test pump_on() with various motor speeds."""
        mock_service = MagicMock()
        mock_service.motorOn = MagicMock(return_value=True)
        mock_robot = MagicMock()

        settings = {GlueSettingKey.MOTOR_SPEED.value: motor_speed}

        pump_controller.pump_on(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        call_kwargs = mock_service.motorOn.call_args[1]
        assert call_kwargs['speed'] == expected

    @pytest.mark.parametrize("reverse_speed,expected", [
        (500, 500.0),
        (1000, 1000.0),
        (2000, 2000.0),
    ])
    def test_pump_off_various_reverse_speeds(self, pump_controller, reverse_speed, expected):
        """Test pump_off() with various reverse speeds."""
        mock_service = MagicMock()
        mock_service.motorOff = MagicMock(return_value=None)
        mock_robot = MagicMock()

        settings = {GlueSettingKey.SPEED_REVERSE.value: reverse_speed}

        pump_controller.pump_off(
            service=mock_service,
            robot_service=mock_robot,
            glue_type=42,
            settings=settings
        )

        call_kwargs = mock_service.motorOff.call_args[1]
        assert call_kwargs['speedReverse'] == expected
