"""
Glue Types Handler

Handles API requests for glue type management operations.
Provides request/response handling layer between API dispatcher and service layer.
"""

from typing import Tuple, Dict, Any, List, Optional
from applications.glue_dispensing_application.services.glue.glue_types_service import GlueTypesService
from applications.glue_dispensing_application.repositories.glue_types_repository import GlueTypesRepository
from applications.glue_dispensing_application.model.glue.glue_field import GlueField
from core.application.ApplicationStorageResolver import get_app_settings_path


class GlueTypesHandler:
    """
    Handler for glue types API requests.
    
    Translates API requests into service calls and formats responses.
    Follows the handler pattern used in BaseApplicationSettingsHandler.
    """
    
    def __init__(self):
        """Initialize handler with service instance."""
        # Get file path using ApplicationStorageResolver
        file_path = get_app_settings_path("glue_dispensing_application", "glue_types.json")
        repository = GlueTypesRepository(file_path)
        repository.initialize_default_types()
        self.service = GlueTypesService(repository)
        self.repository = repository  # Keep reference for direct access if needed

    def handle_get_glue_types(self, data: Dict[str, Any] = None) -> Tuple[bool, str, List[Dict]]:
        """
        Get all glue types.
        
        Args:
            data: Request data (not used for GET operation)
            
        Returns:
            Tuple of (success: bool, message: str, glue_types: List[Dict])
        """
        glue_types = self.service.get_all()
        glue_types_data = [glue.to_json() for glue in glue_types]
        
        return True, f"Retrieved {len(glue_types)} glue type(s)", glue_types_data
    
    def handle_add_glue_type(self, data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """
        Add a new glue type.
        
        Args:
            data: Dictionary containing:
                - name (str): Name of the glue type (required)
                - description (str): Description (optional)
                
        Returns:
            Tuple of (success: bool, message: str, glue_data: Optional[Dict])
        """
        name = data.get(GlueField.NAME.value, "").strip()
        description = data.get(GlueField.DESCRIPTION.value, "").strip()
        
        # Validate required fields
        if not name:
            return False, "Glue type name is required", None
        
        # Call service layer
        success, message, glue = self.service.add(name, description)
        
        if success and glue:
            return True, message, glue.to_json()
        else:
            return False, message, None
    
    def handle_update_glue_type(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing glue type.
        
        Args:
            data: Dictionary containing:
                - id (str): Glue type ID (required)
                - name (str): New name (required)
                - description (str): New description (optional)
                
        Returns:
            Tuple of (success: bool, message: str)
        """
        glue_id = data.get(GlueField.ID.value, "").strip()
        name = data.get(GlueField.NAME.value, "").strip()
        description = data.get(GlueField.DESCRIPTION.value, "").strip()
        
        # Validate required fields
        if not glue_id:
            return False, "Glue type ID is required"
        if not name:
            return False, "Glue type name is required"
        
        # Call service layer
        return self.service.update(glue_id, name, description)
    
    def handle_remove_glue_type(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Remove a glue type.
        
        Args:
            data: Dictionary containing:
                - id (str): Glue type ID to remove (required)
                - force (bool): Force delete even if in use (optional, default False)
                
        Returns:
            Tuple of (success: bool, message: str)
        """
        glue_id = data.get(GlueField.ID.value, "").strip()
        force = data.get("force", False)
        
        # Validate required fields
        if not glue_id:
            return False, "Glue type ID is required"
        
        # Call service layer
        return self.service.delete(glue_id, force=force)
