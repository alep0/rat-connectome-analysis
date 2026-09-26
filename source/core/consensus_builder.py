"""Build the "raw" consensus connectome by averaging across repetitions/subjects.

Mirrors notebook section 4: zeros are treated as "no observation" (not
as a true zero-weight measurement) while averaging, so the mean/std of
each edge is computed only over the repetitions where that edge was
actually observed (non-zero).
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass

import numpy as np

from source.utils.validators import validate_non_empty_array

logger = logging.getLogger("rat_connectome.core.consensus_builder")


@dataclass
class ConsensusResult:
    """Statistics of the raw consensus connectome."""

    mean_weight: np.ndarray
    std_weight: np.ndarray
    mean_distance: np.ndarray
    std_distance: np.ndarray
    occurrence: np.ndarray  # number of repetitions where each edge is non-zero


def compute_occurrence(w_3d: np.ndarray) -> np.ndarray:
    """Count, per edge, in how many repetitions the weight is non-zero."""
    return np.sum(w_3d > 0, axis=0)


def build_consensus(w_3d: np.ndarray, d_3d: np.ndarray) -> ConsensusResult:
    """Compute the mean/std connectome, ignoring zero (unobserved) edges.

    Parameters
    ----------
    w_3d, d_3d:
        Tensors of shape (n_reps, N, N), already NaN-cleaned.

    Returns
    -------
    ConsensusResult
    """
    validate_non_empty_array(w_3d, name="weight tensor")
    validate_non_empty_array(d_3d, name="distance tensor")

    w_nan = np.where(w_3d == 0, np.nan, w_3d)
    d_nan = np.where(d_3d == 0, np.nan, d_3d)

    with warnings.catch_warnings():
        # All-NaN slices (edges never observed) are expected and handled
        # explicitly below via nan_to_num; silence the noisy RuntimeWarning.
        warnings.simplefilter("ignore", category=RuntimeWarning)
        w_mean = np.nanmean(w_nan, axis=0)
        d_mean = np.nanmean(d_nan, axis=0)
        w_std = np.nanstd(w_nan, axis=0)
        d_std = np.nanstd(d_nan, axis=0)

    w_mean = np.nan_to_num(w_mean, nan=0.0)
    d_mean = np.nan_to_num(d_mean, nan=0.0)
    w_std = np.nan_to_num(w_std, nan=0.0)
    d_std = np.nan_to_num(d_std, nan=0.0)

    occurrence = compute_occurrence(w_3d)

    logger.info(
        "Consensus connectome built: %d nodes, %d edges observed at least once.",
        w_mean.shape[0],
        int(np.sum(occurrence > 0)),
    )
    return ConsensusResult(
        mean_weight=w_mean,
        std_weight=w_std,
        mean_distance=d_mean,
        std_distance=d_std,
        occurrence=occurrence,
    )
