"""Application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .paths import AppPaths


def configure_logging(paths: AppPaths) -> logging.Logger:
    paths.logs.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("bookscreenshot")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(getattr(handler, "_bookscreenshot_handler", False) for handler in logger.handlers):
        handler = RotatingFileHandler(
            paths.log_file,
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler._bookscreenshot_handler = True  # type: ignore[attr-defined]
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger
