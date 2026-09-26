from __future__ import annotations

import numpy as np
import pytest

from source.analysis import cv_analysis
from source.utils.exceptions import AnalysisError


def test_compute_cv_basic():
    mean_w = np.array([[0, 2.0], [2.0, 0]])
    std_w = np.array([[0, 1.0], [1.0, 0]])
    occurrence = np.array([[0, 3], [3, 0]])
    cv = cv_analysis.compute_cv(mean_w, std_w, occurrence)
    assert cv[0, 1] == pytest.approx(0.5)


def test_compute_cv_forces_zero_for_single_occurrence():
    mean_w = np.array([[0, 5.0], [5.0, 0]])
    std_w = np.array([[0, 0.0], [0.0, 0]])
    occurrence = np.array([[0, 1], [1, 0]])
    cv = cv_analysis.compute_cv(mean_w, std_w, occurrence)
    assert cv[0, 1] == 0.0


def test_cv_edge_table_sorted_descending():
    n = 3
    cv_matrix = np.array([[0, 0.9, 0.1], [0.9, 0, 0.5], [0.1, 0.5, 0]])
    occurrence = np.array([[0, 2, 2], [2, 0, 2], [2, 2, 0]])
    mean_w = np.ones((n, n))
    w_3d = np.ones((2, n, n))

    df = cv_analysis.cv_edge_table(cv_matrix, occurrence, mean_w, w_3d)

    assert list(df["cv"])[:1] == [0.9]
    assert df["cv"].is_monotonic_decreasing


def test_cv_survival_curve_shape_and_monotonic_increase():
    # As the *maximum allowed* CV threshold increases, more edges qualify,
    # so the retained percentage is non-decreasing.
    cv_flat = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    df = cv_analysis.cv_survival_curve(cv_flat, n_points=10)
    pct = df["pct_of_edges"].to_numpy()
    assert all(pct[i] <= pct[i + 1] for i in range(len(pct) - 1))
    assert pct[0] > 0
    assert pct[-1] <= 100.0


def test_cv_survival_curve_raises_on_empty():
    with pytest.raises(AnalysisError):
        cv_analysis.cv_survival_curve(np.array([]))


def test_cv_vs_metadata_excludes_single_occurrence_edges():
    cv_matrix = np.array([[0, 0.5], [0.5, 0]])
    occurrence = np.array([[0, 1], [1, 0]])
    mean_w = np.array([[0, 2.0], [2.0, 0]])
    mean_d = np.array([[0, 3.0], [3.0, 0]])
    df = cv_analysis.cv_vs_metadata(cv_matrix, occurrence, mean_w, mean_d, n_repetitions=4)
    assert df.empty
