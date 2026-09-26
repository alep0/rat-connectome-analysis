"""Group-level orchestration pipeline.

Runs the full per-rat analysis (data loading -> cleaning -> consensus
-> consistency/CV/outlier analyses -> figures/tables) for every rat in
every configured experimental group, and produces a group-level summary.

This is the generalized, multi-rat, multi-group replacement for the
original notebook, which only ever processed one hard-coded rat.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # headless backend: required for Docker/CI, no display available

import numpy as np
import pandas as pd

from source.analysis import consistency_analysis, cv_analysis, outlier_analysis
from source.core import consensus_builder, matrix_cleaner
from source.core.data_loader import ConnectomeDataLoader
from source.utils import plotting
from source.utils.exceptions import RatConnectomeError

logger = logging.getLogger("rat_connectome.analysis.group_pipeline")


@dataclass
class RatAnalysisResult:
    """Outcome of running the pipeline for a single rat."""

    rat_id: str
    group: str
    success: bool
    n_nodes: int | None = None
    n_repetitions_loaded: int | None = None
    error: str | None = None
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)


class GroupAnalysisPipeline:
    """Runs the connectome analysis pipeline across groups and rats."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        data_cfg = config["data"]
        self.loader = ConnectomeDataLoader(
            base_path=data_cfg["base_path"],
            data_history=data_cfg["data_history"],
            folder_pattern=data_cfg["folder_pattern"],
            weight_file_pattern=data_cfg["file_pattern"]["weight"],
            distance_file_pattern=data_cfg["file_pattern"]["distance"],
            n_repetitions=data_cfg["n_repetitions"],
            )
        self.results_dir = Path(config["output"]["results_dir"])
        self.figures_dir = self.results_dir / config["output"].get("figures_subdir", "figures")
        self.tables_dir = self.results_dir / config["output"].get("tables_subdir", "tables")
        self.consensus_dir = self.results_dir / config["output"].get("consensus_subdir", "consensus")
        self.dpi = config["output"].get("figure_dpi", 300)
        self.save_figures = config["output"].get("save_figures", True)
        plotting.apply_default_style()

    def run_all(self) -> list[RatAnalysisResult]:
        """Run the pipeline for every rat in every group defined in the configuration."""
        results: list[RatAnalysisResult] = []
        groups: dict[str, list[str]] = self.config["data"]["groups"]

        logger.info("Starting analysis for %d group(s): %s", len(groups), list(groups.keys()))
        for group_name, rat_ids in groups.items():
            logger.info("=== Group '%s': %d rat(s) ===", group_name, len(rat_ids))
            for rat_id in rat_ids:
                results.append(self.run_single_rat(group_name, rat_id))

        n_ok = sum(r.success for r in results)
        logger.info("Pipeline finished: %d/%d rats analyzed successfully.", n_ok, len(results))
        self._write_run_summary(results)
        return results

    def run_single_rat(self, group_name: str, rat_id: str) -> RatAnalysisResult:
        """Run the complete analysis chain for one rat; never raises, always returns a result."""
        try:
            return self._run_single_rat_unsafe(group_name, rat_id)
        except RatConnectomeError as exc:
            logger.error("Rat '%s' (group '%s') failed: %s", rat_id, group_name, exc)
            return RatAnalysisResult(rat_id=rat_id, group=group_name, success=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001 - guard rail so one rat cannot crash the whole batch
            logger.exception("Unexpected error analyzing rat '%s' (group '%s').", rat_id, group_name)
            return RatAnalysisResult(
                rat_id=rat_id, group=group_name, success=False, error=f"Unexpected error: {exc}"
            )

    def _run_single_rat_unsafe(self, group_name: str, rat_id: str) -> RatAnalysisResult:
        pre_cfg = self.config["preprocessing"]
        analysis_cfg = self.config["analysis"]

        raw = self.loader.load_rat(
            group_name, rat_id, remove_self_connections=pre_cfg.get("remove_self_connections", True)
            )
        w_3d, d_3d, nan_report = matrix_cleaner.full_cleaning_pipeline(
            raw, pre_cfg.get("fictitious_nodes", [])
        )

        n_nodes = w_3d.shape[1]
        consensus = consensus_builder.build_consensus(w_3d, d_3d)

        occurrence_flat = consistency_analysis.edge_occurrences(consensus.occurrence)
        df_survival = consistency_analysis.survival_curve(
            occurrence_flat, n_nodes=n_nodes, thresholds=analysis_cfg["occurrence_thresholds"]
        )

        cv_matrix = cv_analysis.compute_cv(consensus.mean_weight, consensus.std_weight, consensus.occurrence)
        df_cv_edges = cv_analysis.cv_edge_table(cv_matrix, consensus.occurrence, consensus.mean_weight, w_3d)
        df_cv_meta = cv_analysis.cv_vs_metadata(
            cv_matrix,
            consensus.occurrence,
            consensus.mean_weight,
            consensus.mean_distance,
            n_repetitions=w_3d.shape[0],
        )
        cv_flat_gt1 = df_cv_meta["cv"].to_numpy()
        df_cv_survival = cv_analysis.cv_survival_curve(cv_flat_gt1) if cv_flat_gt1.size else pd.DataFrame()

        outlier_cfg = analysis_cfg["outlier"]
        bounds = outlier_analysis.compute_iqr_bounds(w_3d, multiplier=outlier_cfg["iqr_multipliers"][-1])
        df_outliers = outlier_analysis.outlier_summary_table(
            cv_matrix, consensus.occurrence, consensus.mean_weight, consensus.std_weight, w_3d, bounds
        )

        min_occurrence = analysis_cfg.get("min_occurrence_for_consistency", 9)
        occurrence_mask = consensus.occurrence > 0
        min_occurrence_mask = consensus.occurrence[occurrence_mask] >= min_occurrence
        cv_flat_baseline = cv_matrix[occurrence_mask]
        cv_dist_dict = outlier_analysis.cv_distribution_across_multipliers(
            w_3d, cv_flat_baseline, occurrence_mask, min_occurrence_mask, outlier_cfg["iqr_multipliers"]
        )

        tables = {
            "nan_report": nan_report,
            "survival_curve": df_survival,
            "cv_edges": df_cv_edges,
            "cv_survival_curve": df_cv_survival,
            "outliers": df_outliers,
        }
        self._save_tables(group_name, rat_id, tables)
        self._save_consensus(group_name, rat_id, consensus)
        if self.save_figures:
            self._save_figures(
                group_name,
                rat_id,
                consensus,
                occurrence_flat,
                df_survival,
                df_cv_meta,
                cv_flat_gt1,
                df_cv_survival,
                cv_dist_dict,
                df_outliers,
                n_nodes,
            )

        logger.info(
            "Rat '%s' (group '%s'): analysis complete (%d nodes, %d/%d repetitions loaded).",
            rat_id,
            group_name,
            n_nodes,
            raw.n_loaded,
            self.loader.n_repetitions,
        )
        return RatAnalysisResult(
            rat_id=rat_id,
            group=group_name,
            success=True,
            n_nodes=n_nodes,
            n_repetitions_loaded=raw.n_loaded,
            tables=tables,
        )

    def _save_tables(self, group_name: str, rat_id: str, tables: dict[str, pd.DataFrame]) -> None:
        out_dir = self.tables_dir / group_name / rat_id
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, df in tables.items():
            if df is None or df.empty:
                continue
            df.to_csv(out_dir / f"{name}.csv", index=False)
        logger.debug("Saved %d tables for rat '%s' to '%s'.", len(tables), rat_id, out_dir)

    def _save_consensus(
        self, group_name: str, rat_id: str, consensus: consensus_builder.ConsensusResult
    ) -> None:
        out_dir = self.consensus_dir / group_name / rat_id
        out_dir.mkdir(parents=True, exist_ok=True)
        np.savetxt(out_dir / "mean_weight.txt", consensus.mean_weight)
        np.savetxt(out_dir / "std_weight.txt", consensus.std_weight)
        np.savetxt(out_dir / "mean_distance.txt", consensus.mean_distance)
        np.savetxt(out_dir / "occurrence.txt", consensus.occurrence, fmt="%d")
        logger.debug("Saved consensus matrices for rat '%s' to '%s'.", rat_id, out_dir)

    def _save_figures(
        self,
        group_name,
        rat_id,
        consensus,
        occurrence_flat,
        df_survival,
        df_cv_meta,
        cv_flat_gt1,
        df_cv_survival,
        cv_dist_dict,
        df_outliers,
        n_nodes,
    ) -> None:
        out_dir = self.figures_dir / group_name / rat_id
        n_reps = self.loader.n_repetitions
        plotting.plot_weight_heatmap_and_topology(
            consensus.mean_weight, out_dir / "weight_heatmap_topology.png", self.dpi
        )
        plotting.plot_occurrence_histogram(
            occurrence_flat, n_reps, out_dir / "occurrence_histogram.png", self.dpi
        )
        if not df_survival.empty:
            plotting.plot_survival_curve(df_survival, out_dir / "occurrence_survival_curve.png", self.dpi)
        if not df_cv_meta.empty:
            plotting.plot_cv_scatter(df_cv_meta, out_dir / "cv_weight_distance_scatter.png", self.dpi)
        if cv_flat_gt1.size:
            plotting.plot_cv_distribution(cv_flat_gt1, out_dir / "cv_distribution.png", dpi=self.dpi)
        if not df_cv_survival.empty:
            plotting.plot_cv_survival_curve(df_cv_survival, out_dir / "cv_survival_curve.png", self.dpi)
        if cv_dist_dict:
            plotting.plot_cv_comparison_across_multipliers(
                cv_dist_dict, out_dir / "cv_outlier_removal_comparison.png", dpi=self.dpi
            )
        if not df_outliers.empty:
            plotting.plot_outlier_map(
                n_nodes,
                df_outliers["source_roi"].to_numpy(),
                df_outliers["target_roi"].to_numpy(),
                df_outliers["max_is_outlier"].to_numpy(),
                df_outliers["min_is_outlier"].to_numpy(),
                out_dir / "spatial_outlier_map.png",
                self.dpi,
            )
        logger.debug("Saved figures for rat '%s' to '%s'.", rat_id, out_dir)

    def _write_run_summary(self, results: list[RatAnalysisResult]) -> None:
        rows = [
            {
                "group": r.group,
                "rat_id": r.rat_id,
                "success": r.success,
                "n_nodes": r.n_nodes,
                "n_repetitions_loaded": r.n_repetitions_loaded,
                "error": r.error,
            }
            for r in results
        ]
        summary_df = pd.DataFrame(rows)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        summary_path = self.results_dir / "run_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        logger.info("Run summary written to '%s'.", summary_path)
