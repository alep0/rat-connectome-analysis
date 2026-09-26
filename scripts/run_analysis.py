#!/usr/bin/env python3
"""Command-line entry point for the rat connectome analysis pipeline.

Usage
-----
    python scripts/run_analysis.py --config config/config.json
    python scripts/run_analysis.py --config config/config.json --group control
    python scripts/run_analysis.py --config config/config.json --group control --rat R01

Exit codes
----------
0
    All requested rats were analyzed successfully.
1
    Configuration error (invalid/missing config.json).
2
    One or more rats failed analysis (see logs/run.log and results/run_summary.csv).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the project root importable when this script is invoked directly
# (e.g. `python scripts/run_analysis.py`) rather than as an installed package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from source.analysis.group_pipeline import GroupAnalysisPipeline  # noqa: E402
from source.utils.config_loader import load_config  # noqa: E402
from source.utils.exceptions import ConfigurationError, RatConnectomeError  # noqa: E402
from source.utils.logging_config import setup_logging  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the rat connectome analysis pipeline.")
    parser.add_argument(
        "--config", default="config/config.json", help="Path to config.json (default: %(default)s)."
    )
    parser.add_argument(
        "--group", default=None, help="Restrict the run to a single group (default: all groups)."
    )
    parser.add_argument("--rat", default=None, help="Restrict the run to a single rat ID (requires --group).")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (default: %(default)s).",
    )
    args = parser.parse_args(argv)
    if args.rat and not args.group:
        parser.error("--rat requires --group to also be specified.")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigurationError as exc:
        # Logging may not yet be configured if config loading itself failed;
        # fall back to a plain, guaranteed-visible error message.
        print(f"[CONFIG ERROR] {exc}", file=sys.stderr)
        return 1

    logger = setup_logging(log_dir=config["logging"]["log_dir"], level=args.log_level)
    logger.info("=" * 70)
    logger.info("Rat Connectome Analysis Pipeline starting.")
    logger.info("Config: %s | Group filter: %s | Rat filter: %s", args.config, args.group, args.rat)

    if args.group:
        all_groups = config["data"]["groups"]
        if args.group not in all_groups:
            logger.error(
                "Group '%s' not found in configuration. Available groups: %s",
                args.group,
                list(all_groups.keys()),
            )
            return 1
        rat_ids = all_groups[args.group]
        if args.rat:
            if args.rat not in rat_ids:
                logger.error(
                    "Rat '%s' not found in group '%s'. Available rats: %s", args.rat, args.group, rat_ids
                )
                return 1
            rat_ids = [args.rat]
        config = {**config, "data": {**config["data"], "groups": {args.group: rat_ids}}}

    try:
        pipeline = GroupAnalysisPipeline(config)
        results = pipeline.run_all()
    except RatConnectomeError as exc:
        logger.error("Pipeline aborted: %s", exc)
        return 1
    except Exception:  # noqa: BLE001 - top-level safety net, always logged with traceback
        logger.exception("Pipeline aborted due to an unexpected error.")
        return 1

    n_failed = sum(not r.success for r in results)
    if n_failed:
        logger.warning(
            "%d/%d rats failed analysis. See results/run_summary.csv for details.", n_failed, len(results)
        )
        return 2

    logger.info("Pipeline finished successfully for all %d rat(s).", len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
