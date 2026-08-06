"""Application configuration loader."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


class ConfigLoader:
    """Loads YAML settings and merges environment/profile overrides."""

    def __init__(self, config_path: Path | None = None) -> None:
        # Initializes config by loading .env files and parsing settings.yaml.
        load_dotenv(PROJECT_ROOT / ".env")
        load_dotenv(PROJECT_ROOT / "config" / "env.example")
        self._config_path = config_path or CONFIG_PATH
        self._raw = self._load_yaml()
        self._profile = os.getenv("ENV_PROFILE", "dev")

    def _load_yaml(self) -> dict[str, Any]:
        # Reads and parses the YAML configuration file from disk.
        with self._config_path.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    @property
    def profile(self) -> str:
        # Returns the active environment profile name (e.g. dev, ci).
        return self._profile

    def get(self, key: str, default: Any = None) -> Any:
        # Resolves a config key with profile and environment variable overrides.
        profile_overrides = self._raw.get("profiles", {}).get(self._profile, {})
        merged = {**self._raw.get("default", {}), **profile_overrides}

        env_map = {
            "base_url": os.getenv("BASE_URL"),
            "headless": os.getenv("HEADLESS"),
            "slow_mo": os.getenv("SLOW_MO"),
        }
        for env_key, env_value in env_map.items():
            if env_value is not None:
                if env_key == "headless":
                    merged[env_key] = env_value.lower() in {"1", "true", "yes"}
                elif env_key == "slow_mo":
                    merged[env_key] = int(env_value)
                else:
                    merged[env_key] = env_value

        if "." not in key:
            return merged.get(key, default)

        current: Any = self._raw
        for part in key.split("."):
            if not isinstance(current, dict):
                return default
            current = current.get(part, default)
        return current

    def section(self, name: str) -> dict[str, Any]:
        # Returns a named configuration section as a dictionary.
        value = self._raw.get(name, {})
        return value if isinstance(value, dict) else {}
