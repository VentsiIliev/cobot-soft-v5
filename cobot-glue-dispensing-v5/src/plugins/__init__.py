"""
Plugin System for Cobot Glue Dispensing Application

This package provides a flexible plugin architecture for modular application development.
"""

__version__ = "1.0.0"
__author__ = "PL Team"

from .base.plugin_manager import PluginManager
from .base.plugin_interface import IPlugin, PluginMetadata

__all__ = [
    "PluginManager",
    "IPlugin", 
    "PluginMetadata"
]