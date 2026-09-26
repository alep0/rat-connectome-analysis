#!/usr/bin/env python3
"""Validate ``config.json`` and the expected data layout before running the pipeline.

Intended to be run in CI and locally as a fast pre-flight check, so
configuration or data-layout problems are caught in seconds rather than
after a long analysis run fails partway through.

Usage
-----
    python scripts/validate_setup.py --config config/config.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source.utils.config_loader import load_config  # noqa: E402
from source.utils.exceptions import ConfigurationError  # noqa: E402
from source.utils.logging_config import setup_logging  # noqa: E402


def validate_data_layout(config: dict, logger) -> list[str]:
    """Check that the raw-data folders referenced by config exist. Returns a list of warnings."""
    warnings: list[str] = []
    base_path = Path(config["data"]["base_path"])
    data_history = Path(config["data"]["data_history"])
    n_reps = config["data"]["n_repetitions"]
    folder_pattern = config["data"]["folder_pattern"]
    weight_pattern = config["data"]["file_pattern"]["weight"]
    distance_pattern = config["data"]["file_pattern"]["distance"]

    if not base_path.is_dir():
        warnings.append(f"Base data path does not exist: '{base_path}'. Pipeline will fail to load any rat.")
        return warnings

    for group_name, rat_ids in config["data"]["groups"].items():
        for rat_id in rat_ids:
            found_any = False
            for rep in range(1, n_reps + 1):
                folder = base_path / group_name / data_history / folder_pattern.format(rat_id=rat_id, rep=rep)
                w_file = folder / weight_pattern.format(rat_id=rat_id)
                d_file = folder / distance_pattern.format(rat_id=rat_id)
                if w_file.is_file() and d_file.is_file():
                    found_any = True
                    print(w_file)
                else:
                    logger.debug(
                        "Missing expected file(s) for group='%s' rat='%s' rep=%d.", group_name, rat_id, rep
                    )
            if not found_any:
                warnings.append(
                    f"Group '{group_name}', rat '{rat_id}': no repetition files found under '{base_path}'."
                )
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate config.json and data layout.")
    parser.add_argument("--config", default="config/config.json")
    args = parser.parse_args(argv)

    logger = setup_logging(log_dir="logs", level="INFO")
    logger.info("Validating configuration at '%s'...", args.config)

    try:
        config = load_config(args.config)
    except ConfigurationError as exc:
        logger.error("Configuration is INVALID: %s", exc)
        return 1

    logger.info("Configuration schema OK.")
    data_warnings = validate_data_layout(config, logger)
    if data_warnings:
        logger.warning("Data layout check found %d issue(s):", len(data_warnings))
        for w in data_warnings:
            logger.warning("  - %s", w)
        logger.warning("The pipeline may still run, but with fewer rats/repetitions than configured.")
    else:
        logger.info("Data layout check OK: at least one repetition found for every configured rat.")

    logger.info("Validation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
