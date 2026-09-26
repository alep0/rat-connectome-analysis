from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from source.core.data_loader import ConnectomeDataLoader
from source.utils.exceptions import DataLoadError


def _make_loader(base_path: Path, n_reps: int) -> ConnectomeDataLoader:
    return ConnectomeDataLoader(
        base_path=base_path,
        folder_pattern="{rat_id}_r{rep}",
        weight_file_pattern="th-0.0_{rat_id}_w.txt",
        distance_file_pattern="th-0.0_{rat_id}_d.txt",
        n_repetitions=n_reps,
    )


def test_load_rat_success(synthetic_rat_dataset):
    base_path, rat_id, n_reps = synthetic_rat_dataset
    loader = _make_loader(base_path, n_reps)

    data = loader.load_rat(rat_id)

    assert data.rat_id == rat_id
    assert data.n_loaded == n_reps
    assert data.missing_repetitions == []
    for rep in range(1, n_reps + 1):
        assert rep in data.weights
        assert rep in data.distances
        assert data.weights[rep].shape == data.distances[rep].shape


def test_load_rat_removes_self_connections(synthetic_rat_dataset):
    base_path, rat_id, n_reps = synthetic_rat_dataset
    loader = _make_loader(base_path, n_reps)

    data = loader.load_rat(rat_id, remove_self_connections=True)

    for w in data.weights.values():
        assert np.all(np.diag(w) == 0)


def test_load_rat_handles_missing_repetition(synthetic_rat_dataset, tmp_path):
    base_path, rat_id, n_reps = synthetic_rat_dataset
    # Delete one repetition's files to simulate a missing acquisition.
    missing_folder = base_path / f"{rat_id}_r2"
    for f in missing_folder.iterdir():
        f.unlink()

    loader = _make_loader(base_path, n_reps)
    data = loader.load_rat(rat_id)

    assert 2 in data.missing_repetitions
    assert data.n_loaded == n_reps - 1


def test_load_rat_raises_when_no_repetitions_found(tmp_path):
    loader = _make_loader(tmp_path / "does_not_exist", n_reps=3)
    with pytest.raises(DataLoadError):
        loader.load_rat("R00")
