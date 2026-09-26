from __future__ import annotations

import numpy as np
import pytest

from source.analysis import consistency_analysis
from source.utils.exceptions import AnalysisError, MatrixValidationError


def test_edge_occurrences_filters_zero_entries():
    occurrence = np.array([[0, 3], [3, 0]])
    flat = consistency_analysis.edge_occurrences(occurrence)
    assert list(flat) == [3, 3]


def test_edge_occurrences_raises_when_all_zero():
    occurrence = np.zeros((3, 3))
    with pytest.raises(MatrixValidationError):
        consistency_analysis.edge_occurrences(occurrence)


def test_survival_curve_monotonically_non_increasing():
    occurrence_flat = np.array([1, 1, 2, 3, 3, 3, 5])
    df = consistency_analysis.survival_curve(occurrence_flat, n_nodes=4, thresholds=[1, 2, 3, 4, 5])

    counts = df["n_edges_surviving"].to_numpy()
    assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))
    assert df.iloc[0]["n_edges_surviving"] == 7  # threshold=1: everything survives
    assert df.iloc[-1]["n_edges_surviving"] == 1  # threshold=5: only the single 5 survives


def test_survival_curve_density_uses_max_possible_edges():
    occurrence_flat = np.array([4, 4])
    n_nodes = 4  # max possible edges = 4*3/2 = 6
    df = consistency_analysis.survival_curve(occurrence_flat, n_nodes=n_nodes, thresholds=[4])
    assert df.iloc[0]["network_density"] == pytest.approx(2 / 6)


def test_survival_curve_rejects_too_few_nodes():
    with pytest.raises(AnalysisError):
        consistency_analysis.survival_curve(np.array([1]), n_nodes=1, thresholds=[1])
