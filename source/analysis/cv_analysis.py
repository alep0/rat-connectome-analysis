"""Coefficient of Variation (CV) analysis of edge weights across repetitions.

Mirrors notebook section 5: CV = std / mean per edge, its relationship
with occurrence count and physical distance, its distribution, and a
survival curve for a *maximum* allowed CV.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from source.utils.exceptions import AnalysisError

logger = logging.getLogger("rat_connectome.analysis.cv")

_EPSILON = 1e-14


def compute_cv(mean_weight: np.ndarray, std_weight: np.ndarray, occurrence: np.ndarray) -> np.ndarray:
    """Compute the per-edge coefficient of variation matrix.

    Edges observed in exactly one repetition have an undefined
    (population) CV in the original analysis; they are set to 0.0
    rather than left as NaN/inf so downstream masking/statistics stay
    well-behaved, matching the notebook's convention.
    """
    cv = std_weight / (mean_weight + _EPSILON)
    single_occurrence_mask = occurrence == 1
    cv = np.where(single_occurrence_mask, 0.0, cv)
    return cv


def cv_edge_table(
    cv_matrix: np.ndarray,
    occurrence: np.ndarray,
    mean_weight: np.ndarray,
    w_3d: np.ndarray,
) -> pd.DataFrame:
    """Build a per-edge table of CV, occurrence, and the raw observed weight values.

    Only edges observed at least once are included, ranked by
    descending CV (the edges most likely to need scrutiny appear
    first).
    """
    mask = occurrence > 0
    i_idx, j_idx = np.where(mask)
    weight_lists = [
        np.round(w_3d[:, i, j][w_3d[:, i, j] > 0], 4).tolist() for i, j in zip(i_idx, j_idx, strict=False)
    ]
    df = pd.DataFrame(
        {
            "source_roi": i_idx,
            "target_roi": j_idx,
            "cv": cv_matrix[mask],
            "occurrence": occurrence[mask],
            "mean_weight": mean_weight[mask],
            "observed_weights": weight_lists,
        }
    )
    return df.sort_values(by="cv", ascending=False).reset_index(drop=True)


def cv_survival_curve(
    cv_flat: np.ndarray, n_points: int = 1000, percentile_cap: float = 95.0
) -> pd.DataFrame:
    """Compute the fraction of edges retained as the *maximum allowed* CV threshold varies.

    Unlike the occurrence survival curve (higher threshold = stricter),
    here lower CV thresholds are stricter (retain only the most
    reproducible edges).
    """
    if cv_flat.size == 0:
        raise AnalysisError("cv_flat is empty; cannot build a CV survival curve.")

    max_val = np.percentile(cv_flat, percentile_cap)
    thresholds = np.linspace(np.min(cv_flat), max_val, n_points)
    total_edges = len(cv_flat)

    n_surviving = np.array([np.sum(cv_flat <= t) for t in thresholds])
    df = pd.DataFrame(
        {
            "cv_threshold": thresholds,
            "n_edges_surviving": n_surviving,
            "pct_of_edges": 100.0 * n_surviving / total_edges,
        }
    )
    logger.info(
        "Computed CV survival curve over %d thresholds up to the %.0fth percentile.", n_points, percentile_cap
    )
    return df


def cv_vs_metadata(
    cv_matrix: np.ndarray,
    occurrence: np.ndarray,
    mean_weight: np.ndarray,
    mean_distance: np.ndarray,
    n_repetitions: int,
) -> pd.DataFrame:
    """Tidy per-edge table combining CV, weight, distance and consistency (for scatter/violin plots)."""
    mask = occurrence > 1  # CV undefined/forced-zero for single-occurrence edges
    return pd.DataFrame(
        {
            "occurrence": occurrence[mask],
            "pct_occurrence": 100.0 * occurrence[mask] / n_repetitions,
            "cv": cv_matrix[mask],
            "weight": mean_weight[mask],
            "distance": mean_distance[mask],
        }
    )
