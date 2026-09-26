"""Shared pytest fixtures for the validations test suite.

Tests use small synthetic matrices (never the real dataset, which is
not shipped with the repository) so they run fast, deterministically,
and without any external data dependency -- suitable for CI.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture()
def rng() -> np.random.Generator:
    return np.random.default_rng(seed=42)


@pytest.fixture()
def small_weight_matrix(rng: np.random.Generator) -> np.ndarray:
    """A small, symmetric, non-negative 6x6 synthetic weight matrix."""
    n = 6
    m = rng.random((n, n))
    m = (m + m.T) / 2
    np.fill_diagonal(m, 0)
    m[m < 0.3] = 0.0  # sparsify, like a real connectome
    return m


@pytest.fixture()
def synthetic_rat_dataset(tmp_path: Path) -> tuple[Path, str, int]:
    """Create a small on-disk dataset for one synthetic rat with 4 repetitions.

    Returns (base_path, rat_id, n_repetitions).
    """
    rat_id = "R99"
    n_reps = 4
    n_nodes = 5
    base_path = tmp_path / "raw"
    rng = np.random.default_rng(123)

    for rep in range(1, n_reps + 1):
        folder = base_path / f"{rat_id}_r{rep}"
        folder.mkdir(parents=True, exist_ok=True)
        w = rng.random((n_nodes, n_nodes))
        w = (w + w.T) / 2
        np.fill_diagonal(w, 0)
        d = rng.random((n_nodes, n_nodes)) * 10
        d = (d + d.T) / 2
        np.fill_diagonal(d, 0)
        np.savetxt(folder / f"th-0.0_{rat_id}_w.txt", w)
        np.savetxt(folder / f"th-0.0_{rat_id}_d.txt", d)

    yield base_path, rat_id, n_reps
    shutil.rmtree(tmp_path, ignore_errors=True)
