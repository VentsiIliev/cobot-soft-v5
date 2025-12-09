"""
Glue Application Constants

This module defines constants specific to the glue dispensing application,
including request resources and endpoint definitions.
"""

# === GLUE APPLICATION RESOURCES ===
REQUEST_RESOURCE_GLUE = "Glue"                    # Glue dispensing system resource
REQUEST_RESOURCE_GLUE_NOZZLE = "GlueNozzle"      # Glue nozzle control resource

# === GLUE APPLICATION ENDPOINTS ===

# Glue system configuration management
SETTINGS_GLUE_GET = "/api/v1/settings/glue/get"
SETTINGS_GLUE_SET = "/api/v1/settings/glue/set"

# Glue cells configuration management
GLUE_CELLS_CONFIG_GET = "/api/v1/settings/glue/cells"
GLUE_CELLS_CONFIG_SET = "/api/v1/settings/glue/cells/set"
GLUE_CELL_UPDATE = "/api/v1/settings/glue/cells/update"
GLUE_CELL_CALIBRATE = "/api/v1/settings/glue/cells/calibrate"
GLUE_CELL_TARE = "/api/v1/settings/glue/cells/tare"
GLUE_CELL_UPDATE_TYPE = "/api/v1/settings/glue/cells/type"

GLUE_TYPES_GET = "/api/v1/settings/glue/types/get"
GLUE_TYPES_SET = "/api/v1/settings/glue/types/set"
GLUE_TYPE_ADD_CUSTOM = "/api/v1/settings/glue/types/add/custom"
GLUE_TYPE_REMOVE_CUSTOM = "/api/v1/settings/glue/types/remove/custom"


# Glue application specific operations
GLUE_NOZZLE_CLEAN = "glue/nozzle/clean"
GLUE_SPRAY_START = "glue/spray/start"
GLUE_SPRAY_STOP = "glue/spray/stop"
GLUE_CALIBRATE_NOZZLE = "glue/calibrate/nozzle"

# Glue cell weight monitoring
GLUE_CELL_WEIGHTS_GET = "/api/v1/glue/cells/weights"
GLUE_CELL_WEIGHT_GET = "/api/v1/glue/cells/weight"

