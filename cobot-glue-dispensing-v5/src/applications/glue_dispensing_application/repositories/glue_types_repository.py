"""
Glue Types Repository

Handles persistence of glue types to JSON file.
Provides CRUD operations with file I/O.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from applications.glue_dispensing_application.model.glue.glue import Glue


class GlueTypesRepository:
    """
    Repository for managing glue types persistence.

    Handles reading/writing glue types to JSON file.
    """

    CURRENT_VERSION = "1.0"

    def __init__(self, file_path: str):
        """
        Initialize repository with file path.

        Args:
            file_path: Full path to glue_types.json file
        """
        self.file_path = Path(file_path)
        self.logger = logging.getLogger(self.__class__.__name__)

    def load(self) -> List[Glue]:
        """
        Load all glue types from file.

        Returns:
            List of Glue instances (empty if file doesn't exist)
        """
        if not self.file_path.exists():
            self.logger.info(f"Glue types file not found at {self.file_path}")
            return []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate structure
            if not isinstance(data, dict) or "glue_types" not in data:
                self.logger.warning("Invalid glue types file structure, returning empty list")
                return []

            # Deserialize glue types
            glue_types = []
            for glue_data in data.get("glue_types", []):
                try:
                    glue = Glue.deserialize(glue_data)
                    glue_types.append(glue)
                except Exception as e:
                    self.logger.error(f"Error deserializing glue type: {e}")

            self.logger.debug(f"Loaded {len(glue_types)} glue types from {self.file_path}")
            return glue_types

        except Exception as e:
            self.logger.error(f"Error loading glue types: {e}")
            return []

    def save(self, glue_types: List[Glue]) -> bool:
        """
        Save glue types to file.

        Args:
            glue_types: List of Glue instances to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(self.file_path.parent, exist_ok=True)

            # Prepare data structure
            data = {
                "version": self.CURRENT_VERSION,
                "glue_types": [glue.to_json() for glue in glue_types]
            }

            # Atomic write using temp file
            temp_file = str(self.file_path) + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic move
            os.replace(temp_file, self.file_path)

            self.logger.info(f"Saved {len(glue_types)} glue types to {self.file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving glue types: {e}")
            return False

    def initialize_default_types(self) -> None:
        """
        Initialize default glue types (Type A-D) if file doesn't exist.
        These replace the hardcoded enum values.
        """
        if self.file_path.exists():
            return

        default_types = [
            Glue(name="Type A", description="Built-in glue type A"),
            Glue(name="Type B", description="Built-in glue type B"),
            Glue(name="Type C", description="Built-in glue type C"),
            Glue(name="Type D", description="Built-in glue type D"),
        ]

        self.save(default_types)
        self.logger.info(f"Initialized default glue types at {self.file_path}")

    def get_file_path(self) -> str:
        """Get the repository file path."""
        return str(self.file_path)
