import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import threading

class StatisticsRepository:
    """Handles loading and saving statistics to JSON."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.storage_path / "glue_spray_statistics.json"
        self._lock = threading.Lock()

    def load(self) -> Dict[str, Any]:
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[StatisticsRepository] Error loading statistics: {e}")
        return self._default_statistics()

    def save(self, stats: Dict[str, Any]):
        try:
            with self._lock:
                stats["system"]["last_updated"] = datetime.now().isoformat()
                with open(self.stats_file, "w") as f:
                    json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"[StatisticsRepository] Error saving statistics: {e}")

    def _default_statistics(self) -> Dict[str, Any]:
        return {
            "generator": {
                "on_count": 0,
                "off_count": 0,
                "total_runtime_seconds": 0.0,
                "last_on_timestamp": None,
                "last_off_timestamp": None,
                "current_state": "off",
                "session_start": None,
            },
            "motor": {
                "on_count": 0,
                "off_count": 0,
                "total_runtime_seconds": 0.0,
                "last_on_timestamp": None,
                "last_off_timestamp": None,
                "current_state": "off",
                "session_start": None,
            },
            "system": {
                "total_cycles": 0,
                "session_start": datetime.now().isoformat(),
                "last_updated": None,
            },
        }
