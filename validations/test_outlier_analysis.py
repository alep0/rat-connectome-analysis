from __future__ import annotations

import numpy as np
import pytest

from source.analysis import outlier_analysis
from source.utils.exceptions import AnalysisError


def test_multiplier_from_p_value_matches_classic_1_5_for_p_0_007():
    # B=1.5 corresponds to roughly p ~= 0.00698 under the normal approximation used.
    b = outlier_analysis.multiplier_from_p_value(0.007)
    assert b == pytest.approx(1.5, abs=0.05)


def test_multiplier_from_p_value_rejects_out_of_range():
    with pytest.raises(AnalysisError):
        outlier_analysis.multiplier_from_p_value(0.0)
    with pytest.raises(AnalysisError):
        outlier_analysis.multiplier_from_p_value(1.0)


def test_compute_iqr_bounds_shapes():
    w_3d = np.random.default_rng(0).random((5, 3, 3))
    for k in range(5):
        np.fill_diagonal(w_3d[k], 0)
    bounds = outlier_analysis.compute_iqr_bounds(w_3d, multiplier=1.5)
    assert bounds.q1.shape == (3, 3)
    assert bounds.upper_bound.shape == (3, 3)
    # Diagonal entries are always zero (self-connections removed) and
    # therefore NaN after the zero->NaN mask; only off-diagonal edges
    # have well-defined bounds.
    off_diag = ~np.eye(3, dtype=bool)
    assert np.all(bounds.upper_bound[off_diag] >= bounds.lower_bound[off_diag])


def test_flag_extreme_value_outliers_detects_injected_spike():
    rng = np.random.default_rng(1)
    w_3d = rng.uniform(1, 2, size=(10, 3, 3))
    for k in range(10):
        np.fill_diagonal(w_3d[k], 0)
    # Inject a clear outlier on edge (0,1) in repetition 0.
    w_3d[0, 0, 1] = 1000.0
    w_3d[0, 1, 0] = 1000.0

    bounds = outlier_analysis.compute_iqr_bounds(w_3d, multiplier=1.5)
    max_is_outlier, _ = outlier_analysis.flag_extreme_value_outliers(w_3d, bounds)
    assert max_is_outlier[0, 1]


def test_recompute_cv_without_outliers_reduces_cv():
    rng = np.random.default_rng(2)
    w_3d = rng.uniform(1, 1.2, size=(10, 3, 3))
    for k in range(10):
        np.fill_diagonal(w_3d[k], 0)
    w_3d[0, 0, 1] = 100.0
    w_3d[0, 1, 0] = 100.0

    w_nan = np.where(w_3d == 0, np.nan, w_3d)
    mean_before = np.nanmean(w_nan, axis=0)
    std_before = np.nanstd(w_nan, axis=0)
    cv_before = std_before[0, 1] / (mean_before[0, 1] + 1e-14)

    bounds = outlier_analysis.compute_iqr_bounds(w_3d, multiplier=1.5)
    cv_after_matrix = outlier_analysis.recompute_cv_without_outliers(w_3d, bounds)

    assert cv_after_matrix[0, 1] < cv_before
