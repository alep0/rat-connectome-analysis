from __future__ import annotations

import numpy as np
import pytest

from source.core.consensus_builder import build_consensus, compute_occurrence
from source.utils.exceptions import MatrixValidationError


def test_compute_occurrence_counts_nonzero_edges():
    w_3d = np.array(
        [
            [[0, 1], [1, 0]],
            [[0, 0], [0, 0]],
            [[0, 2], [2, 0]],
        ]
    )
    occurrence = compute_occurrence(w_3d)
    assert occurrence[0, 1] == 2
    assert occurrence[1, 0] == 2


def test_build_consensus_ignores_zero_edges_in_mean():
    # Edge (0,1) has values [2.0, 0.0, 4.0] -> mean over non-zero = 3.0
    w_3d = np.array(
        [
            [[0, 2], [2, 0]],
            [[0, 0], [0, 0]],
            [[0, 4], [4, 0]],
        ],
        dtype=float,
    )
    d_3d = np.zeros_like(w_3d)

    result = build_consensus(w_3d, d_3d)

    assert result.mean_weight[0, 1] == pytest.approx(3.0)
    assert result.occurrence[0, 1] == 2


def test_build_consensus_handles_never_observed_edge():
    w_3d = np.zeros((2, 2, 2))
    d_3d = np.zeros((2, 2, 2))
    result = build_consensus(w_3d, d_3d)
    assert result.mean_weight[0, 1] == 0.0
    assert result.occurrence[0, 1] == 0


def test_build_consensus_rejects_empty_input():
    with pytest.raises(MatrixValidationError):
        build_consensus(np.empty((0, 0, 0)), np.empty((0, 0, 0)))
