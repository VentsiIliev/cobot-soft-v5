from enum import Enum

class ContourMatchingSettingKey(Enum):
    # Core matching settings
    SIMILARITY_THRESHOLD = "SIMILARITY_THRESHOLD"
    REFINEMENT_THRESHOLD = "REFINEMENT_THRESHOLD"
    
    # Debug flags
    DEBUG_SIMILARITY = "DEBUG_SIMILARITY"
    DEBUG_CALCULATE_DIFFERENCES = "DEBUG_CALCULATE_DIFFERENCES"
    DEBUG_ALIGN_CONTOURS = "DEBUG_ALIGN_CONTOURS"
    
    # Strategy selection
    USE_COMPARISON_MODEL = "USE_COMPARISON_MODEL"

    def getAsLabel(self):
        return self.value + ":"