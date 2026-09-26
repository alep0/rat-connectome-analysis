from __future__ import annotations

from pathlib import Path

import pandas as pd

from source.analysis.group_pipeline import GroupAnalysisPipeline


def _build_config(base_path: Path, results_dir: Path, rat_id: str, n_reps: int) -> dict:
    return {
        "data": {
            "base_path": str(base_path),
            "groups": {"synthetic_group": [rat_id]},
            "n_repetitions": n_reps,
            "folder_pattern": "{rat_id}_r{rep}",
            "file_pattern": {"weight": "th-0.0_{rat_id}_w.txt", "distance": "th-0.0_{rat_id}_d.txt"},
        },
        "preprocessing": {"remove_self_connections": True, "fictitious_nodes": []},
        "analysis": {
            "occurrence_thresholds": [1, 2, 3],
            "min_occurrence_for_consistency": 2,
            "cv_threshold": 0.2,
            "outlier": {"iqr_multipliers": [3.0, 1.5], "p_value_for_adaptive_multiplier": 0.01},
        },
        "output": {
            "results_dir": str(results_dir),
            "figures_subdir": "figures",
            "tables_subdir": "tables",
            "consensus_subdir": "consensus",
            "save_figures": True,
            "figure_dpi": 72,
        },
        "logging": {"log_dir": str(results_dir / "logs"), "log_file": "run.log"},
    }


def test_group_pipeline_end_to_end(synthetic_rat_dataset, tmp_path):
    base_path, rat_id, n_reps = synthetic_rat_dataset
    results_dir = tmp_path / "results"
    config = _build_config(base_path, results_dir, rat_id, n_reps)

    pipeline = GroupAnalysisPipeline(config)
    results = pipeline.run_all()

    assert len(results) == 1
    result = results[0]
    assert result.success, result.error
    assert result.n_repetitions_loaded == n_reps
    assert result.n_nodes == 5

    summary_path = results_dir / "run_summary.csv"
    assert summary_path.is_file()
    summary = pd.read_csv(summary_path)
    assert summary.loc[0, "success"] == True  # noqa: E712

    consensus_dir = results_dir / "consensus" / "synthetic_group" / rat_id
    assert (consensus_dir / "mean_weight.txt").is_file()

    figures_dir = results_dir / "figures" / "synthetic_group" / rat_id
    assert (figures_dir / "weight_heatmap_topology.png").is_file()


def test_group_pipeline_continues_after_one_rat_fails(synthetic_rat_dataset, tmp_path):
    base_path, rat_id, n_reps = synthetic_rat_dataset
    results_dir = tmp_path / "results"
    config = _build_config(base_path, results_dir, rat_id, n_reps)
    # Add a second, nonexistent rat: its failure must not prevent rat_id from succeeding.
    config["data"]["groups"]["synthetic_group"].append("R_DOES_NOT_EXIST")

    pipeline = GroupAnalysisPipeline(config)
    results = pipeline.run_all()

    by_id = {r.rat_id: r for r in results}
    assert by_id[rat_id].success is True
    assert by_id["R_DOES_NOT_EXIST"].success is False
    assert by_id["R_DOES_NOT_EXIST"].error is not None
