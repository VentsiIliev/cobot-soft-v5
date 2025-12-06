from pathlib import Path
from modules.contour_matching.settings.ContourMatchingSettings import ContourMatchingSettings

# Initialize configuration system
_config_file_path = Path(__file__).resolve().parent.parent.parent.parent / "applications" / "glue_dispensing_application" / "storage" / "settings" / "contour_matching_settings.json"
_settings = ContourMatchingSettings(_config_file_path)

# Expose the configured values as module-level constants for backward compatibility
SIMILARITY_THRESHOLD = _settings.get_similarity_threshold()
DEBUG_SIMILARITY = _settings.get_debug_similarity()
DEBUG_CALCULATE_DIFFERENCES = _settings.get_debug_calculate_differences()
DEBUG_ALIGN_CONTOURS = _settings.get_debug_align_contours()
USE_COMPARISON_MODEL = _settings.get_use_comparison_model()
REFINEMENT_THRESHOLD = _settings.get_refinement_threshold()

# Expose the settings instance for runtime configuration access
def get_settings():
    """Get the ContourMatchingSettings instance for runtime configuration"""
    return _settings

def reload_settings():
    """Reload settings from file"""
    _settings.load_from_file()
    # Update module-level constants
    global SIMILARITY_THRESHOLD, DEBUG_SIMILARITY, DEBUG_CALCULATE_DIFFERENCES
    global DEBUG_ALIGN_CONTOURS, USE_COMPARISON_MODEL, REFINEMENT_THRESHOLD
    
    SIMILARITY_THRESHOLD = _settings.get_similarity_threshold()
    DEBUG_SIMILARITY = _settings.get_debug_similarity()
    DEBUG_CALCULATE_DIFFERENCES = _settings.get_debug_calculate_differences()
    DEBUG_ALIGN_CONTOURS = _settings.get_debug_align_contours()
    USE_COMPARISON_MODEL = _settings.get_use_comparison_model()
    REFINEMENT_THRESHOLD = _settings.get_refinement_threshold()