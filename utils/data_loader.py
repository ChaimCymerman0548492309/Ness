"""External test-data loader supporting JSON, CSV, and YAML formats."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = PROJECT_ROOT / "data" / "test_scenarios.json"


class DataLoader:
    """Loads data-driven scenarios from external JSON, CSV, or YAML files."""

    def __init__(self, data_file: Path | None = None) -> None:
        self._data_file = data_file or DEFAULT_DATA_FILE

    def load_scenarios(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        payload = self._read_file()
        scenarios = [self._normalize_scenario(item) for item in payload.get("scenarios", [])]
        if enabled_only:
            return [scenario for scenario in scenarios if scenario.get("enabled", True)]
        return scenarios

    def get_scenario(self, scenario_id: str) -> dict[str, Any]:
        for scenario in self.load_scenarios(enabled_only=False):
            if scenario.get("id") == scenario_id:
                return scenario
        raise KeyError(f"Scenario '{scenario_id}' was not found in {self._data_file}")

    def _read_file(self) -> dict[str, Any]:
        suffix = self._data_file.suffix.lower()
        with self._data_file.open(encoding="utf-8", newline="") as handle:
            if suffix in {".yaml", ".yml"}:
                return yaml.safe_load(handle) or {}
            if suffix == ".csv":
                reader = csv.DictReader(handle)
                return {"scenarios": list(reader)}
            return json.load(handle)

    @staticmethod
    def _normalize_scenario(raw: dict[str, Any]) -> dict[str, Any]:
        scenario = dict(raw)

        if "maxPrice" not in scenario and "max_price" in scenario:
            scenario["maxPrice"] = scenario["max_price"]
        if "budgetPerItem" not in scenario and "budget_per_item" in scenario:
            scenario["budgetPerItem"] = scenario["budget_per_item"]

        if "maxPrice" in scenario:
            scenario["maxPrice"] = float(scenario["maxPrice"])
        if "budgetPerItem" in scenario:
            scenario["budgetPerItem"] = float(scenario["budgetPerItem"])
        if "limit" in scenario:
            scenario["limit"] = int(scenario["limit"])

        enabled = scenario.get("enabled", True)
        if isinstance(enabled, str):
            scenario["enabled"] = enabled.strip().lower() in {"1", "true", "yes", "on"}
        else:
            scenario["enabled"] = bool(enabled)

        return scenario
