"""Simple logging utilities for the project.

Provides a ``get_logger`` function that returns a configured ``logging.Logger``.
The configuration adds a ``StreamHandler`` with a basic formatter if no handlers
are attached, which prevents "No handlers could be found" warnings during
development.
"""

import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger instance.

    If *name* is ``None`` the root logger is returned.  The function ensures
    that at least one ``StreamHandler`` is attached.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


__all__ = ["get_logger"]