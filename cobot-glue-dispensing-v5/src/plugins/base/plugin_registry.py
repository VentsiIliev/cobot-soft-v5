"""
Plugin Registry

Central registry for managing plugin instances and metadata.
"""

import logging
from typing import Dict, List, Optional, Set
from collections import defaultdict

from .plugin_interface import IPlugin, PluginMetadata, PluginCategory


class PluginRegistry:
    """
    Central registry for plugin management.
    
    Maintains a registry of all discovered and loaded plugins,
    handles dependency resolution, and provides plugin lookup.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Plugin storage
        self._plugins: Dict[str, IPlugin] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
        
        # Organization
        self._by_category: Dict[PluginCategory, List[str]] = defaultdict(list)
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # State tracking
        self._loaded_plugins: Set[str] = set()
        self._failed_plugins: Set[str] = set()
    
    def register_plugin(self, plugin: IPlugin) -> bool:
        """
        Register a plugin instance in the registry.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            metadata = plugin.metadata
            print(f"Registerig plugin: {metadata.name} v{metadata.version}")
            plugin_name = metadata.name
            
            # Check for conflicts
            if plugin_name in self._plugins:
                self.logger.warning(f"Plugin '{plugin_name}' already registered, replacing...")
            
            # Register plugin
            self._plugins[plugin_name] = plugin
            self._metadata[plugin_name] = metadata
            
            # Organize by category
            self._by_category[metadata.category].append(plugin_name)
            
            # Track dependencies
            for dep in metadata.dependencies:
                self._dependencies[plugin_name].add(dep)
            
            self.logger.info(f"Registered plugin: {plugin_name} v{metadata.version}")
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.logger.error(f"Failed to register plugin: {e}", exc_info=True)
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin from the registry.
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if plugin_name not in self._plugins:
                self.logger.warning(f"Plugin '{plugin_name}' not found in registry")
                return False
            
            # Get metadata before removal
            metadata = self._metadata[plugin_name]
            
            # Remove from all tracking structures
            del self._plugins[plugin_name]
            del self._metadata[plugin_name]
            
            # Remove from category tracking
            if plugin_name in self._by_category[metadata.category]:
                self._by_category[metadata.category].remove(plugin_name)
            
            # Remove from state tracking
            self._loaded_plugins.discard(plugin_name)
            self._failed_plugins.discard(plugin_name)
            
            # Clear dependencies
            del self._dependencies[plugin_name]
            
            self.logger.info(f"Unregistered plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister plugin '{plugin_name}': {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """Get plugin instance by name"""
        return self._plugins.get(plugin_name)
    
    def get_metadata(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name"""
        return self._metadata.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """Get all registered plugins"""
        return self._plugins.copy()
    
    def get_plugins_by_category(self, category: PluginCategory) -> List[IPlugin]:
        """Get all plugins in a specific category"""
        plugin_names = self._by_category.get(category, [])
        return [self._plugins[name] for name in plugin_names if name in self._plugins]
    
    def get_plugin_names(self) -> List[str]:
        """Get list of all registered plugin names"""
        return list(self._plugins.keys())
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded"""
        return plugin_name in self._loaded_plugins
    
    def mark_plugin_loaded(self, plugin_name: str) -> None:
        """Mark a plugin as loaded"""
        self._loaded_plugins.add(plugin_name)
        self._failed_plugins.discard(plugin_name)
    
    def mark_plugin_failed(self, plugin_name: str) -> None:
        """Mark a plugin as failed to load"""
        self._failed_plugins.add(plugin_name)
        self._loaded_plugins.discard(plugin_name)
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of successfully loaded plugin names"""
        result = list(self._loaded_plugins)
        print(f"[PluginRegistry] get_loaded_plugins: {result}")
        return result

    def get_failed_plugins(self) -> List[str]:
        """Get list of plugins that failed to load"""
        return list(self._failed_plugins)
    
    def resolve_dependencies(self, plugin_name: str) -> List[str]:
        """
        Resolve plugin dependencies in loading order.
        
        Args:
            plugin_name: Name of plugin to resolve dependencies for
            
        Returns:
            List of plugin names in dependency order
        """
        resolved = []
        visited = set()
        visiting = set()
        
        def visit(name: str) -> bool:
            if name in visiting:
                self.logger.error(f"Circular dependency detected involving '{name}'")
                return False
            
            if name in visited:
                return True
            
            visiting.add(name)
            
            # Visit dependencies first
            for dep in self._dependencies.get(name, []):
                if dep not in self._plugins:
                    self.logger.error(f"Dependency '{dep}' not found for plugin '{name}'")
                    return False
                
                if not visit(dep):
                    return False
            
            visiting.remove(name)
            visited.add(name)
            resolved.append(name)
            return True
        
        if visit(plugin_name):
            return resolved
        else:
            return []
    
    def get_registry_stats(self) -> Dict[str, any]:
        """Get registry statistics"""
        return {
            "total_plugins": len(self._plugins),
            "loaded_plugins": len(self._loaded_plugins),
            "failed_plugins": len(self._failed_plugins),
            "by_category": {
                category.value: len(plugins) 
                for category, plugins in self._by_category.items()
            }
        }