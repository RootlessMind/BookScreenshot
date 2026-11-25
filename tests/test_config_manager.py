import json
from pathlib import Path

from bookscreenshot.config_manager import ConfigManager
from bookscreenshot.paths import AppPaths


def make_paths(tmp_path: Path) -> AppPaths:
    config = tmp_path / "config"
    logs = tmp_path / "logs"
    return AppPaths(
        base=tmp_path,
        config=config,
        logs=logs,
        captures=tmp_path / "Captures",
        sessions=tmp_path / "sessions",
        modules=tmp_path / "Modules",
        settings_file=config / "settings.json",
        shortcuts_file=config / "shortcuts.json",
        profiles_file=config / "profiles.json",
        log_file=logs / "BookScreenshot.log",
    )


def test_creates_default_json_files(tmp_path):
    paths = make_paths(tmp_path)
    manager = ConfigManager(paths)

    assert paths.settings_file.exists()
    assert paths.shortcuts_file.exists()
    assert paths.profiles_file.exists()
    assert manager.load_settings()["interface_mode"] == "simple"
    assert "capture_all_monitors" in manager.load_shortcuts()["shortcuts"]


def test_saves_and_reloads_settings(tmp_path):
    manager = ConfigManager(make_paths(tmp_path))
    settings = manager.load_settings()
    settings["default_delay_ms"] = 450
    manager.save_settings(settings)

    assert manager.load_settings()["default_delay_ms"] == 450


def test_saves_custom_profiles(tmp_path):
    manager = ConfigManager(make_paths(tmp_path))
    profiles = [
        {"name": "My reader", "turn": [10, 20], "activate": [30, 40], "crop": [0, 0, 100, 100]}
    ]
    manager.save_custom_profiles(profiles)

    assert manager.load_custom_profiles() == profiles


def test_migrates_legacy_custom_presets(tmp_path):
    legacy = [
        {
            "name": "Old profile",
            "reader": "Custom",
            "turn": [1, 2],
            "activate": [3, 4],
            "crop": [0, 0, 10, 10],
        }
    ]
    (tmp_path / "custom_presets.json").write_text(json.dumps(legacy), encoding="utf-8")

    manager = ConfigManager(make_paths(tmp_path))

    assert manager.load_custom_profiles() == legacy
    # Migration deliberately leaves the original file untouched as a backup.
    assert (tmp_path / "custom_presets.json").exists()
