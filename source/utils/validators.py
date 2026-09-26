"""Reusable validation helpers for matrices and analysis inputs.

Keeping validation logic in one place avoids scattering ad-hoc
``assert`` statements throughout the analysis code and gives consistent,
informative error messages (and log lines) whenever something is wrong
with the data.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

import numpy as np

from source.utils.exceptions import MatrixShapeError, MatrixValidationError

logger = logging.getLogger("rat_connectome.utils.validators")


def validate_square_matrix(matrix: np.ndarray, name: str = "matrix") -> None:
    """Ensure ``matrix`` is a 2D square numpy array."""
    if not isinstance(matrix, np.ndarray):
        raise MatrixValidationError(f"'{name}' must be a numpy.ndarray, got {type(matrix).__name__}.")
    if matrix.ndim != 2:
        raise MatrixShapeError(f"'{name}' must be 2D, got shape {matrix.shape}.")
    if matrix.shape[0] != matrix.shape[1]:
        raise MatrixShapeError(f"'{name}' must be square, got shape {matrix.shape}.")


def validate_matching_shapes(matrices: Sequence[np.ndarray], names: Sequence[str]) -> None:
    """Ensure every matrix in ``matrices`` shares the same shape."""
    if len(matrices) == 0:
        raise MatrixValidationError("No matrices provided for shape validation.")
    reference_shape = matrices[0].shape
    for mat, name in zip(matrices, names, strict=False):
        if mat.shape != reference_shape:
            raise MatrixShapeError(
                f"Shape mismatch: '{names[0]}' has shape {reference_shape} but '{name}' has shape {mat.shape}."
            )


def validate_no_negative_weights(matrix: np.ndarray, name: str = "weight matrix") -> None:
    """Warn (log) if negative edge weights are found; structural connectomes should be non-negative."""
    if np.any(matrix < 0):
        n_negative = int(np.sum(matrix < 0))
        logger.warning(
            "'%s' contains %d negative values; this is unexpected for connectome weights.", name, n_negative
        )


def validate_node_indices(indices: Iterable[int], n_nodes: int, name: str = "node indices") -> None:
    """Ensure a collection of node indices to remove/keep are within bounds and unique."""
    indices = list(indices)
    if len(indices) != len(set(indices)):
        raise MatrixValidationError(f"'{name}' contains duplicate entries: {indices}.")
    out_of_bounds = [i for i in indices if i < 0 or i >= n_nodes]
    if out_of_bounds:
        raise MatrixValidationError(
            f"'{name}' contains out-of-bounds indices {out_of_bounds} for {n_nodes} nodes."
        )


def validate_non_empty_array(array: np.ndarray, name: str = "array") -> None:
    """Ensure an array used for statistics is non-empty (avoids silent NaN propagation)."""
    if array.size == 0:
        raise MatrixValidationError(f"'{name}' is empty; cannot compute statistics on zero elements.")
