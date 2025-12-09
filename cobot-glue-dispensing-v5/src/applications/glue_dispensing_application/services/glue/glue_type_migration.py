"""
Glue Type Migration Utilities
Helper functions for migrating from GlueType enum to string-based types.
"""
import warnings
from typing import Union, Optional
def migrate_glue_type_to_string(glue_type: Union['GlueType', str]) -> str:
    """
    Convert GlueType enum or string to plain string.
    Args:
        glue_type: GlueType enum instance or string
    Returns:
        String representation of glue type
    Examples:
        GlueType.TypeA → "Type A"
        "Type A" → "Type A"
    """
    if isinstance(glue_type, str):
        return glue_type.strip()
    if hasattr(glue_type, 'value'):
        warnings.warn(
            "GlueType enum usage detected. Please use string directly.",
            DeprecationWarning,
            stacklevel=2
        )
        return str(glue_type.value)
    return str(glue_type)
def validate_glue_type(glue_type_str: str, allow_empty: bool = False) -> bool:
    """
    Validate glue type string against registered types.
    Args:
        glue_type_str: Glue type name to validate
        allow_empty: Whether to allow empty string
    Returns:
        True if valid, False otherwise
    """
    if not glue_type_str and allow_empty:
        return True
    if not glue_type_str:
        return False
    from applications.glue_dispensing_application.handlers.glue_types_handler import GlueTypesHandler
    handler = GlueTypesHandler()
    return handler.service.exists(glue_type_str)
def get_all_glue_type_names() -> list[str]:
    """
    Get list of all registered glue type names.
    Returns:
        List of glue type names
    """
    from applications.glue_dispensing_application.handlers.glue_types_handler import GlueTypesHandler
    handler = GlueTypesHandler()
    glue_types = handler.service.get_all()
    return [glue.name for glue in glue_types]
