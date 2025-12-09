# GlueType Enum Migration Plan

**Date:** December 9, 2025  
**Goal:** Deprecate hardcoded `GlueType` enum and migrate to dynamic glue types from persistence layer

---

## Current Situation Analysis

### GlueType Enum Location
- **File**: `src/modules/shared/tools/glue_monitor_system/glue_type.py`
- **Current Values**: TypeA, TypeB, TypeC, TypeD (hardcoded)
- **Usage**: 10 active files import and use this enum

### Files Using GlueType Enum
1. ✅ `modules/shared/tools/GlueCell.py` - Core cell model
2. ✅ `modules/shared/tools/glue_monitor_system/config.py` - Config loading
3. ✅ `modules/shared/tools/glue_monitor_system/interfaces.py` - Type hints
4. ✅ `modules/shared/tools/glue_monitor_system/cells_manager.py` - Cell manager
5. ✅ `modules/shared/tools/glue_monitor_system/models/cell_models.py` - Data models
6. ✅ `modules/shared/tools/glue_monitor_system/models/dto.py` - DTOs
7. ✅ `modules/shared/tools/glue_monitor_system/config_validator.py` - Validation
8. ✅ `modules/shared/tools/glue_monitor_system/glue_cells_manager.py` - Legacy manager
9. ✅ `plugins/core/dashboard/ui/factories/GlueCardFactory.py` - UI factory
10. ✅ `plugins/core/settings/ui/LoadCellsSettingsTabLayout.py` - Settings UI

---

## Migration Strategy

### Phase 1: Backward-Compatible Transition ✅ (Current)
**Status**: Already implemented via glue types persistence system

**What exists**:
- ✅ Dynamic glue types with JSON persistence
- ✅ API endpoints for CRUD operations
- ✅ UI for managing custom types
- ✅ Repository, Service, Handler layers

**What we'll add**:
- Deprecation warnings on enum usage
- Migration utilities to convert enum → string
- Type validation using dynamic types list

### Phase 2: Replace Enum with String Type 🔄 (This Plan)
**Goal**: Change `GlueType` enum to plain `str` throughout codebase

**Changes needed**:
1. Update type hints: `GlueType` → `str`
2. Store glue type as string in models
3. Validate against dynamic types from persistence
4. UI dropdowns populated from API instead of enum

### Phase 3: Complete Removal 🔮 (Future)
**Goal**: Remove enum file entirely

**Conditions**:
- All data migrated to strings
- No enum references in codebase
- UI fully using dynamic types

---

## Detailed Implementation Plan

### Step 1: Add Deprecation Warning to Enum
**File**: `src/modules/shared/tools/glue_monitor_system/glue_type.py`

```python
import warnings
from enum import Enum


class GlueType(Enum):
    """
    DEPRECATED: This enum is deprecated and will be removed in a future version.
    
    Use dynamic glue types from GlueTypesService instead:
    - Get types: GlueTypesHandler.handle_get_glue_types()
    - Validate: GlueTypesService.exists(name)
    
    Built-in types (TypeA-D) are now stored as regular custom types.
    """
    
    TypeA = "Type A"
    TypeB = "Type B"
    TypeC = "Type C"
    TypeD = "Type D"

    def __init__(self, value):
        warnings.warn(
            f"GlueType enum is deprecated. Use string '{value}' directly instead. "
            "This enum will be removed in v6.0.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__()

    def __str__(self):
        return self.value
```

### Step 2: Populate Default Types in Repository
**File**: `src/applications/glue_dispensing_application/repositories/glue_types_repository.py`

**Add method**:
```python
def initialize_default_types(self) -> None:
    """
    Initialize default glue types (Type A-D) if file doesn't exist.
    These replace the hardcoded enum values.
    """
    if self.file_path.exists():
        return  # Already initialized
    
    default_types = [
        Glue(name="Type A", description="Built-in glue type A"),
        Glue(name="Type B", description="Built-in glue type B"),
        Glue(name="Type C", description="Built-in glue type C"),
        Glue(name="Type D", description="Built-in glue type D"),
    ]
    
    self.save(default_types)
    self.logger.info(f"Initialized default glue types at {self.file_path}")
```

**Call in handler init**:
```python
# In GlueTypesHandler.__init__
repository = GlueTypesRepository(file_path)
repository.initialize_default_types()  # Add this line
self.service = GlueTypesService(repository)
```

### Step 3: Create Migration Utilities
**New File**: `src/applications/glue_dispensing_application/services/glue/glue_type_migration.py`

```python
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
    
    # Handle enum
    if hasattr(glue_type, 'value'):
        warnings.warn(
            "GlueType enum usage detected. Please use string directly.",
            DeprecationWarning,
            stacklevel=2
        )
        return str(glue_type.value)
    
    # Fallback
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
    
    # Import here to avoid circular dependency
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
```

### Step 4: Update GlueCell Model
**File**: `src/modules/shared/tools/GlueCell.py`

**Current**:
```python
from modules.shared.tools.glue_monitor_system.glue_type import GlueType

class GlueCell:
    def __init__(self, glue_type: GlueType, ...):
        self.glue_type = glue_type
```

**Updated**:
```python
from typing import Union
from modules.shared.tools.glue_monitor_system.glue_type import GlueType  # Keep for backward compat
from applications.glue_dispensing_application.services.glue.glue_type_migration import migrate_glue_type_to_string

class GlueCell:
    def __init__(self, glue_type: Union[GlueType, str], ...):
        """
        Args:
            glue_type: Glue type name (str) or deprecated GlueType enum
        """
        # Normalize to string
        self.glue_type = migrate_glue_type_to_string(glue_type)
    
    def to_dict(self):
        return {
            # ...existing fields...
            "type": self.glue_type,  # Now always a string
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        glue_type = data.get("type", "")
        # If it's an enum value string, use directly
        return cls(glue_type=glue_type, ...)
```

### Step 5: Update Config Models
**File**: `src/modules/shared/tools/glue_monitor_system/models/cell_models.py`

**Current**:
```python
@dataclass
class CellConfig:
    type: GlueType
```

**Updated**:
```python
from typing import Union

@dataclass
class CellConfig:
    type: str  # Changed from GlueType to str
    
    def __post_init__(self):
        """Ensure type is always a string"""
        from applications.glue_dispensing_application.services.glue.glue_type_migration import migrate_glue_type_to_string
        self.type = migrate_glue_type_to_string(self.type)
```

### Step 6: Update Config Loader
**File**: `src/modules/shared/tools/glue_monitor_system/config.py`

**Current**:
```python
def _parse_cell_type(type_str: str) -> GlueType:
    try:
        return GlueType[type_str]
    except KeyError:
        return GlueType.TypeA
```

**Updated**:
```python
def _parse_cell_type(type_str: str) -> str:
    """
    Parse cell type from config.
    
    Args:
        type_str: Type string from JSON (e.g., "TypeA" or "Type A")
        
    Returns:
        Normalized glue type name (e.g., "Type A")
    """
    # Map old enum names to full names
    enum_mapping = {
        "TypeA": "Type A",
        "TypeB": "Type B", 
        "TypeC": "Type C",
        "TypeD": "Type D",
    }
    
    # Check if it's an old enum name
    if type_str in enum_mapping:
        return enum_mapping[type_str]
    
    # Return as-is (custom type)
    return type_str.strip()
```

### Step 7: Update Config Validator
**File**: `src/modules/shared/tools/glue_monitor_system/config_validator.py`

**Current**:
```python
def _validate_type(self, type_value) -> bool:
    if isinstance(type_value, str):
        return type_value in [e.name for e in GlueType]
    return isinstance(type_value, GlueType)
```

**Updated**:
```python
def _validate_type(self, type_value) -> bool:
    """
    Validate glue type against registered types.
    
    Args:
        type_value: Type to validate (string or legacy enum)
        
    Returns:
        True if valid
    """
    from applications.glue_dispensing_application.services.glue.glue_type_migration import (
        migrate_glue_type_to_string,
        validate_glue_type
    )
    
    # Convert to string
    type_str = migrate_glue_type_to_string(type_value)
    
    # Validate against registered types
    return validate_glue_type(type_str, allow_empty=False)
```

### Step 8: Update CellsManager
**File**: `src/modules/shared/tools/glue_monitor_system/cells_manager.py`

**Update method signatures**:
```python
def update_glue_type_by_id(self, cell_id: str, glue_type: str) -> bool:
    """
    Update glue type for a cell.
    
    Args:
        cell_id: Cell identifier
        glue_type: New glue type NAME (string, not enum)
        
    Returns:
        True if updated successfully
    """
    # ...existing implementation...
    # Ensure it stores as string in config
```

### Step 9: Update UI Components

#### A. LoadCellsSettingsTabLayout
**File**: `src/plugins/core/settings/ui/LoadCellsSettingsTabLayout.py`

**Current**:
```python
from modules.shared.tools.glue_monitor_system.glue_type import GlueType

# Populate dropdown
for glue_type in GlueType:
    dropdown.addItem(glue_type.value)
```

**Updated**:
```python
from applications.glue_dispensing_application.services.glue.glue_type_migration import get_all_glue_type_names

# Populate dropdown from API
glue_type_names = get_all_glue_type_names()
for name in glue_type_names:
    dropdown.addItem(name)
```

#### B. GlueCardFactory
**File**: `src/plugins/core/dashboard/ui/factories/GlueCardFactory.py`

**Update to work with string types instead of enum**:
```python
# Remove enum import, work with strings directly
def create_card(self, cell_data: dict):
    glue_type_name = cell_data.get("type", "Unknown")
    # ...use string directly...
```

### Step 10: Update DTOs
**File**: `src/modules/shared/tools/glue_monitor_system/models/dto.py`

**Current**:
```python
@dataclass
class CellDTO:
    type: GlueType
    
    def to_dict(self):
        return {"type": self.type.value}
```

**Updated**:
```python
@dataclass
class CellDTO:
    type: str  # Changed from GlueType
    
    def to_dict(self):
        return {"type": self.type}  # Already a string
```

### Step 11: Data Migration Script
**New File**: `src/scripts/migrate_glue_types_data.py`

```python
"""
Data Migration Script: GlueType Enum to String

Migrates glue_cell_config.json from enum names (TypeA) to full names (Type A).
"""

import json
from pathlib import Path

def migrate_config_file(config_path: Path):
    """Migrate config file from enum names to full names"""
    
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return
    
    # Enum to full name mapping
    mapping = {
        "TypeA": "Type A",
        "TypeB": "Type B",
        "TypeC": "Type C",
        "TypeD": "Type D",
    }
    
    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Migrate cells
    modified = False
    for cell in config.get("cells", []):
        old_type = cell.get("type", "")
        if old_type in mapping:
            cell["type"] = mapping[old_type]
            modified = True
            print(f"Migrated: {old_type} → {mapping[old_type]}")
    
    # Save if modified
    if modified:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Migration complete: {config_path}")
    else:
        print(f"No migration needed: {config_path}")


if __name__ == "__main__":
    from core.application.ApplicationStorageResolver import get_app_settings_path
    
    config_path = Path(get_app_settings_path("glue_dispensing_application", "glue_cell_config.json"))
    migrate_config_file(config_path)
```

---

## Implementation Order

### Week 1: Preparation & Deprecation
1. ✅ Add deprecation warning to GlueType enum
2. ✅ Add default types initialization to repository
3. ✅ Create migration utilities file
4. ✅ Run migration script on existing data

### Week 2: Model Layer Migration
5. ✅ Update GlueCell model to accept both enum and string
6. ✅ Update CellConfig dataclass
7. ✅ Update DTOs
8. ✅ Update config loader and validator

### Week 3: Service Layer Migration
9. ✅ Update CellsManager methods
10. ✅ Update interfaces to use string type hints
11. ✅ Test all CRUD operations with strings

### Week 4: UI Layer Migration
12. ✅ Update LoadCellsSettingsTabLayout dropdown
13. ✅ Update GlueCardFactory
14. ✅ Update GlueSettingsTabLayout enum checks
15. ✅ Test UI with dynamic types

### Week 5: Testing & Validation
16. ✅ Integration testing
17. ✅ Data migration verification
18. ✅ Deprecation warnings review
19. ✅ Documentation updates

### Week 6: Cleanup (Optional - Future)
20. 🔮 Remove enum file entirely
21. 🔮 Remove migration utilities
22. 🔮 Update all type hints to pure `str`

---

## Testing Checklist

### Data Migration
- [ ] Existing glue_cell_config.json migrates correctly
- [ ] TypeA → "Type A" conversion works
- [ ] Custom types preserved
- [ ] No data loss

### Backward Compatibility
- [ ] Old code using enum still works (with warnings)
- [ ] New code using strings works
- [ ] Mixed usage (enum + string) works
- [ ] Config files with old enum names load correctly

### UI Functionality
- [ ] Dropdowns populated from API, not enum
- [ ] Type selection saves as string
- [ ] Display shows correct names
- [ ] Custom types appear in dropdowns

### API Integration
- [ ] CRUD operations work with string types
- [ ] Validation uses dynamic types list
- [ ] Cascade updates work correctly
- [ ] No enum references in API responses

---

## Risk Mitigation

### Risk 1: Data Corruption
**Mitigation**: 
- Backup glue_cell_config.json before migration
- Migration script is idempotent (can run multiple times)
- Rollback plan: restore from backup

### Risk 2: Breaking Changes
**Mitigation**:
- Keep enum for backward compatibility (Phase 1)
- Use Union[GlueType, str] type hints during transition
- Gradual migration over multiple weeks

### Risk 3: UI Dropdown Empty
**Mitigation**:
- Initialize default types (Type A-D) on first run
- Fallback to default list if API fails
- Error handling in UI population code

### Risk 4: Validation Failures
**Mitigation**:
- Allow empty/unknown types during transition
- Warn on invalid types instead of rejecting
- Provide clear error messages

---

## Success Criteria

✅ **Phase 1 Complete When**:
- All glue types stored in glue_types.json
- Default types (A-D) created automatically
- Enum has deprecation warnings
- No new enum usage introduced

✅ **Phase 2 Complete When**:
- All models use `str` instead of `GlueType`
- UI dropdowns populated from API
- Config files use full names (not enum names)
- All tests pass with string types

✅ **Phase 3 Complete When**:
- Enum file deleted
- No enum imports in codebase
- All type hints use `str`
- Documentation updated

---

## Rollback Plan

If migration causes issues:

1. **Restore data**: `git checkout glue_cell_config.json`
2. **Revert code**: `git revert <migration-commit>`
3. **Re-enable enum**: Remove deprecation warnings
4. **Investigate**: Review error logs and fix issues
5. **Retry**: Plan smaller incremental changes

---

## Key Files Summary

### To Modify (11 files)
1. `glue_type.py` - Add deprecation warning
2. `glue_types_repository.py` - Add default types init
3. `GlueCell.py` - Accept Union[GlueType, str]
4. `cell_models.py` - Change type hint to str
5. `config.py` - Update type parser
6. `config_validator.py` - Use dynamic validation
7. `cells_manager.py` - Update signatures
8. `dto.py` - Change type hints
9. `LoadCellsSettingsTabLayout.py` - Populate from API
10. `GlueCardFactory.py` - Use string directly
11. `interfaces.py` - Update type hints

### To Create (2 files)
1. `glue_type_migration.py` - Migration utilities
2. `migrate_glue_types_data.py` - Data migration script

### Data Files Affected
1. `glue_cell_config.json` - Cell configurations
2. `glue_types.json` - New dynamic types storage

---

## Communication Plan

### Developers
- Document enum deprecation in changelog
- Update coding standards
- Code review checklist for new code

### Users
- No impact - UI behavior unchanged
- More flexibility to add custom types
- Better error messages

---

## Timeline

- **Week 1**: Deprecation & preparation (Low risk)
- **Week 2-3**: Model migration (Medium risk)
- **Week 4**: UI migration (Medium risk)
- **Week 5**: Testing (Low risk)
- **Week 6+**: Cleanup when stable (Future)

**Total Estimated Time**: 5-6 weeks for complete migration

---

**Next Action**: Start with Step 1 (Add deprecation warning) - this is non-breaking and gives visibility into current usage patterns.

