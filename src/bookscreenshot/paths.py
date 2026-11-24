"""Centralized application paths for portable and source runs."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    base: Path
    config: Path
    logs: Path
    captures: Path
    sessions: Path
    modules: Path
    settings_file: Path
    shortcuts_file: Path
    profiles_file: Path
    log_file: Path


def application_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # .../src/bookscreenshot/paths.py -> project root
    return Path(__file__).resolve().parents[2]


def get_app_paths() -> AppPaths:
    base = application_directory()
    config = base / "config"
    logs = base / "logs"
    return AppPaths(
        base=base,
        config=config,
        logs=logs,
        captures=base / "Captures",
        sessions=base / "sessions",
        modules=base / "Modules",
        settings_file=config / "settings.json",
        shortcuts_file=config / "shortcuts.json",
        profiles_file=config / "profiles.json",
        log_file=logs / "BookScreenshot.log",
    )


def ensure_app_directories(paths: AppPaths) -> None:
    for directory in (paths.config, paths.logs, paths.captures, paths.sessions, paths.modules):
        directory.mkdir(parents=True, exist_ok=True)
