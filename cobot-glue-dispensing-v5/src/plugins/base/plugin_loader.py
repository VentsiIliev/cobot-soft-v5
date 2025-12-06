"""
Plugin Loader

Dynamic loading and instantiation of plugins from directories and files.
"""

import os
import sys
import json
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .plugin_interface import IPlugin, PluginMetadata


class PluginLoadError(Exception):
    """Exception raised when plugin loading fails"""
    pass


class PluginLoader:
    """
    Dynamic plugin loader with automatic discovery.
    
    Handles discovering, loading, and instantiating plugins from
    filesystem locations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._loaded_modules: Dict[str, Any] = {}
    
    def discover_plugins(self, plugin_dirs: List[str]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Discover all plugins in the specified directories.
        
        Args:
            plugin_dirs: List of directory paths to search for plugins
            
        Returns:
            List of tuples containing (plugin_path, plugin_metadata)
        """
        discovered = []
        
        for plugin_dir in plugin_dirs:
            try:
                discovered.extend(self._scan_directory(plugin_dir))
            except Exception as e:
                self.logger.error(f"Error scanning plugin directory '{plugin_dir}': {e}")
        
        self.logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
    
    def _scan_directory(self, directory: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Scan a directory for plugins.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            List of discovered plugins with metadata
        """
        plugins = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            self.logger.warning(f"Plugin directory does not exist: {directory}")
            return plugins
        
        # Look for plugin.json files to identify plugins
        for plugin_json in directory_path.rglob("plugin.json"):
            try:
                plugin_metadata = self._load_plugin_metadata(plugin_json)
                plugin_path = plugin_json.parent
                plugins.append((str(plugin_path), plugin_metadata))
                self.logger.debug(f"Found plugin: {plugin_metadata.get('name', 'Unknown')} at {plugin_path}")
            except Exception as e:
                self.logger.error(f"Failed to load plugin metadata from {plugin_json}: {e}")
        
        return plugins
    
    def _load_plugin_metadata(self, metadata_file: Path) -> Dict[str, Any]:
        """
        Load plugin metadata from plugin.json file.
        
        Args:
            metadata_file: Path to plugin.json file
            
        Returns:
            Dictionary containing plugin metadata
        """
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Validate required fields
            required_fields = ['name', 'version', 'entry_point']
            for field in required_fields:
                if field not in metadata:
                    raise PluginLoadError(f"Missing required field '{field}' in plugin.json")
            
            return metadata
        except json.JSONDecodeError as e:
            raise PluginLoadError(f"Invalid JSON in plugin metadata: {e}")
        except Exception as e:
            raise PluginLoadError(f"Failed to read plugin metadata: {e}")
    
    def load_plugin(self, plugin_path: str, metadata: Dict[str, Any]) -> IPlugin:
        """
        Load and instantiate a plugin from its path and metadata.
        
        Args:
            plugin_path: Path to plugin directory
            metadata: Plugin metadata from plugin.json
            
        Returns:
            Instantiated plugin instance
        """
        try:
            plugin_name = metadata['name']
            entry_point = metadata['entry_point']
            
            self.logger.info(f"Loading plugin '{plugin_name}' from {plugin_path}")
            
            # Load the plugin module
            plugin_module = self._load_plugin_module(plugin_path, plugin_name, entry_point)
            
            # Get the plugin class
            plugin_class = self._get_plugin_class(plugin_module, entry_point)
            
            # Instantiate the plugin
            plugin_instance = plugin_class()
            
            # Validate plugin implements IPlugin
            if not isinstance(plugin_instance, IPlugin):
                raise PluginLoadError(f"Plugin class does not implement IPlugin interface")
            
            self.logger.info(f"Successfully loaded plugin: {plugin_name}")
            return plugin_instance
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin from {plugin_path}: {e}")
            raise PluginLoadError(f"Plugin loading failed: {e}")
    
    def _load_plugin_module(self, plugin_path: str, plugin_name: str, entry_point: str) -> Any:
        """
        Dynamically load a plugin module.
        
        Args:
            plugin_path: Path to plugin directory
            plugin_name: Plugin name for module identification
            entry_point: Entry point specification (e.g., 'plugin.SettingsPlugin')
            
        Returns:
            Loaded module object
        """
        try:
            # Parse entry point to get module and class
            if '.' in entry_point:
                module_name, class_name = entry_point.rsplit('.', 1)
            else:
                raise PluginLoadError(f"Invalid entry point format: {entry_point}")
            
            # Construct full module path
            module_file = os.path.join(plugin_path, f"{module_name}.py")
            
            if not os.path.exists(module_file):
                raise PluginLoadError(f"Plugin module not found: {module_file}")
            
            # Create unique module name to avoid conflicts
            full_module_name = f"plugin_{plugin_name}_{module_name}".replace('-', '_')
            
            # Load module using importlib
            spec = importlib.util.spec_from_file_location(full_module_name, module_file)
            if spec is None or spec.loader is None:
                raise PluginLoadError(f"Could not create module spec for {module_file}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Add plugin path to sys.path temporarily for imports
            plugin_path_abs = os.path.abspath(plugin_path)
            if plugin_path_abs not in sys.path:
                sys.path.insert(0, plugin_path_abs)
                path_added = True
            else:
                path_added = False
            
            try:
                spec.loader.exec_module(module)
                self._loaded_modules[full_module_name] = module
                return module
            finally:
                # Remove path if we added it
                if path_added and plugin_path_abs in sys.path:
                    sys.path.remove(plugin_path_abs)
            
        except Exception as e:
            raise PluginLoadError(f"Failed to load module for plugin '{plugin_name}': {e}")
    
    def _get_plugin_class(self, module: Any, entry_point: str) -> type:
        """
        Extract plugin class from loaded module.
        
        Args:
            module: Loaded plugin module
            entry_point: Entry point specification
            
        Returns:
            Plugin class type
        """
        try:
            if '.' in entry_point:
                _, class_name = entry_point.rsplit('.', 1)
            else:
                class_name = entry_point
            
            if not hasattr(module, class_name):
                raise PluginLoadError(f"Plugin class '{class_name}' not found in module")
            
            plugin_class = getattr(module, class_name)
            
            if not isinstance(plugin_class, type):
                raise PluginLoadError(f"'{class_name}' is not a class")
            
            return plugin_class
            
        except Exception as e:
            raise PluginLoadError(f"Failed to get plugin class: {e}")
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin and clean up its module.
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if unload successful, False otherwise
        """
        try:
            # Find and remove loaded modules for this plugin
            modules_to_remove = [
                name for name in self._loaded_modules.keys()
                if name.startswith(f"plugin_{plugin_name}_")
            ]
            
            for module_name in modules_to_remove:
                # Remove from our tracking
                del self._loaded_modules[module_name]
                
                # Remove from sys.modules if present
                if module_name in sys.modules:
                    del sys.modules[module_name]
            
            self.logger.info(f"Unloaded plugin modules for: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin '{plugin_name}': {e}")
            return False
    
    def get_loaded_modules(self) -> Dict[str, Any]:
        """Get dictionary of loaded plugin modules"""
        return self._loaded_modules.copy()