"""Centralized logging configuration.

All entry points (CLI scripts, pipelines) should call :func:`setup_logging`
exactly once, early in ``main()``. Every module then obtains a logger via
``logging.getLogger("rat_connectome.<module>")`` and inherits the handlers
configured here: a console handler (human-readable, concise) and a
rotating file handler (verbose, persisted to ``logs/run.log``).
"""

from __future__ import annotations

import logging
import logging.config
import logging.handlers
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is a hard dependency, guarded for clarity
    yaml = None

_DEFAULT_LOGGING_CONFIG_PATH = Path("config/logging_config.yaml")
_CONFIGURED = False


def _fallback_dict_config(log_dir: Path, level: str) -> dict[str, Any]:
    """Return a minimal logging config dict if the YAML file is unavailable."""
    log_dir.mkdir(parents=True, exist_ok=True)
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"standard": {"format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": str(log_dir / "run.log"),
                "maxBytes": 5_242_880,
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "root": {"level": "DEBUG", "handlers": ["console", "file"]},
    }


def setup_logging(
    config_path: str | Path | None = None,
    log_dir: str | Path = "logs",
    level: str = "INFO",
) -> logging.Logger:
    """Configure application-wide logging exactly once.

    Parameters
    ----------
    config_path:
        Path to a ``logging_config.yaml`` (logging's ``dictConfig`` schema).
        Falls back to a sane built-in configuration if the file is
        missing or PyYAML is not installed.
    log_dir:
        Directory where ``run.log`` should be written. Created if absent.
    level:
        Console log level (e.g. "DEBUG", "INFO", "WARNING").

    Returns
    -------
    logging.Logger
        The root package logger (``rat_connectome``).
    """
    global _CONFIGURED

    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    if not _CONFIGURED:
        cfg_path = Path(config_path) if config_path else _DEFAULT_LOGGING_CONFIG_PATH
        if cfg_path.is_file() and yaml is not None:
            with cfg_path.open("r", encoding="utf-8") as fh:
                dict_config = yaml.safe_load(fh)
            # Ensure the file handler points at the requested log_dir even
            # if the YAML was authored relative to a different working dir.
            if "handlers" in dict_config and "file" in dict_config["handlers"]:
                dict_config["handlers"]["file"]["filename"] = str(log_dir_path / "run.log")
        else:
            dict_config = _fallback_dict_config(log_dir_path, level)

        logging.config.dictConfig(dict_config)
        _CONFIGURED = True

    logger = logging.getLogger("rat_connectome")
    logger.setLevel(logging.DEBUG)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced child logger, e.g. ``get_logger(__name__)``."""
    return logging.getLogger(f"rat_connectome.{name}" if not name.startswith("rat_connectome") else name)
