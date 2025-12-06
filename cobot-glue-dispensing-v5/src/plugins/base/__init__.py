"""
Plugin Base Infrastructure

Core plugin system components including interfaces, managers, and utilities.
"""

from .plugin_interface import IPlugin, PluginMetadata, PluginCategory, PluginPermission
from .plugin_manager import PluginManager
from .plugin_registry import PluginRegistry
from .plugin_loader import PluginLoader

__all__ = [
    "IPlugin",
    "PluginMetadata", 
    "PluginCategory",
    "PluginPermission",
    "PluginManager",
    "PluginRegistry",
    "PluginLoader"
]