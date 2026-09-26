"""Inter-subject consistency (edge occurrence) analysis.

Mirrors notebook section 4: how many repetitions/subjects each edge
appears in, and the "survival curve" of the connectome as a minimum
occurrence threshold is applied.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from source.utils.exceptions import AnalysisError
from source.utils.validators import validate_non_empty_array

logger = logging.getLogger("rat_connectome.analysis.consistency")


def edge_occurrences(occurrence: np.ndarray) -> np.ndarray:
    """Flatten the occurrence matrix to the edges that appear at least once."""
    mask = occurrence > 0
    flat = occurrence[mask]
    validate_non_empty_array(flat, name="edge occurrences")
    return flat


def survival_curve(
    occurrence_flat: np.ndarray,
    n_nodes: int,
    thresholds: list[int],
) -> pd.DataFrame:
    """Compute, for each minimum-occurrence threshold, how much of the connectome survives.

    Parameters
    ----------
    occurrence_flat:
        1D array of per-edge occurrence counts (edges with 0 occurrences already excluded).
    n_nodes:
        Number of nodes in the (undirected, upper-triangular) network,
        used to compute network density.
    thresholds:
        Minimum-occurrence thresholds to evaluate.

    Returns
    -------
    pandas.DataFrame
        Columns: threshold, n_edges_surviving, pct_of_observed_edges, network_density.
    """
    if n_nodes < 2:
        raise AnalysisError(f"n_nodes must be >= 2 to compute density, got {n_nodes}.")

    total_edges = len(occurrence_flat)
    max_possible_edges = int(n_nodes * (n_nodes - 1) / 2)

    rows = []
    for thresh in thresholds:
        n_surviving = int(np.sum(occurrence_flat >= thresh))
        rows.append(
            {
                "threshold": thresh,
                "n_edges_surviving": n_surviving,
                "pct_of_observed_edges": 100.0 * n_surviving / total_edges,
                "network_density": n_surviving / max_possible_edges,
            }
        )
    df = pd.DataFrame(rows)
    logger.info(
        "Computed survival curve across %d thresholds (%d total observed edges).",
        len(thresholds),
        total_edges,
    )
    return df
