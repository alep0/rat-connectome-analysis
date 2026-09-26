"""Stack per-repetition matrices into 3D tensors and clean known artifacts.

Mirrors the notebook's NaN-inspection and disconnected-node-removal
logic (sections 0.3, 1.1 and 1.2), but as pure, tested, logged
functions operating on a :class:`~source.core.data_loader.RatRawData`
instance instead of module-level notebook variables.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np
import pandas as pd

from source.core.data_loader import RatRawData
from source.utils.exceptions import MatrixValidationError
from source.utils.validators import validate_node_indices

logger = logging.getLogger("rat_connectome.core.matrix_cleaner")


def stack_to_3d(data: RatRawData) -> tuple[np.ndarray, np.ndarray]:
    """Stack the loaded per-repetition matrices into (n_reps, N, N) tensors.

    Only successfully loaded repetitions are stacked, in ascending
    repetition order, so downstream code should not assume a fixed
    ``n_repetitions`` length.
    """
    reps = sorted(data.weights.keys())
    if not reps:
        raise MatrixValidationError(f"Rat '{data.rat_id}' has no loaded repetitions to stack.")
    w_3d = np.array([data.weights[r] for r in reps])
    d_3d = np.array([data.distances[r] for r in reps])
    logger.debug(
        "Rat '%s': stacked %d repetitions into tensors of shape %s.", data.rat_id, len(reps), w_3d.shape
    )
    return w_3d, d_3d


def report_nan_positions(w_3d: np.ndarray, d_3d: np.ndarray) -> pd.DataFrame:
    """Return a tidy DataFrame describing every (repetition, i, j) with a NaN in W or D."""
    nan_mask = np.isnan(w_3d) | np.isnan(d_3d)
    coords = np.argwhere(nan_mask)
    records = [
        {
            "repetition": int(k) + 1,
            "row": int(i),
            "col": int(j),
            "weight_value": w_3d[k, i, j],
            "distance_value": d_3d[k, i, j],
        }
        for k, i, j in coords
    ]
    df = pd.DataFrame(records)
    if df.empty:
        logger.info("No NaN values found in weight/distance tensors.")
    else:
        logger.warning("Found %d NaN entries across weight/distance tensors.", len(df))
    return df


def clean_nans(w_3d: np.ndarray, d_3d: np.ndarray, fill_value: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    """Replace NaNs in either tensor (at matching positions) with ``fill_value``.

    NaNs are safe to zero here because they correspond to edges with
    zero weight (no physical connection), not missing measurements of
    an existing edge.
    """
    nan_mask = np.isnan(w_3d) | np.isnan(d_3d)
    n_nan = int(nan_mask.sum())
    w_clean = np.where(nan_mask, fill_value, w_3d)
    d_clean = np.where(nan_mask, fill_value, d_3d)
    if n_nan:
        logger.info("Replaced %d NaN entries with %.1f in weight/distance tensors.", n_nan, fill_value)
    return w_clean, d_clean


def find_disconnected_nodes(w_mean: np.ndarray) -> np.ndarray:
    """Return indices of nodes with zero degree (fully disconnected) in a symmetrized mean matrix."""
    w_sym = w_mean + w_mean.T - np.diag(np.diag(w_mean))
    empty_mask = np.all(w_sym == 0, axis=0) | np.all(w_sym == 0, axis=1)
    indices = np.where(empty_mask)[0]
    logger.info("Found %d fully disconnected nodes: %s", len(indices), indices.tolist())
    return indices


def remove_nodes(
    w_3d: np.ndarray,
    d_3d: np.ndarray,
    node_indices: Sequence[int],
) -> tuple[np.ndarray, np.ndarray]:
    """Remove ``node_indices`` (e.g. non-ROI/background nodes) from both tensors.

    Parameters
    ----------
    w_3d, d_3d:
        Tensors of shape (n_reps, N, N).
    node_indices:
        Row/column indices to delete from every matrix in the tensors
        (e.g. background, white matter, ventricle labels that are not
        genuine brain regions).
    """
    n_nodes = w_3d.shape[1]
    validate_node_indices(node_indices, n_nodes, name="nodes_to_remove")

    w_clean = np.delete(w_3d, node_indices, axis=1)
    w_clean = np.delete(w_clean, node_indices, axis=2)
    d_clean = np.delete(d_3d, node_indices, axis=1)
    d_clean = np.delete(d_clean, node_indices, axis=2)

    logger.info(
        "Removed %d nodes (%s): %d -> %d nodes remaining.",
        len(node_indices),
        list(node_indices),
        n_nodes,
        w_clean.shape[1],
    )
    return w_clean, d_clean


def full_cleaning_pipeline(
    data: RatRawData,
    fictitious_nodes: Sequence[int],
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Convenience wrapper: stack -> report NaNs -> clean NaNs -> remove fictitious nodes.

    Returns
    -------
    (w_clean, d_clean, nan_report)
        Cleaned tensors and the NaN report collected before cleaning.
    """
    w_3d, d_3d = stack_to_3d(data)
    nan_report = report_nan_positions(w_3d, d_3d)
    w_3d, d_3d = clean_nans(w_3d, d_3d)
    if fictitious_nodes:
        w_3d, d_3d = remove_nodes(w_3d, d_3d, fictitious_nodes)
    return w_3d, d_3d, nan_report
