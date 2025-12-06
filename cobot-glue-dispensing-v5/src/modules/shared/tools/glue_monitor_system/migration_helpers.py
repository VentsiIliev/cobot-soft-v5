"""
Migration helpers for transitioning from singleton-based to dependency injection.
Provides backward compatibility during the transition period.
"""
import warnings
from typing import Optional

from modules.shared.tools.glue_monitor_system.interfaces import (
    IWeightDataFetcher, IGlueCellsManager
)
from modules.shared.tools.glue_monitor_system.service_factory import get_service_factory


class SingletonCompatibilityWrapper:
    """
    Compatibility wrapper that provides singleton-like interface
    while using the new dependency injection system underneath.
    """
    
    _weight_data_fetcher: Optional[IWeightDataFetcher] = None
    _cells_manager: Optional[IGlueCellsManager] = None
    
    @classmethod
    def get_weight_data_fetcher(cls) -> IWeightDataFetcher:
        """
        Get weight data fetcher instance with singleton-like behavior.
        
        This is provided for backward compatibility during migration.
        New code should use the service factory directly.
        """
        warnings.warn(
            "Using SingletonCompatibilityWrapper is deprecated. "
            "Use service_factory.create_weight_data_fetcher() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if cls._weight_data_fetcher is None:
            cls._weight_data_fetcher = get_service_factory().create_weight_data_fetcher()
        return cls._weight_data_fetcher
    
    @classmethod
    def get_cells_manager(cls) -> IGlueCellsManager:
        """
        Get cells manager instance with singleton-like behavior.
        
        This is provided for backward compatibility during migration.
        New code should use the service factory directly.
        """
        warnings.warn(
            "Using SingletonCompatibilityWrapper is deprecated. "
            "Use service_factory.create_cells_manager() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if cls._cells_manager is None:
            cls._cells_manager = get_service_factory().create_cells_manager()
        return cls._cells_manager
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset singleton instances.
        Useful for testing and during migration.
        """
        cls._weight_data_fetcher = None
        cls._cells_manager = None


def create_backward_compatible_data_fetcher():
    """
    Create a data fetcher that's compatible with the old singleton interface.
    
    This function provides backward compatibility for code that expects
    the old GlueDataFetcher singleton behavior.
    """
    return SingletonCompatibilityWrapper.get_weight_data_fetcher()


def create_backward_compatible_cells_manager():
    """
    Create a cells manager that's compatible with the old singleton interface.
    
    This function provides backward compatibility for code that expects
    the old GlueCellsManagerSingleton behavior.
    """
    return SingletonCompatibilityWrapper.get_cells_manager()


# Adapter classes for the old interfaces
class GlueDataFetcherAdapter:
    """
    Adapter that makes the new IWeightDataFetcher compatible with old code
    that expects the GlueDataFetcher singleton interface.
    """
    
    def __init__(self):
        self._fetcher = create_backward_compatible_data_fetcher()
        
        # Expose individual weight properties for backward compatibility
        self._weight1 = 0.0
        self._weight2 = 0.0
        self._weight3 = 0.0
        
        # Start fetching immediately like the old singleton
        self._fetcher.start()
    
    @property
    def weight1(self) -> float:
        """Get weight for cell 1."""
        weight = self._fetcher.get_weight(1)
        return weight if weight is not None else 0.0
    
    @property
    def weight2(self) -> float:
        """Get weight for cell 2."""
        weight = self._fetcher.get_weight(2)
        return weight if weight is not None else 0.0
    
    @property
    def weight3(self) -> float:
        """Get weight for cell 3."""
        weight = self._fetcher.get_weight(3)
        return weight if weight is not None else 0.0
    
    def start(self) -> None:
        """Start the fetcher."""
        self._fetcher.start()
    
    def stop(self) -> None:
        """Stop the fetcher."""
        self._fetcher.stop()
    
    def reload_config(self) -> None:
        """Reload configuration."""
        self._fetcher.reload_config()


class GlueCellsManagerSingletonAdapter:
    """
    Adapter that provides the old GlueCellsManagerSingleton interface
    using the new dependency injection system.
    """
    
    _instance: Optional['GlueCellsManagerSingletonAdapter'] = None
    
    @classmethod
    def get_instance(cls) -> 'GlueCellsManagerSingletonAdapter':
        """Get singleton instance (adapter pattern)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self._manager = create_backward_compatible_cells_manager()
    
    def getCellById(self, cell_id: int):
        """Get cell by ID (old interface)."""
        return self._manager.get_cell_by_id(cell_id)
    
    def updateGlueTypeById(self, cell_id: int, glue_type) -> bool:
        """Update glue type by ID (old interface)."""
        return self._manager.update_glue_type_by_id(cell_id, glue_type)
    
    def pollGlueDataById(self, cell_id: int):
        """Poll glue data by ID (old interface)."""
        return self._manager.poll_glue_data_by_id(cell_id)
    
    @property
    def cells(self):
        """Get all cells (old interface)."""
        return self._manager.get_all_cells()