"""
Application Context Manager

This module provides a global context for the current running application,
allowing base services to access application-specific core settings.
"""

import threading
from typing import Optional
from core.application.ApplicationStorageResolver import get_application_storage_resolver
from core.base_robot_application import ApplicationType


class ApplicationContext:
    """
    Global context manager for the current running application.
    
    This class provides a thread-safe way to set and get the current
    application name, allowing base services to access core settings
    from the correct application storage location.
    """
    
    _instance: Optional['ApplicationContext'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Initialize the application context."""
        self._current_app_name: Optional[str] = None
        self._app_lock = threading.Lock()
        self._storage_resolver = get_application_storage_resolver()
    
    def set_current_application(self, app_type) -> None:
        """
        Set the current running application.
        
        Args:
            app_type: ApplicationType enum or string name of the current application
        """
        from core.base_robot_application import ApplicationType
        
        # Handle both enum and string inputs for backward compatibility
        if isinstance(app_type, ApplicationType):
            app_name = app_type.value
        else:
            app_name = app_type  # Assume it's already a string
            
        with self._app_lock:
            self._current_app_name = app_name
            print(f"ApplicationContext: Current application set to '{app_name}'")
    
    def get_current_application(self) -> Optional[str]:
        """
        Get the current running application name.
        
        Returns:
            str or None: The current application name, or None if not set
        """
        with self._app_lock:
            return self._current_app_name
    
    def get_core_settings_path(self, settings_filename: str, create_if_missing: bool = False) -> Optional[str]:
        """
        Get the path to a core settings file in the current application's storage.
        
        Core settings are settings that all applications need (camera_settings.json, robot_config.json).
        
        Args:
            settings_filename: Name of the settings file (e.g., 'camera_settings.json')
            create_if_missing: Whether to create directories if they don't exist
            
        Returns:
            str or None: Full path to the core settings file, or None if no application is set
        """
        current_app = self.get_current_application()
        if current_app is None:
            print(f"ApplicationContext: No current application set, cannot get core settings path for '{settings_filename}'")
            return None
        
        # Extract settings type from filename (remove .json extension)
        settings_type = settings_filename.replace('.json', '')
        
        settings_path = self._storage_resolver.get_settings_path(
            current_app, settings_type, create_if_missing
        )
        
        return settings_path
    
    def get_workpiece_storage_path(self, create_if_missing: bool = False) -> Optional[str]:
        """
        Get the path to the workpiece storage directory for the current application.
        
        Args:
            create_if_missing: Whether to create directories if they don't exist
            
        Returns:
            str or None: Full path to the workpiece storage directory, or None if no application is set
        """
        current_app = self.get_current_application()
        if current_app is None:
            print(f"ApplicationContext: No current application set, cannot get workpiece storage path")
            return None
        
        workpiece_path = self._storage_resolver.get_workpiece_storage_path(
            current_app, create_if_missing
        )
        
        return workpiece_path

    def get_users_storage_path(self, create_if_missing: bool = False) -> Optional[str]:
        """
        Get the path to the users storage directory for the current application.

        Args:
            create_if_missing: Whether to create directories if they don't exist
        Returns:
            str or None: Full path to the users storage directory, or None if no application is set
        """
        current_app = self.get_current_application()
        if current_app is None:
            print(f"ApplicationContext: No current application set, cannot get users storage path")
            return None

        users_path = self._storage_resolver.get_users_storage_path(
            current_app, create_if_missing
        )

        return users_path

    def get_calibration_storage_path(self, create_if_missing: bool = False) -> Optional[str]:
        """
        Get the path to the calibration storage directory for the current application.
        
        Args:
            create_if_missing: Whether to create directories if they don't exist
            
        Returns:
            str or None: Full path to the calibration storage directory, or None if no application is set
        """
        current_app = self.get_current_application()
        if current_app is None:
            print(f"ApplicationContext: No current application set, cannot get calibration storage path")
            return None
        
        calibration_path = self._storage_resolver.get_calibration_storage_path(
            current_app, create_if_missing
        )
        
        return calibration_path
    
    def is_application_set(self) -> bool:
        """
        Check if a current application has been set.
        
        Returns:
            bool: True if an application is set, False otherwise
        """
        return self.get_current_application() is not None


class ApplicationContextSingleton:
    """Singleton wrapper for ApplicationContext."""
    
    _instance: Optional[ApplicationContext] = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> ApplicationContext:
        """
        Get the singleton ApplicationContext instance.
        
        Returns:
            ApplicationContext: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ApplicationContext()
        return cls._instance


# Convenience functions
def set_current_application(app_type) -> None:
    """
    Set the current running application.
    
    Args:
        app_type: ApplicationType enum or string name of the current application
    """
    context = ApplicationContextSingleton.get_instance()
    context.set_current_application(app_type)


def get_current_application() -> Optional[str]:
    """
    Get the current running application name.
    
    Returns:
        str or None: The current application name
    """
    context = ApplicationContextSingleton.get_instance()
    return context.get_current_application()


def get_core_settings_path(settings_filename: str, create_if_missing: bool = False) -> Optional[str]:
    """
    Get the path to a core settings file in the current application's storage.
    
    Args:
        settings_filename: Name of the settings file (e.g., 'camera_settings.json')
        create_if_missing: Whether to create directories if they don't exist
        
    Returns:
        str or None: Full path to the core settings file
    """
    context = ApplicationContextSingleton.get_instance()
    return context.get_core_settings_path(settings_filename, create_if_missing)


def get_workpiece_storage_path(create_if_missing: bool = False) -> Optional[str]:
    """
    Get the path to the workpiece storage directory for the current application.
    
    Args:
        create_if_missing: Whether to create directories if they don't exist
        
    Returns:
        str or None: Full path to the workpiece storage directory
    """
    context = ApplicationContextSingleton.get_instance()
    return context.get_workpiece_storage_path(create_if_missing)

def get_users_storage_path(create_if_missing: bool = False) -> Optional[str]:
    """
    Get the path to the users storage directory for the current application.

    Args:
        create_if_missing: Whether to create directories if they don't exist
    Returns:
        str or None: Full path to the users storage directory
    """
    context = ApplicationContextSingleton.get_instance()
    return context.get_users_storage_path(create_if_missing)

def get_calibration_storage_path(create_if_missing: bool = False) -> Optional[str]:
    """
    Get the path to the calibration storage directory for the current application.
    
    Args:
        create_if_missing: Whether to create directories if they don't exist
        
    Returns:
        str or None: Full path to the calibration storage directory
    """
    context = ApplicationContextSingleton.get_instance()
    return context.get_calibration_storage_path(create_if_missing)


def is_application_context_set() -> bool:
    """
    Check if a current application has been set.
    
    Returns:
        bool: True if an application is set, False otherwise
    """
    context = ApplicationContextSingleton.get_instance()
    return context.is_application_set()


def get_application_settings_tabs() -> list:
    """
    Get the settings tabs needed by the current application.
    
    Returns:
        list: List of settings tab names needed by current application, 
              or default ["camera", "robot"] if no application is set
    """
    from core.base_robot_application import ApplicationType
    
    try:
        current_app_name = get_current_application()
        if current_app_name is None:
            return ["camera", "robot"]  # Default tabs
        
        # Create ApplicationType enum directly from the current app name
        app_type = ApplicationType(current_app_name)
        
        # Get the registered application class and its metadata
        if app_type == ApplicationType.GLUE_DISPENSING:
            from applications.glue_dispensing_application.GlueDispensingApplication import GlueSprayingApplication
            metadata = GlueSprayingApplication.get_metadata()
            return metadata.settings_tabs
        elif app_type == ApplicationType.TEST_APPLICATION:
            from applications.test_application.test_application import TestApplication
            metadata = TestApplication.get_metadata()
            return metadata.settings_tabs
        else:
            return ["camera", "robot"]  # Default tabs
            
    except Exception as e:
        print(f"Error getting application settings tabs: {e}")
        return ["camera", "robot"]  # Fallback to default tabs


def get_application_required_plugins() -> list:
    """
    Get the plugin dependencies needed by the current application.
    
    Returns:
        list: List of plugin identifiers needed by current application,
              or default plugins if no application is set
    """

    try:
        current_app_name = get_current_application()
        if current_app_name is None:
            # Default plugins for all applications
            return ["dashboard", "settings", "gallery"]
        
        # Create ApplicationType enum directly from the current app name
        app_type = ApplicationType(current_app_name)
        
        # Get the registered application class and its metadata
        if app_type == ApplicationType.GLUE_DISPENSING:
            from applications.glue_dispensing_application.GlueDispensingApplication import GlueSprayingApplication
            metadata = GlueSprayingApplication.get_metadata()
            return metadata.get_required_plugins()
        elif app_type == ApplicationType.TEST_APPLICATION:
            from applications.test_application.test_application import TestApplication
            metadata = TestApplication.get_metadata()
            return metadata.get_required_plugins()
        elif app_type == ApplicationType.PAINT_APPLICATION:
            from applications.edge_painting_application.application import EdgePaintingApplication
            metadata = EdgePaintingApplication.get_metadata()
            return metadata.get_required_plugins()
        else:
            # Default plugins for unknown applications
            return ["dashboard", "settings", "gallery"]
            
    except Exception as e:
        print(f"Error getting application required plugins: {e}")
        return ["dashboard", "settings", "gallery"]  # Fallback to default plugins


if __name__ == "__main__":
    # Test the application context
    print("=== ApplicationContext Test ===")
    
    # Test setting application
    set_current_application("glue_dispensing_application")
    print(f"Current application: {get_current_application()}")
    
    # Test getting core settings paths
    camera_path = get_core_settings_path("camera_settings.json")
    robot_path = get_core_settings_path("robot_config.json")
    
    print(f"Camera settings path: {camera_path}")
    print(f"Robot config path: {robot_path}")
    
    # Test context check
    print(f"Is context set: {is_application_context_set()}")