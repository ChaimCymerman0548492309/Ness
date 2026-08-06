"""External test-data loader supporting JSON and YAML formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = PROJECT_ROOT / "data" / "test_scenarios.json"


class DataLoader:
    """Loads data-driven scenarios from external JSON or YAML files."""

    def __init__(self, data_file: Path | None = None) -> None:
        self._data_file = data_file or DEFAULT_DATA_FILE

    def load_scenarios(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        # Reads and returns test scenarios from the configured data file.
        payload = self._read_file()
        scenarios = payload.get("scenarios", [])
        if enabled_only:
            return [scenario for scenario in scenarios if scenario.get("enabled", True)]
        return scenarios

    def get_scenario(self, scenario_id: str) -> dict[str, Any]:
        # Returns a single scenario dict by its unique id, or raises KeyError.
        for scenario in self.load_scenarios(enabled_only=False):
            if scenario.get("id") == scenario_id:
                return scenario
        raise KeyError(f"Scenario '{scenario_id}' was not found in {self._data_file}")

    def _read_file(self) -> dict[str, Any]:
        # Parses the data file based on its extension (.json or .yaml/.yml).
        suffix = self._data_file.suffix.lower()
        with self._data_file.open(encoding="utf-8") as handle:
            if suffix in {".yaml", ".yml"}:
                return yaml.safe_load(handle) or {}
            return json.load(handle)
