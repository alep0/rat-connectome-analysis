"""Outlier detection via Tukey's IQR fences, and its effect on CV.

Mirrors notebook section 6: per-edge Q1/Q3/IQR computed across
repetitions, Tukey fences with a configurable multiplier ``B`` (or a
multiplier derived from a target p-value assuming approximate
normality), classification of extreme values, and re-computation of CV
after removing flagged outliers.
"""

from __future__ import annotations

import logging
import warnings
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm

from source.utils.exceptions import AnalysisError

logger = logging.getLogger("rat_connectome.analysis.outliers")

_EPSILON = 1e-14


@dataclass
class IqrBounds:
    q1: np.ndarray
    q3: np.ndarray
    iqr: np.ndarray
    lower_bound: np.ndarray
    upper_bound: np.ndarray


def multiplier_from_p_value(p_value: float) -> float:
    """Convert a two-sided normal-tail p-value into an equivalent Tukey IQR multiplier ``B``.

    Uses the classic approximation relating the normal distribution's
    z-score to Tukey's fence multiplier (``B = (z - 0.6745) / 1.349``),
    so a stricter ``p_value`` yields a larger, more permissive ``B``.
    """
    if not (0 < p_value < 1):
        raise AnalysisError(f"p_value must be in (0, 1), got {p_value}.")
    z_score = norm.ppf(1 - p_value / 2)
    return (z_score - 0.6745) / 1.349


def compute_iqr_bounds(w_3d: np.ndarray, multiplier: float) -> IqrBounds:
    """Compute per-edge Tukey fences from the (zero-as-NaN) repetition tensor."""
    w_nan = np.where(w_3d == 0, np.nan, w_3d)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        q1 = np.nanpercentile(w_nan, 25, axis=0)
        q3 = np.nanpercentile(w_nan, 75, axis=0)
    iqr = q3 - q1
    return IqrBounds(
        q1=q1,
        q3=q3,
        iqr=iqr,
        lower_bound=q1 - multiplier * iqr,
        upper_bound=q3 + multiplier * iqr,
    )


def flag_extreme_value_outliers(w_3d: np.ndarray, bounds: IqrBounds) -> tuple[np.ndarray, np.ndarray]:
    """Flag, per edge, whether its observed maximum/minimum exceeds the Tukey fences."""
    w_nan = np.where(w_3d == 0, np.nan, w_3d)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        w_max = np.nanmax(w_nan, axis=0)
        w_min = np.nanmin(w_nan, axis=0)
    max_is_outlier = w_max > bounds.upper_bound
    min_is_outlier = w_min < bounds.lower_bound
    return max_is_outlier, min_is_outlier


def outlier_summary_table(
    cv_matrix: np.ndarray,
    occurrence: np.ndarray,
    mean_weight: np.ndarray,
    std_weight: np.ndarray,
    w_3d: np.ndarray,
    bounds: IqrBounds,
) -> pd.DataFrame:
    """Per-edge table combining CV, occurrence, weight stats and outlier flags."""
    mask = occurrence > 0
    i_idx, j_idx = np.where(mask)

    max_is_outlier, min_is_outlier = flag_extreme_value_outliers(w_3d, bounds)
    w_nan = np.where(w_3d == 0, np.nan, w_3d)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        w_max = np.nanmax(w_nan, axis=0)
        w_min = np.nanmin(w_nan, axis=0)

    df = pd.DataFrame(
        {
            "source_roi": i_idx,
            "target_roi": j_idx,
            "cv": cv_matrix[mask],
            "occurrence": occurrence[mask],
            "mean_weight": np.round(mean_weight[mask], 3),
            "std_weight": np.round(std_weight[mask], 3),
            "max_weight": np.round(w_max[mask], 3),
            "min_weight": np.round(w_min[mask], 3),
            "max_is_outlier": max_is_outlier[mask],
            "min_is_outlier": min_is_outlier[mask],
        }
    )
    return df.sort_values(by="cv", ascending=False).reset_index(drop=True)


def recompute_cv_without_outliers(w_3d: np.ndarray, bounds: IqrBounds) -> np.ndarray:
    """Recompute the per-edge CV matrix after masking out values outside the Tukey fences."""
    w_nan = np.where(w_3d == 0, np.nan, w_3d)
    outlier_mask = (w_nan > bounds.upper_bound) | (w_nan < bounds.lower_bound)
    w_clean = w_nan.copy()
    w_clean[outlier_mask] = np.nan

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        clean_mean = np.nanmean(w_clean, axis=0)
        clean_std = np.nanstd(w_clean, axis=0)

    return clean_std / (clean_mean + _EPSILON)


def cv_distribution_across_multipliers(
    w_3d: np.ndarray,
    cv_flat_baseline: np.ndarray,
    occurrence_mask: np.ndarray,
    min_occurrence_mask: np.ndarray,
    multipliers: Sequence[float],
) -> dict[str, np.ndarray]:
    """Compute, for each IQR multiplier, the 1D CV distribution of the "reliable" edges.

    Mirrors notebook section 6.3: only edges passing both
    ``occurrence_mask`` (>0 occurrences, matches the CV matrix flattening)
    and ``min_occurrence_mask`` (e.g. >= 9 occurrences) are retained, so
    that all curves share the same edge population and are directly
    comparable.
    """
    result: dict[str, np.ndarray] = {
        "original": cv_flat_baseline[min_occurrence_mask],
    }

    w_nan = np.where(w_3d == 0, np.nan, w_3d)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        q1 = np.nanpercentile(w_nan, 25, axis=0)
        q3 = np.nanpercentile(w_nan, 75, axis=0)
        iqr = q3 - q1

        for m in multipliers:
            lower = q1 - m * iqr
            upper = q3 + m * iqr
            w_filtered = w_nan.copy()
            outlier_mask = (w_filtered > upper) | (w_filtered < lower)
            w_filtered[outlier_mask] = np.nan

            mean_clean = np.nanmean(w_filtered, axis=0)
            std_clean = np.nanstd(w_filtered, axis=0)
            cv_clean = std_clean / (mean_clean + _EPSILON)

            cv_flat = cv_clean[occurrence_mask][min_occurrence_mask]
            result[f"iqr_x{m}"] = np.nan_to_num(cv_flat, nan=0.0)

    logger.info("Computed CV distributions for %d IQR multipliers.", len(multipliers))
    return result
