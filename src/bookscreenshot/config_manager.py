"""Versioned JSON configuration with safe writes and legacy preset migration."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from .paths import AppPaths

LOGGER = logging.getLogger("bookscreenshot.config")
CONFIG_VERSION = 1

DEFAULT_SETTINGS: dict[str, Any] = {
    "config_version": CONFIG_VERSION,
    "interface_mode": "simple",
    "default_image_format": "JPEG",
    "jpeg_quality": 95,
    "default_delay_ms": 300,
    "default_pause_after": 0,
    "keep_screenshots": True,
    "create_pdf": True,
    "open_output_folder": False,
}

DEFAULT_SHORTCUTS: dict[str, Any] = {
    "config_version": CONFIG_VERSION,
    "shortcuts": {
        "capture_current_target": {"enabled": True, "combination": "CTRL+ALT+1", "scope": "global"},
        "capture_primary_monitor": {
            "enabled": True,
            "combination": "CTRL+ALT+2",
            "scope": "global",
        },
        "capture_all_monitors": {"enabled": True, "combination": "CTRL+ALT+3", "scope": "global"},
        "select_region": {"enabled": True, "combination": "CTRL+ALT+4", "scope": "global"},
        "select_window": {"enabled": True, "combination": "CTRL+ALT+5", "scope": "global"},
        "cancel_operation": {"enabled": True, "combination": "ESC", "scope": "application"},
    },
}


class ConfigManager:
    def __init__(self, paths: AppPaths):
        self.paths = paths
        self.paths.config.mkdir(parents=True, exist_ok=True)
        self._ensure_file(paths.settings_file, DEFAULT_SETTINGS)
        self._ensure_file(paths.shortcuts_file, DEFAULT_SHORTCUTS)
        self._migrate_legacy_presets_if_needed()
        self._ensure_file(
            paths.profiles_file, {"config_version": CONFIG_VERSION, "custom_profiles": []}
        )

    @staticmethod
    def _atomic_write(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=4, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    def _ensure_file(self, path: Path, defaults: Any) -> None:
        if not path.exists():
            self._atomic_write(path, defaults)

    def read_json(self, path: Path, defaults: Any) -> Any:
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
            if not isinstance(value, type(defaults)):
                raise ValueError(f"Unexpected top-level JSON type in {path.name}")
            return value
        except FileNotFoundError:
            self._atomic_write(path, defaults)
            return defaults.copy() if isinstance(defaults, dict) else list(defaults)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            LOGGER.exception("Could not load configuration %s: %s", path, exc)
            backup = path.with_suffix(path.suffix + ".invalid")
            try:
                if path.exists() and not backup.exists():
                    path.replace(backup)
            except OSError:
                LOGGER.exception("Could not preserve invalid configuration file %s", path)
            self._atomic_write(path, defaults)
            return defaults.copy() if isinstance(defaults, dict) else list(defaults)

    def load_settings(self) -> dict[str, Any]:
        data = self.read_json(self.paths.settings_file, DEFAULT_SETTINGS)
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        merged["config_version"] = CONFIG_VERSION
        return merged

    def save_settings(self, settings: dict[str, Any]) -> None:
        data = DEFAULT_SETTINGS.copy()
        data.update(settings)
        data["config_version"] = CONFIG_VERSION
        self._atomic_write(self.paths.settings_file, data)

    def load_shortcuts(self) -> dict[str, Any]:
        data = self.read_json(self.paths.shortcuts_file, DEFAULT_SHORTCUTS)
        merged = DEFAULT_SHORTCUTS.copy()
        merged.update(data)
        merged["shortcuts"] = {**DEFAULT_SHORTCUTS["shortcuts"], **data.get("shortcuts", {})}
        merged["config_version"] = CONFIG_VERSION
        return merged

    def save_shortcuts(self, shortcuts: dict[str, Any]) -> None:
        data = DEFAULT_SHORTCUTS.copy()
        data.update(shortcuts)
        data["config_version"] = CONFIG_VERSION
        self._atomic_write(self.paths.shortcuts_file, data)

    def load_custom_profiles(self) -> list[dict[str, Any]]:
        data = self.read_json(
            self.paths.profiles_file, {"config_version": CONFIG_VERSION, "custom_profiles": []}
        )
        profiles = data.get("custom_profiles", [])
        return profiles if isinstance(profiles, list) else []

    def save_custom_profiles(self, profiles: list[dict[str, Any]]) -> None:
        self._atomic_write(
            self.paths.profiles_file,
            {
                "config_version": CONFIG_VERSION,
                "custom_profiles": profiles,
            },
        )

    def _migrate_legacy_presets_if_needed(self) -> None:
        if self.paths.profiles_file.exists():
            return
        legacy_path = self.paths.base / "custom_presets.json"
        if not legacy_path.exists():
            return
        try:
            with legacy_path.open("r", encoding="utf-8") as handle:
                old_data = json.load(handle)
            if not isinstance(old_data, list):
                raise ValueError("Legacy custom presets must be a JSON list")
            self._atomic_write(
                self.paths.profiles_file,
                {
                    "config_version": CONFIG_VERSION,
                    "custom_profiles": old_data,
                },
            )
            LOGGER.info("Migrated %d custom presets from %s", len(old_data), legacy_path)
        except (OSError, json.JSONDecodeError, ValueError):
            LOGGER.exception("Could not migrate legacy custom presets from %s", legacy_path)
