"""Load raw weight (W) and distance (D) connectivity matrices for a rat.

This module replaces the original notebook cell that loaded, for a
single hard-coded ``rat_id``, ten repetition ``.txt`` files from an
absolute Windows path. Here the base path is configurable, every rat in
every group can be loaded, missing/corrupt files are handled explicitly,
and every step is logged instead of printed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from source.utils.exceptions import DataLoadError
from source.utils.validators import validate_square_matrix

logger = logging.getLogger("rat_connectome.core.data_loader")


@dataclass
class RatRawData:
    """Container for the raw per-repetition matrices of a single rat."""

    rat_id: str
    weights: dict[int, np.ndarray] = field(default_factory=dict)
    distances: dict[int, np.ndarray] = field(default_factory=dict)
    missing_repetitions: list[int] = field(default_factory=list)

    @property
    def n_loaded(self) -> int:
        return len(self.weights)


class ConnectomeDataLoader:
    """Loads raw W/D matrices for a rat across its repeated acquisitions."""

    def __init__(
        self,
        base_path: str | Path,
        data_history: str,
        folder_pattern: str,
        weight_file_pattern: str,
        distance_file_pattern: str,
        n_repetitions: int,
    ) -> None:
        self.base_path = Path(base_path)
        self.data_history = data_history
        self.folder_pattern = folder_pattern
        self.weight_file_pattern = weight_file_pattern
        self.distance_file_pattern = distance_file_pattern
        self.n_repetitions = n_repetitions

    def _repetition_paths(self, group_name: str, rat_id: str, repetition: int) -> tuple[Path, Path]:
        folder_name = self.folder_pattern.format(rat_id=rat_id, rep=repetition)
        weight_name = self.weight_file_pattern.format(rat_id=rat_id)
        distance_name = self.distance_file_pattern.format(rat_id=rat_id)
        folder = self.base_path / group_name / self.data_history / folder_name
        return folder / weight_name, folder / distance_name

    def load_rat(self, group_name: str, rat_id: str, remove_self_connections: bool = True) -> RatRawData:
        """Load all available repetitions of weight/distance matrices for ``rat_id``.

        A missing repetition is logged as a warning and skipped rather
        than aborting the whole load, so a single missing file does not
        prevent analyzing the rest of the cohort.

        Raises
        ------
        DataLoadError
            If *no* repetitions at all could be loaded for this rat, or
            if a file exists but cannot be parsed as a numeric matrix.
        """
        logger.info("Loading data for rat '%s' (expecting %d repetitions)...", rat_id, self.n_repetitions)
        data = RatRawData(rat_id=rat_id)

        for rep in range(1, self.n_repetitions + 1):
            weight_path, distance_path = self._repetition_paths(group_name, rat_id, rep)
            try:
                w_matrix = np.loadtxt(weight_path)
                d_matrix = np.loadtxt(distance_path)
            except FileNotFoundError as exc:
                logger.warning(
                    "Repetition %d for rat '%s' is missing (%s). Skipping.", rep, rat_id, exc.filename
                )
                data.missing_repetitions.append(rep)
                continue
            except (ValueError, OSError) as exc:
                raise DataLoadError(
                    f"Failed to parse matrices for rat '{rat_id}', repetition {rep}: {exc}"
                ) from exc

            validate_square_matrix(w_matrix, name=f"{rat_id} rep{rep} weight matrix")
            validate_square_matrix(d_matrix, name=f"{rat_id} rep{rep} distance matrix")

            if remove_self_connections:
                np.fill_diagonal(w_matrix, 0)

            data.weights[rep] = w_matrix
            data.distances[rep] = d_matrix
            logger.debug("  -> rep %d loaded successfully (shape=%s).", rep, w_matrix.shape)

        if data.n_loaded == 0:
            raise DataLoadError(
                f"No repetitions could be loaded for rat '{rat_id}' under '{self.base_path}'."
            )

        logger.info(
            "Rat '%s': loaded %d/%d repetitions (%d missing).",
            rat_id,
            data.n_loaded,
            self.n_repetitions,
            len(data.missing_repetitions),
        )
        return data
