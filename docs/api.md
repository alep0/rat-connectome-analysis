# API Reference

This document describes the public modules, classes and functions of the
`source` package, organized by subpackage.

---

## `source.core` — data loading, cleaning, consensus building

### `source.core.data_loader`

#### `class RatRawData`
Container for one rat's raw per-repetition matrices.

| Field | Type | Description |
|---|---|---|
| `rat_id` | `str` | Rat identifier (e.g. `"R01"`). |
| `weights` | `Dict[int, np.ndarray]` | Repetition number → weight matrix. |
| `distances` | `Dict[int, np.ndarray]` | Repetition number → distance matrix. |
| `missing_repetitions` | `List[int]` | Repetitions that could not be loaded. |
| `n_loaded` (property) | `int` | Number of successfully loaded repetitions. |

#### `class ConnectomeDataLoader(base_path, folder_pattern, weight_file_pattern, distance_file_pattern, n_repetitions)`
Loads raw `W`/`D` matrices for a rat across repeated acquisitions.

- **`load_rat(rat_id: str, remove_self_connections: bool = True) -> RatRawData`**
  Loads every available repetition for `rat_id`. Missing individual files
  are logged and skipped (not fatal); raises `DataLoadError` only if **no**
  repetition could be loaded, or if a file exists but cannot be parsed.

---

### `source.core.matrix_cleaner`

- **`stack_to_3d(data: RatRawData) -> (w_3d, d_3d)`** — stacks loaded
  repetitions into `(n_reps, N, N)` tensors, in repetition order.
- **`report_nan_positions(w_3d, d_3d) -> pd.DataFrame`** — tidy table of
  every `(repetition, row, col)` containing a NaN in `W` or `D`.
- **`clean_nans(w_3d, d_3d, fill_value=0.0) -> (w_3d, d_3d)`** — replaces
  NaNs at matching positions in both tensors.
- **`find_disconnected_nodes(w_mean) -> np.ndarray`** — indices of nodes
  with zero degree in the symmetrized mean weight matrix.
- **`remove_nodes(w_3d, d_3d, node_indices) -> (w_3d, d_3d)`** — deletes
  the given row/column indices from every matrix in both tensors.
- **`full_cleaning_pipeline(data, fictitious_nodes) -> (w_3d, d_3d, nan_report)`**
  — convenience wrapper chaining the above four steps.

---

### `source.core.consensus_builder`

#### `class ConsensusResult`
| Field | Description |
|---|---|
| `mean_weight`, `std_weight` | Per-edge mean/std of `W`, ignoring unobserved (zero) edges. |
| `mean_distance`, `std_distance` | Same, for `D`. |
| `occurrence` | Per-edge count of repetitions where the edge is non-zero. |

- **`compute_occurrence(w_3d) -> np.ndarray`**
- **`build_consensus(w_3d, d_3d) -> ConsensusResult`**

---

## `source.analysis` — statistical analyses

### `source.analysis.consistency_analysis`
- **`edge_occurrences(occurrence) -> np.ndarray`** — flattens to edges
  observed at least once.
- **`survival_curve(occurrence_flat, n_nodes, thresholds) -> pd.DataFrame`**
  — columns: `threshold`, `n_edges_surviving`, `pct_of_observed_edges`,
  `network_density`.

### `source.analysis.cv_analysis`
- **`compute_cv(mean_weight, std_weight, occurrence) -> np.ndarray`** —
  per-edge CV = std/mean; forced to `0.0` for single-occurrence edges.
- **`cv_edge_table(cv_matrix, occurrence, mean_weight, w_3d) -> pd.DataFrame`**
  — per-edge table sorted by descending CV, including the raw observed
  weight values per edge.
- **`cv_survival_curve(cv_flat, n_points=1000, percentile_cap=95.0) -> pd.DataFrame`**
  — fraction of edges retained as the **maximum allowed** CV threshold varies.
- **`cv_vs_metadata(cv_matrix, occurrence, mean_weight, mean_distance, n_repetitions) -> pd.DataFrame`**
  — tidy table for scatter/violin plots (excludes single-occurrence edges).

### `source.analysis.outlier_analysis`
- **`multiplier_from_p_value(p_value) -> float`** — converts a two-sided
  normal-tail p-value into an equivalent Tukey IQR multiplier `B`.
- **`compute_iqr_bounds(w_3d, multiplier) -> IqrBounds`** — per-edge
  Q1/Q3/IQR and lower/upper Tukey fences.
- **`flag_extreme_value_outliers(w_3d, bounds) -> (max_is_outlier, min_is_outlier)`**
- **`outlier_summary_table(cv_matrix, occurrence, mean_weight, std_weight, w_3d, bounds) -> pd.DataFrame`**
- **`recompute_cv_without_outliers(w_3d, bounds) -> np.ndarray`**
- **`cv_distribution_across_multipliers(w_3d, cv_flat_baseline, occurrence_mask, min_occurrence_mask, multipliers) -> Dict[str, np.ndarray]`**

### `source.analysis.group_pipeline`

#### `class RatAnalysisResult`
Outcome of running the pipeline for a single rat: `rat_id`, `group`,
`success`, `n_nodes`, `n_repetitions_loaded`, `error`, `tables`.

#### `class GroupAnalysisPipeline(config: dict)`
- **`run_all() -> List[RatAnalysisResult]`** — runs every rat in every
  configured group; never raises for a single rat's failure (isolates
  failures per-rat) and writes `results/run_summary.csv`.
- **`run_single_rat(group_name, rat_id) -> RatAnalysisResult`** — runs one
  rat's full analysis chain; catches and logs all errors.

---

## `source.utils` — cross-cutting utilities

### `source.utils.config_loader`
- **`load_config(config_path) -> dict`** — loads, parses and validates
  `config.json`; raises `ConfigurationError` on any problem.
- **`validate_config(config: dict) -> None`**

**Required config keys:**
```
data.base_path, data.groups, data.n_repetitions, data.folder_pattern,
data.file_pattern.weight, data.file_pattern.distance,
preprocessing.fictitious_nodes,
analysis.occurrence_thresholds, analysis.cv_threshold,
output.results_dir,
logging.log_dir
```

### `source.utils.logging_config`
- **`setup_logging(config_path=None, log_dir="logs", level="INFO") -> logging.Logger`**
  — configures console + rotating-file logging exactly once per process.
- **`get_logger(name) -> logging.Logger`**

### `source.utils.validators`
- `validate_square_matrix`, `validate_matching_shapes`,
  `validate_no_negative_weights`, `validate_node_indices`,
  `validate_non_empty_array` — raise `MatrixShapeError` /
  `MatrixValidationError` with descriptive messages.

### `source.utils.plotting`
Figure builders (each saves a PNG and closes the figure; never calls
`plt.show()`): `plot_weight_heatmap_and_topology`,
`plot_occurrence_histogram`, `plot_survival_curve`, `plot_cv_scatter`,
`plot_cv_distribution`, `plot_cv_survival_curve`,
`plot_cv_comparison_across_multipliers`, `plot_outlier_map`.

### `source.utils.exceptions`
`RatConnectomeError` (base) → `ConfigurationError`, `DataLoadError`,
`MatrixShapeError`, `MatrixValidationError`, `AnalysisError`.

---

## Command-line scripts

### `scripts/run_analysis.py`
```
python scripts/run_analysis.py --config config/config.json [--group NAME] [--rat ID] [--log-level LEVEL]
```
Exit codes: `0` success, `1` configuration error, `2` one or more rats failed.

### `scripts/validate_setup.py`
```
python scripts/validate_setup.py --config config/config.json
```
Validates the config schema and reports missing data files/folders.

### `scripts/run_pipeline.sh`
Bash wrapper: runs `validate_setup.py` then `run_analysis.py`, logging every
step to `logs/run.log`.
