"""Load and validate the project's JSON configuration file.

The configuration drives every stage of the pipeline (which rats/groups
to analyze, preprocessing rules, analysis thresholds and output
locations), so it is validated eagerly and loudly: a malformed
``config.json`` should fail fast with a clear message rather than cause
a confusing ``KeyError`` deep inside an analysis routine.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from source.utils.exceptions import ConfigurationError

logger = logging.getLogger("rat_connectome.utils.config_loader")

# Keys that must exist for the pipeline to run at all. Nested keys are
# expressed as dotted paths and checked with `_get_nested`.
_REQUIRED_KEYS = (
    "data.base_path",
    "data.groups",
    "data.n_repetitions",
    "data.folder_pattern",
    "data.file_pattern.weight",
    "data.file_pattern.distance",
    "preprocessing.fictitious_nodes",
    "analysis.occurrence_thresholds",
    "analysis.cv_threshold",
    "output.results_dir",
    "logging.log_dir",
)


def _get_nested(config: dict[str, Any], dotted_key: str) -> Any:
    node: Any = config
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise ConfigurationError(f"Missing required configuration key: '{dotted_key}'")
        node = node[part]
    return node


def validate_config(config: dict[str, Any]) -> None:
    """Validate that ``config`` contains every key the pipeline relies on.

    Raises
    ------
    ConfigurationError
        If a required key is missing or a value is of the wrong type/shape.
    """
    for key in _REQUIRED_KEYS:
        _get_nested(config, key)

    groups = config["data"]["groups"]
    if not isinstance(groups, dict) or len(groups) == 0:
        raise ConfigurationError("'data.groups' must be a non-empty mapping of group_name -> [rat_ids].")
    for group_name, rat_ids in groups.items():
        if not isinstance(rat_ids, list) or len(rat_ids) == 0:
            raise ConfigurationError(f"Group '{group_name}' must map to a non-empty list of rat IDs.")

    n_reps = config["data"]["n_repetitions"]
    if not isinstance(n_reps, int) or n_reps < 1:
        raise ConfigurationError("'data.n_repetitions' must be a positive integer.")

    thresholds = config["analysis"]["occurrence_thresholds"]
    if not isinstance(thresholds, list) or len(thresholds) == 0:
        raise ConfigurationError("'analysis.occurrence_thresholds' must be a non-empty list.")

    cv_threshold = config["analysis"]["cv_threshold"]
    if not isinstance(cv_threshold, (int, float)) or cv_threshold <= 0:
        raise ConfigurationError("'analysis.cv_threshold' must be a positive number.")

    logger.debug("Configuration validated successfully (%d groups found).", len(groups))


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load, parse and validate the JSON configuration file.

    Parameters
    ----------
    config_path:
        Path to a ``config.json`` file.

    Returns
    -------
    dict
        The parsed and validated configuration.

    Raises
    ------
    ConfigurationError
        If the file is missing, is not valid JSON, or fails validation.
    """
    path = Path(config_path)
    if not path.is_file():
        raise ConfigurationError(f"Configuration file not found: '{path}'")

    try:
        with path.open("r", encoding="utf-8") as fh:
            config = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Configuration file '{path}' is not valid JSON: {exc}") from exc

    validate_config(config)
    logger.info("Loaded configuration from '%s'.", path)
    return config
