from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from source.core import matrix_cleaner
from source.core.data_loader import RatRawData
from source.utils.exceptions import MatrixValidationError


def _make_raw_data(n_reps: int = 3, n_nodes: int = 5, seed: int = 0) -> RatRawData:
    rng = np.random.default_rng(seed)
    data = RatRawData(rat_id="RTEST")
    for rep in range(1, n_reps + 1):
        w = rng.random((n_nodes, n_nodes))
        w = (w + w.T) / 2
        np.fill_diagonal(w, 0)
        d = rng.random((n_nodes, n_nodes)) * 5
        data.weights[rep] = w
        data.distances[rep] = d
    return data


def test_stack_to_3d_shapes():
    data = _make_raw_data(n_reps=3, n_nodes=4)
    w_3d, d_3d = matrix_cleaner.stack_to_3d(data)
    assert w_3d.shape == (3, 4, 4)
    assert d_3d.shape == (3, 4, 4)


def test_stack_to_3d_raises_on_empty():
    data = RatRawData(rat_id="EMPTY")
    with pytest.raises(MatrixValidationError):
        matrix_cleaner.stack_to_3d(data)


def test_report_nan_positions_detects_nans():
    data = _make_raw_data(n_reps=2, n_nodes=3)
    w_3d, d_3d = matrix_cleaner.stack_to_3d(data)
    w_3d[0, 1, 2] = np.nan

    report = matrix_cleaner.report_nan_positions(w_3d, d_3d)

    assert isinstance(report, pd.DataFrame)
    assert len(report) == 1
    assert report.iloc[0]["repetition"] == 1


def test_clean_nans_fills_with_zero():
    w_3d = np.array([[[0.0, np.nan], [1.0, 0.0]]])
    d_3d = np.array([[[0.0, 2.0], [1.0, 0.0]]])
    w_clean, d_clean = matrix_cleaner.clean_nans(w_3d, d_3d)
    assert not np.isnan(w_clean).any()
    assert not np.isnan(d_clean).any()
    assert w_clean[0, 0, 1] == 0.0


def test_find_disconnected_nodes():
    w_mean = np.array(
        [
            [0.0, 0.5, 0.0],
            [0.5, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ]
    )
    disconnected = matrix_cleaner.find_disconnected_nodes(w_mean)
    assert list(disconnected) == [2]


def test_remove_nodes_reduces_shape():
    data = _make_raw_data(n_reps=2, n_nodes=5)
    w_3d, d_3d = matrix_cleaner.stack_to_3d(data)
    w_clean, d_clean = matrix_cleaner.remove_nodes(w_3d, d_3d, [0, 4])
    assert w_clean.shape == (2, 3, 3)
    assert d_clean.shape == (2, 3, 3)


def test_remove_nodes_rejects_out_of_bounds():
    data = _make_raw_data(n_reps=2, n_nodes=3)
    w_3d, d_3d = matrix_cleaner.stack_to_3d(data)
    with pytest.raises(MatrixValidationError):
        matrix_cleaner.remove_nodes(w_3d, d_3d, [10])


def test_full_cleaning_pipeline_end_to_end():
    data = _make_raw_data(n_reps=3, n_nodes=6)
    w_clean, d_clean, nan_report = matrix_cleaner.full_cleaning_pipeline(data, fictitious_nodes=[0, 1])
    assert w_clean.shape == (3, 4, 4)
    assert isinstance(nan_report, pd.DataFrame)
