"""Application entry point."""

from __future__ import annotations

from .config_manager import ConfigManager
from .logging_manager import configure_logging
from .paths import ensure_app_directories, get_app_paths


def main() -> None:
    paths = get_app_paths()

    try:
        paths.logs.mkdir(parents=True, exist_ok=True)
        logger = configure_logging(paths)
    except Exception as exc:
        print(f"\nUnable to initialize application logging: {exc}")
        input("Press Enter to exit...")
        return

    logger.info("BookScreenshot %s starting", "0.1.0")
    logger.info("Application directory: %s", paths.base)

    try:
        ensure_app_directories(paths)

        config = ConfigManager(paths)
        settings = config.load_settings()

        logger.info(
            "Interface mode: %s",
            settings.get("interface_mode", "simple"),
        )

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
