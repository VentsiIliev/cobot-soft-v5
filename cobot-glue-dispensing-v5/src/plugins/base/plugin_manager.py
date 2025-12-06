"""
Plugin Manager

Main orchestrator for the plugin system with automatic discovery and lifecycle management.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from .plugin_interface import IPlugin, PluginMetadata, PluginCategory
from .plugin_registry import PluginRegistry
from .plugin_loader import PluginLoader, PluginLoadError


class PluginManagerError(Exception):
    """Exception raised by plugin manager operations"""
    pass


class PluginManager:
    """
    Central plugin management system.
    
    Handles automatic plugin discovery, loading, dependency resolution,
    and lifecycle management for the entire plugin ecosystem.
    """
    
    def __init__(self, controller_service=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Core components
        self.registry = PluginRegistry()
        self.loader = PluginLoader()
        self.controller_service = controller_service
        
        # Plugin directories
        self.plugin_dirs: List[str] = []
        
        # State tracking
        self._is_initialized = False
        self._loaded_categories: List[PluginCategory] = []
        
        # Event callbacks
        self._on_plugin_loaded: Optional[Callable[[str, IPlugin], None]] = None
        self._on_plugin_failed: Optional[Callable[[str, Exception], None]] = None
        
        self.logger.info("Plugin manager initialized")
    
    def add_plugin_directory(self, directory: str) -> None:
        """
        Add a directory to search for plugins.
        
        Args:
            directory: Path to plugin directory
        """
        abs_path = os.path.abspath(directory)
        if abs_path not in self.plugin_dirs:
            self.plugin_dirs.append(abs_path)
            self.logger.info(f"Added plugin directory: {abs_path}")
    
    def set_controller_service(self, controller_service) -> None:
        """Set the controller service for plugin initialization"""
        self.controller_service = controller_service
        self.logger.info("Controller service configured for plugin manager")
    
    def discover_and_load_all(self, categories: Optional[List[PluginCategory]] = None) -> Dict[str, bool]:
        """
        Discover and load all plugins from configured directories.
        
        Args:
            categories: List of categories to load, None for all categories
            
        Returns:
            Dictionary mapping plugin names to loading success status
        """
        try:
            if not self.controller_service:
                raise PluginManagerError("Controller service not configured")
            
            self.logger.info("Starting plugin discovery and loading...")
            
            # Discover all plugins
            discovered_plugins = self.loader.discover_plugins(self.plugin_dirs)
            self.logger.info(f"Discovered {len(discovered_plugins)} plugins")
            
            # Load plugins by category in order
            load_order = categories or [PluginCategory.CORE, PluginCategory.FEATURE, PluginCategory.TOOL, PluginCategory.EXTENSION]
            results = {}
            
            for category in load_order:
                category_results = self._load_plugins_by_category(discovered_plugins, category)
                results.update(category_results)
                self._loaded_categories.append(category)
            
            self._is_initialized = True
            self.logger.info(f"Plugin loading complete. Loaded: {len([r for r in results.values() if r])} plugins")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to discover and load plugins: {e}", exc_info=True)
            raise PluginManagerError(f"Plugin loading failed: {e}")
    
    def discover_and_load_selective(self, required_plugin_names: List[str]) -> Dict[str, bool]:
        """
        Discover and load only specific plugins required by the application.

        Args:
            required_plugin_names: List of plugin names to load (e.g., ["dashboard", "settings", "gallery"])

        Returns:
            Dictionary mapping plugin names to loading success status
        """
        try:
            if not self.controller_service:
                raise PluginManagerError("Controller service not configured")

            self.logger.info(f"Starting selective plugin discovery for: {required_plugin_names}")

            # Discover all plugins
            discovered_plugins = self.loader.discover_plugins(self.plugin_dirs)
            self.logger.info(f"Discovered {len(discovered_plugins)} total plugins")

            # Filter to only required plugins (case-insensitive matching)
            required_lower = [name.lower() for name in required_plugin_names]
            filtered_plugins = [
                (path, metadata) for path, metadata in discovered_plugins
                if metadata.get('name', '').lower() in required_lower
            ]

            self.logger.info(f"Filtered to {len(filtered_plugins)} required plugins: {[m.get('name') for p, m in filtered_plugins]}")

            # Load plugins by category in order
            load_order = [PluginCategory.CORE, PluginCategory.FEATURE, PluginCategory.TOOL, PluginCategory.EXTENSION]
            results = {}

            for category in load_order:
                category_results = self._load_plugins_by_category(filtered_plugins, category)
                results.update(category_results)
                if category not in self._loaded_categories:
                    self._loaded_categories.append(category)

            self._is_initialized = True
            loaded_count = len([r for r in results.values() if r])
            self.logger.info(f"Selective plugin loading complete. Loaded: {loaded_count}/{len(required_plugin_names)} plugins")

            # Log any missing required plugins
            loaded_names = [name.lower() for name, success in results.items() if success]
            missing = [name for name in required_plugin_names if name.lower() not in loaded_names]
            if missing:
                self.logger.warning(f"Required plugins not found or failed to load: {missing}")

            return results

        except Exception as e:
            self.logger.error(f"Failed to discover and load selective plugins: {e}", exc_info=True)
            raise PluginManagerError(f"Selective plugin loading failed: {e}")

    def _load_plugins_by_category(self, discovered_plugins: List[tuple], category: PluginCategory) -> Dict[str, bool]:
        """
        Load plugins of a specific category.
        
        Args:
            discovered_plugins: List of (plugin_path, metadata) tuples
            category: Category to load
            
        Returns:
            Dictionary mapping plugin names to loading success status
        """
        results = {}
        category_plugins = []
        
        # Filter plugins by category
        for plugin_path, metadata in discovered_plugins:
            plugin_category = PluginCategory(metadata.get('category', 'feature'))
            if plugin_category == category:
                category_plugins.append((plugin_path, metadata))
        
        self.logger.info(f"Loading {len(category_plugins)} plugins in category: {category.value}")
        
        # Load each plugin in the category
        for plugin_path, metadata in category_plugins:
            plugin_name = metadata['name']
            try:
                success = self._load_single_plugin(plugin_path, metadata)
                results[plugin_name] = success
            except Exception as e:
                self.logger.error(f"Failed to load plugin '{plugin_name}': {e}")
                results[plugin_name] = False
                self.registry.mark_plugin_failed(plugin_name)
                
                # Call failure callback if set
                if self._on_plugin_failed:
                    self._on_plugin_failed(plugin_name, e)
        
        return results
    
    def _load_single_plugin(self, plugin_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Load a single plugin.
        
        Args:
            plugin_path: Path to plugin directory
            metadata: Plugin metadata
            
        Returns:
            True if loading successful, False otherwise
        """
        plugin_name = metadata['name']
        
        try:
            # Load plugin instance
            plugin = self.loader.load_plugin(plugin_path, metadata)
            
            # Store the raw JSON metadata on the plugin instance for UI purposes
            # This includes folder_id, icon_name, etc. from plugin.json
            plugin._json_metadata = metadata

            # Check if plugin can be loaded
            if not plugin.can_load():
                self.logger.warning(f"Plugin '{plugin_name}' cannot be loaded (conditions not met)")
                return False
            
            # Register in registry
            if not self.registry.register_plugin(plugin):
                self.logger.error(f"Failed to register plugin '{plugin_name}'")
                return False
            
            # Resolve dependencies
            dependency_order = self.registry.resolve_dependencies(plugin_name)
            if not dependency_order:
                self.logger.error(f"Could not resolve dependencies for plugin '{plugin_name}'")
                return False
            
            # Initialize plugin
            if not plugin.initialize(self.controller_service):
                self.logger.error(f"Failed to initialize plugin '{plugin_name}'")
                return False
            
            plugin._mark_initialized(True)
            self.registry.mark_plugin_loaded(plugin_name)
            
            # Call success callback if set
            if self._on_plugin_loaded:
                self._on_plugin_loaded(plugin_name, plugin)
            
            self.logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin '{plugin_name}': {e}", exc_info=True)
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """Get a loaded plugin by name"""
        return self.registry.get_plugin(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """Get all loaded plugins"""
        return self.registry.get_all_plugins()
    
    def get_plugins_by_category(self, category: PluginCategory) -> List[IPlugin]:
        """Get all plugins in a specific category"""
        return self.registry.get_plugins_by_category(category)
    
    def get_loaded_plugin_names(self) -> List[str]:
        """Get list of successfully loaded plugin names"""

        result =  self.registry.get_loaded_plugins()
        print(f"Loaded plugins: {result}")
        return result
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin.
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if unload successful, False otherwise
        """
        try:
            plugin = self.registry.get_plugin(plugin_name)
            if not plugin:
                self.logger.warning(f"Plugin '{plugin_name}' not found")
                return False
            
            # Cleanup plugin
            plugin.cleanup()
            plugin._mark_initialized(False)
            
            # Unload from loader
            self.loader.unload_plugin(plugin_name)
            
            # Unregister from registry
            self.registry.unregister_plugin(plugin_name)
            
            self.logger.info(f"Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin '{plugin_name}': {e}")
            return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a specific plugin.
        
        Args:
            plugin_name: Name of plugin to reload
            
        Returns:
            True if reload successful, False otherwise
        """
        try:
            # Find plugin in discovered plugins
            discovered_plugins = self.loader.discover_plugins(self.plugin_dirs)
            
            for plugin_path, metadata in discovered_plugins:
                if metadata['name'] == plugin_name:
                    # Unload first
                    self.unload_plugin(plugin_name)
                    
                    # Reload
                    return self._load_single_plugin(plugin_path, metadata)
            
            self.logger.error(f"Plugin '{plugin_name}' not found for reload")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to reload plugin '{plugin_name}': {e}")
            return False
    
    def cleanup_all(self) -> None:
        """Cleanup all loaded plugins"""
        try:
            plugin_names = self.registry.get_loaded_plugins().copy()
            for plugin_name in plugin_names:
                self.unload_plugin(plugin_name)
            
            self._is_initialized = False
            self._loaded_categories.clear()
            self.logger.info("All plugins cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during plugin cleanup: {e}")
    
    def set_event_callbacks(self, 
                           on_loaded: Optional[Callable[[str, IPlugin], None]] = None,
                           on_failed: Optional[Callable[[str, Exception], None]] = None) -> None:
        """
        Set event callbacks for plugin loading events.
        
        Args:
            on_loaded: Callback for successful plugin loading
            on_failed: Callback for plugin loading failures
        """
        self._on_plugin_loaded = on_loaded
        self._on_plugin_failed = on_failed
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive plugin system status.
        
        Returns:
            Dictionary with system status information
        """
        registry_stats = self.registry.get_registry_stats()
        
        return {
            "initialized": self._is_initialized,
            "plugin_directories": self.plugin_dirs,
            "loaded_categories": [cat.value for cat in self._loaded_categories],
            "registry_stats": registry_stats,
            "controller_service_configured": self.controller_service is not None
        }