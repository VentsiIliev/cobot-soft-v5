"""
Glue Types Service

Business logic for managing glue types.
Provides CRUD operations with validation and cascade operations.
"""

import logging
from typing import List, Optional, Tuple
from applications.glue_dispensing_application.model.glue.glue import Glue
from applications.glue_dispensing_application.repositories.glue_types_repository import GlueTypesRepository


class GlueTypesService:
    """
    Service for managing glue types business logic.

    Provides:
    - CRUD operations
    - Validation (duplicate names, etc.)
    - Cascade operations for GlueCell integration
    """

    def __init__(self, repository: GlueTypesRepository):
        """
        Initialize service with repository.

        Args:
            repository: GlueTypesRepository instance
        """
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)
        self._glue_types: List[Glue] = []
        self._load_glue_types()

    def _load_glue_types(self) -> None:
        """Load glue types from repository."""
        self._glue_types = self.repository.load()

    def _save_glue_types(self) -> bool:
        """Save glue types to repository."""
        return self.repository.save(self._glue_types)

    def get_all(self) -> List[Glue]:
        """
        Get all glue types.

        Returns:
            List of all Glue instances
        """
        return self._glue_types.copy()

    def get_by_id(self, glue_id: str) -> Optional[Glue]:
        """
        Get glue type by ID.

        Args:
            glue_id: Unique glue ID

        Returns:
            Glue instance or None if not found
        """
        for glue in self._glue_types:
            if glue.id == glue_id:
                return glue
        return None

    def get_by_name(self, name: str) -> Optional[Glue]:
        """
        Get glue type by name (case-insensitive).

        Args:
            name: Glue type name

        Returns:
            Glue instance or None if not found
        """
        name_lower = name.strip().lower()
        for glue in self._glue_types:
            if glue.name.lower() == name_lower:
                return glue
        return None

    def exists(self, name: str, exclude_id: str = None) -> bool:
        """
        Check if glue type with name exists.

        Args:
            name: Glue type name to check
            exclude_id: ID to exclude from check (for updates)

        Returns:
            True if exists, False otherwise
        """
        name_lower = name.strip().lower()
        for glue in self._glue_types:
            if glue.name.lower() == name_lower:
                if exclude_id is None or glue.id != exclude_id:
                    return True
        return False

    def add(self, name: str, description: str = "") -> Tuple[bool, str, Optional[Glue]]:
        """
        Add new glue type.

        Args:
            name: Glue type name
            description: Optional description

        Returns:
            Tuple of (success, message, glue_instance)
        """
        # Validate name
        name = name.strip()
        if not name:
            return False, "Glue type name cannot be empty", None

        # Check for duplicates (case-insensitive)
        if self.exists(name):
            return False, f"Glue type '{name}' already exists", None

        # Create new glue type
        new_glue = Glue(name=name, description=description)
        self._glue_types.append(new_glue)

        # Save to file
        if not self._save_glue_types():
            # Rollback on failure
            self._glue_types.remove(new_glue)
            return False, "Failed to save glue type", None

        self.logger.info(f"Added glue type: {new_glue}")
        return True, f"Glue type '{name}' added successfully", new_glue

    def update(self, glue_id: str, name: str, description: str = "") -> Tuple[bool, str]:
        """
        Update existing glue type.

        Args:
            glue_id: ID of glue type to update
            name: New name
            description: New description

        Returns:
            Tuple of (success, message)
        """
        # Find glue type
        glue = self.get_by_id(glue_id)
        if not glue:
            return False, f"Glue type with ID '{glue_id}' not found"

        # Validate new name
        name = name.strip()
        if not name:
            return False, "Glue type name cannot be empty"

        # Check for duplicate name (excluding current glue)
        if self.exists(name, exclude_id=glue_id):
            return False, f"Glue type '{name}' already exists"

        # Store old values for rollback
        old_name = glue.name
        old_description = glue.description

        # Update glue type
        glue.name = name
        glue.description = description.strip()

        # Save to file
        if not self._save_glue_types():
            # Rollback on failure
            glue.name = old_name
            glue.description = old_description
            return False, "Failed to save glue type"

        self.logger.info(f"Updated glue type: {glue}")

        # Trigger cascade update for GlueCells
        if old_name != name:
            self._cascade_update_glue_cells(old_name, name)

        return True, f"Glue type updated to '{name}'"

    def delete(self, glue_id: str, force: bool = False) -> Tuple[bool, str]:
        """
        Delete glue type.

        Args:
            glue_id: ID of glue type to delete
            force: If True, delete even if in use (clears references)

        Returns:
            Tuple of (success, message)
        """
        # Find glue type
        glue = self.get_by_id(glue_id)
        if not glue:
            return False, f"Glue type with ID '{glue_id}' not found"

        # Check if glue type is in use
        if not force and self._is_glue_type_in_use(glue.name):
            return False, f"Cannot delete glue type '{glue.name}' - it is currently in use by glue cells"

        # Remove from list
        self._glue_types.remove(glue)

        # Save to file
        if not self._save_glue_types():
            # Rollback on failure
            self._glue_types.append(glue)
            return False, "Failed to save changes"

        self.logger.info(f"Deleted glue type: {glue}")

        # Trigger cascade delete for GlueCells if force
        if force:
            self._cascade_delete_glue_cells(glue.name)

        return True, f"Glue type '{glue.name}' deleted successfully"

    def _is_glue_type_in_use(self, glue_name: str) -> bool:
        """
        Check if glue type is referenced by any GlueCells.

        Args:
            glue_name: Name of glue type to check

        Returns:
            True if in use, False otherwise
        """
        try:
            from modules.shared.tools.glue_monitor_system.service_factory import get_service_factory
            cells_manager = get_service_factory().create_cells_manager()

            for cell in cells_manager.get_all_cells():
                cell_type = cell.glue_type.value if hasattr(cell.glue_type, 'value') else str(cell.glue_type)
                if cell_type.lower() == glue_name.lower():
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking glue type usage: {e}")
            # Conservative approach: assume it's in use if we can't check
            return True

    def _cascade_update_glue_cells(self, old_name: str, new_name: str) -> None:
        """
        Update all GlueCells that reference the old glue type name.

        Args:
            old_name: Old glue type name
            new_name: New glue type name
        """
        try:
            from modules.shared.tools.glue_monitor_system.service_factory import get_service_factory
            cells_manager = get_service_factory().create_cells_manager()

            updated_count = 0
            for cell in cells_manager.get_all_cells():
                cell_type = cell.glue_type.value if hasattr(cell.glue_type, 'value') else str(cell.glue_type)
                if cell_type.lower() == old_name.lower():
                    # Update the cell's glue type to new name
                    cells_manager.update_glue_type_by_id(cell.id, new_name)
                    updated_count += 1

            if updated_count > 0:
                self.logger.info(f"Cascade updated {updated_count} glue cells from '{old_name}' to '{new_name}'")
        except Exception as e:
            self.logger.error(f"Error during cascade update of glue cells: {e}")

    def _cascade_delete_glue_cells(self, glue_name: str) -> None:
        """
        Clear glue type references in GlueCells when deleting a glue type.

        Args:
            glue_name: Name of deleted glue type
        """
        try:
            from modules.shared.tools.glue_monitor_system.service_factory import get_service_factory
            cells_manager = get_service_factory().create_cells_manager()

            cleared_count = 0
            for cell in cells_manager.get_all_cells():
                cell_type = cell.glue_type.value if hasattr(cell.glue_type, 'value') else str(cell.glue_type)
                if cell_type.lower() == glue_name.lower():
                    # Clear the reference (set to empty or default)
                    cells_manager.update_glue_type_by_id(cell.id, "")
                    cleared_count += 1

            if cleared_count > 0:
                self.logger.info(f"Cascade cleared {cleared_count} glue cell references to '{glue_name}'")
        except Exception as e:
            self.logger.error(f"Error during cascade delete of glue cells: {e}")

    def reload(self) -> bool:
        """
        Reload glue types from file.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._load_glue_types()
            return True
        except Exception as e:
            self.logger.error(f"Error reloading glue types: {e}")
            return False
