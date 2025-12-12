"""
Camera settings tab module.

Provides camera configuration UI with preview functionality.
"""

from .CameraSettingsUI import CameraSettingsUI

# Legacy import - keep for backward compatibility
try:
    from .CameraSettingsTabLayout import CameraSettingsTabLayout
    __all__ = ['CameraSettingsUI', 'CameraSettingsTabLayout']
except ImportError:
    # If legacy file doesn't exist, only export new UI
    __all__ = ['CameraSettingsUI']