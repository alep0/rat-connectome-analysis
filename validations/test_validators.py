from __future__ import annotations

import numpy as np
import pytest

from source.utils import validators
from source.utils.exceptions import MatrixShapeError, MatrixValidationError


def test_validate_square_matrix_accepts_square():
    validators.validate_square_matrix(np.zeros((3, 3)))  # should not raise


def test_validate_square_matrix_rejects_non_square():
    with pytest.raises(MatrixShapeError):
        validators.validate_square_matrix(np.zeros((3, 4)))


def test_validate_square_matrix_rejects_non_ndarray():
    with pytest.raises(MatrixValidationError):
        validators.validate_square_matrix([[1, 2], [3, 4]])  # type: ignore[arg-type]


def test_validate_matching_shapes_ok():
    validators.validate_matching_shapes([np.zeros((2, 2)), np.ones((2, 2))], ["a", "b"])


def test_validate_matching_shapes_mismatch():
    with pytest.raises(MatrixShapeError):
        validators.validate_matching_shapes([np.zeros((2, 2)), np.ones((3, 3))], ["a", "b"])


def test_validate_node_indices_rejects_duplicates():
    with pytest.raises(MatrixValidationError):
        validators.validate_node_indices([0, 0, 1], n_nodes=5)


def test_validate_node_indices_rejects_out_of_bounds():
    with pytest.raises(MatrixValidationError):
        validators.validate_node_indices([0, 10], n_nodes=5)


def test_validate_node_indices_accepts_valid():
    validators.validate_node_indices([0, 1, 2], n_nodes=5)


def test_validate_non_empty_array_rejects_empty():
    with pytest.raises(MatrixValidationError):
        validators.validate_non_empty_array(np.array([]))
