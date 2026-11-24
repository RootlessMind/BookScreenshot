"""Application entry point."""
from __future__ import annotations

import logging

from .config_manager import ConfigManager
from .logging_manager import configure_logging
from .paths import ensure_app_directories, get_app_paths


def main() -> None:
    paths = get_app_paths()
    ensure_app_directories(paths)
    logger = configure_logging(paths)
    config = ConfigManager(paths)
    settings = config.load_settings()

    logger.info("BookScreenshot %s starting", "0.1.0")
    logger.info("Application directory: %s", paths.base)
    logger.info("Interface mode: %s", settings.get("interface_mode", "simple"))

    try:
        # The existing capture workflow is retained during the first
        # architectural migration. New menus and capture modes will be
        # introduced in subsequent stages.
        from .legacy_capture import main as legacy_main
        legacy_main()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nOperation interrupted.")
    except Exception:
        logger.exception("Unhandled application error")
        print("\nAn unexpected error occurred. See logs/BookScreenshot.log for details.")
        input("Press Enter to exit...")
    finally:
        logger.info("BookScreenshot shutting down")
