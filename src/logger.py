"""Lightweight logging helpers used across the project.

Provides a minimal, typed interface for getting and configuring loggers.
"""

from __future__ import annotations

import logging


def configure_logging(level: int | str = "INFO") -> None:
    """Configure basic logging for the application.

    Accepts either a logging level int or a case-insensitive string name.
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a module-level logger.

    If name is None, returns the root logger.
    """
    return logging.getLogger(name)
