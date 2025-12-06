import json
from pathlib import Path
from core.model.settings.BaseSettings import Settings
from modules.contour_matching.enums.ContourMatchingSettingKey import ContourMatchingSettingKey


class ContourMatchingSettings(Settings):
    def __init__(self, settings_file_path=None):
        super().__init__()
        self.settings_file_path = settings_file_path
        self._initialize_default_values()
        
        if settings_file_path:
            self.load_from_file(settings_file_path)

    def _initialize_default_values(self):
        """Initialize all settings with default values"""
        # Core matching settings
        self.set_value(ContourMatchingSettingKey.SIMILARITY_THRESHOLD.value, 80)
        self.set_value(ContourMatchingSettingKey.REFINEMENT_THRESHOLD.value, 0.1)
        
        # Debug flags - all disabled by default
        self.set_value(ContourMatchingSettingKey.DEBUG_SIMILARITY.value, False)
        self.set_value(ContourMatchingSettingKey.DEBUG_CALCULATE_DIFFERENCES.value, False)
        self.set_value(ContourMatchingSettingKey.DEBUG_ALIGN_CONTOURS.value, False)
        
        # Strategy selection
        self.set_value(ContourMatchingSettingKey.USE_COMPARISON_MODEL.value, False)

    # Similarity threshold getters/setters
    def get_similarity_threshold(self):
        return self.get_value(ContourMatchingSettingKey.SIMILARITY_THRESHOLD.value, 80)

    def set_similarity_threshold(self, value):
        self.set_value(ContourMatchingSettingKey.SIMILARITY_THRESHOLD.value, value)

    def get_refinement_threshold(self):
        return self.get_value(ContourMatchingSettingKey.REFINEMENT_THRESHOLD.value, 0.1)

    def set_refinement_threshold(self, value):
        self.set_value(ContourMatchingSettingKey.REFINEMENT_THRESHOLD.value, value)

    # Debug flags getters/setters
    def get_debug_similarity(self):
        return self.get_value(ContourMatchingSettingKey.DEBUG_SIMILARITY.value, False)

    def set_debug_similarity(self, value):
        self.set_value(ContourMatchingSettingKey.DEBUG_SIMILARITY.value, value)

    def get_debug_calculate_differences(self):
        return self.get_value(ContourMatchingSettingKey.DEBUG_CALCULATE_DIFFERENCES.value, False)

    def set_debug_calculate_differences(self, value):
        self.set_value(ContourMatchingSettingKey.DEBUG_CALCULATE_DIFFERENCES.value, value)

    def get_debug_align_contours(self):
        return self.get_value(ContourMatchingSettingKey.DEBUG_ALIGN_CONTOURS.value, False)

    def set_debug_align_contours(self, value):
        self.set_value(ContourMatchingSettingKey.DEBUG_ALIGN_CONTOURS.value, value)

    # Strategy selection getters/setters
    def get_use_comparison_model(self):
        return self.get_value(ContourMatchingSettingKey.USE_COMPARISON_MODEL.value, False)

    def set_use_comparison_model(self, value):
        self.set_value(ContourMatchingSettingKey.USE_COMPARISON_MODEL.value, value)

    def to_dict(self):
        """Convert settings to dictionary format for JSON serialization"""
        return {
            ContourMatchingSettingKey.SIMILARITY_THRESHOLD.value: self.get_similarity_threshold(),
            ContourMatchingSettingKey.REFINEMENT_THRESHOLD.value: self.get_refinement_threshold(),
            ContourMatchingSettingKey.DEBUG_SIMILARITY.value: self.get_debug_similarity(),
            ContourMatchingSettingKey.DEBUG_CALCULATE_DIFFERENCES.value: self.get_debug_calculate_differences(),
            ContourMatchingSettingKey.DEBUG_ALIGN_CONTOURS.value: self.get_debug_align_contours(),
            ContourMatchingSettingKey.USE_COMPARISON_MODEL.value: self.get_use_comparison_model(),
        }

    def from_dict(self, data):
        """Load settings from dictionary (JSON structure)"""
        for key, value in data.items():
            if key in [setting.value for setting in ContourMatchingSettingKey]:
                self.set_value(key, value)

    def save_to_file(self, file_path=None):
        """Save settings to JSON file"""
        path = file_path or self.settings_file_path
        if not path:
            raise ValueError("No file path specified for saving settings")
        
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def load_from_file(self, file_path=None):
        """Load settings from JSON file"""
        path = file_path or self.settings_file_path
        if not path or not Path(path).exists():
            return  # Use defaults if file doesn't exist
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.from_dict(data)
        except Exception as e:
            print(f"Error loading contour matching settings from {path}: {e}")
            # Keep default values on error

    def updateSettings(self, settings):
        """Update settings from a dictionary (used by UI)"""
        try:
            for key, value in settings.items():
                if key in [setting.value for setting in ContourMatchingSettingKey]:
                    self.set_value(key, value)
            return True, "Settings updated successfully"
        except Exception as e:
            return False, f"Error updating settings: {str(e)}"