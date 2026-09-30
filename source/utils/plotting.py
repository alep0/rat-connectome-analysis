"""Figure-generation helpers used by the analysis pipeline.

Every function here builds a single Matplotlib figure, saves it to
disk, and closes it (never calls ``plt.show()``), so the pipeline can
run headlessly (e.g. inside Docker/CI) without a display backend.
Import this module only after setting ``matplotlib.use("Agg")`` -- done
centrally in :mod:`source.analysis.group_pipeline`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap

logger = logging.getLogger("rat_connectome.utils.plotting")

DEFAULT_RC_PARAMS = {
    "axes.spines.top": True,
    "axes.spines.right": True,
    "axes.spines.bottom": True,
    "axes.spines.left": True,
    "axes.grid": False,
    "lines.linewidth": 2,
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "figure.dpi": 100,
    "savefig.dpi": 300,
}


def apply_default_style() -> None:
    plt.rcParams.update(DEFAULT_RC_PARAMS)


def _save(fig: plt.Figure, out_path: Path, dpi: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.debug("Saved figure to '%s'.", out_path)


def plot_weight_heatmap_and_topology(w_mean: np.ndarray, out_path: Path, dpi: int = 300) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    sns.heatmap(w_mean, cmap="magma", ax=axes[0], cbar_kws={"label": "Weight"}, square=True)
    axes[0].set_title("Gross Mean Weight", fontsize=14, fontweight="bold")
    axes[0].set_xlabel("Region of Interest (ROI)")
    axes[0].set_ylabel("Region of Interest (ROI)")

    binary = (w_mean > 0).astype(int)
    cmap_binary = ListedColormap(["red", "blue"])
    sns.heatmap(binary, cmap=cmap_binary, ax=axes[1], cbar=False, square=True)
    axes[1].set_title("Binary Topology (Blue = Connection, Red = Null)")
    axes[1].set_xlabel("Region of Interest (ROI)")
    axes[1].set_ylabel("Region of Interest (ROI)")

    fig.tight_layout()
    _save(fig, out_path, dpi)


def plot_occurrence_histogram(
    occurrence_flat: np.ndarray, n_repetitions: int, out_path: Path, dpi: int = 300
) -> None:
    bins = np.arange(0.5, n_repetitions + 1.5, 1)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(occurrence_flat, bins=bins, color="royalblue", edgecolor="navy", alpha=0.8)
    ax.set_title("Inter-Subject Consistency")
    ax.set_xlabel("Edge occurrence across repetitions")
    ax.set_ylabel("Counts")
    ax.set_xticks(range(1, n_repetitions + 1))
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    fig.tight_layout()
    _save(fig, out_path, dpi)


def plot_survival_curve(df_survival: pd.DataFrame, out_path: Path, dpi: int = 300) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        df_survival["threshold"],
        df_survival["pct_of_observed_edges"],
        linestyle="-",
        marker="o",
        color="indigo",
        linewidth=2.5,
        markersize=7,
    )
    ax.fill_between(df_survival["threshold"], df_survival["pct_of_observed_edges"], color="indigo", alpha=0.1)
    ax.set_xticks(df_survival["threshold"])
    ax.set_title("Survival Curve: Minimum Occurrence Criterion")
    ax.set_xlabel("Threshold: Minimal Occurrence Required")
    ax.set_ylabel(r"Percentage of the Connectome Conserved, $P_{Cons}\,/\,\%$")
    ax.grid(axis="both", linestyle="--", alpha=0.7)
    fig.tight_layout()
    _save(fig, out_path, dpi)


def plot_ocurrence_scatter(df: pd.DataFrame, out_path: Path, dpi: int = 300) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(
        df["distance"],
        np.log10(df["weight"].clip(lower=1e-12)),
        c=df["pct_occurrence"],
        s=10,
        cmap="viridis",
        alpha=0.6,
    )
    cbar = fig.colorbar(scatter, ax=ax, format="%.0f%%")
    cbar.set_label("Edge occurrence across subjects", fontsize=12)
    ax.set_title("Weight Distribution with Inter-Subject Consistency")
    ax.set_xlabel(r"Physical Distance, $d_{Real}$")
    ax.set_ylabel(r"$\log_{10}(\mathrm{Weight})$")
    ax.grid(True, linestyle="--", alpha=0.7)
    fig.tight_layout()
    _save(fig, out_path, dpi)


def plot_cv_scatter(df: pd.DataFrame, out_path: Path, dpi: int = 300) -> None:
    mask_cero = (df["cv"] == 0.0)
    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(
        df["distance"],
        np.log10(df["weight"].clip(lower=1e-12)),
        c=df["cv"],
        s=10,
        cmap="viridis",
        alpha=0.6,
    )
    ax.scatter(
        df["distance"][mask_cero], 
        np.log10(df["weight"][mask_cero].clip(lower=1e-12)),
        color='red',
        s=10,        
        alpha=0.9, 
        )
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label('Cross Variance Across Subjects, CV', fontsize=12)
    ax.set_title('Weight Distribution with Coefficient of Variation Across Subjects')
    ax.set_xlabel(r"Physical Distance, $d_{Real}$")
    ax.set_ylabel(r"$\log_{10}(\mathrm{Weight})$")
    ax.grid(True, linestyle="--", alpha=0.7)
    fig.tight_layout()
    _save(fig, out_path, dpi)


def cv_ocurrence_boxplot(df: pd.DataFrame, out_path: Path, dpi: int = 300) -> None:
    df_plot = pd.DataFrame({
        'Apariciones': df["pct_occurrence"],
        'CV': df["cv"]
    })
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    sns.boxplot(
        x='Apariciones', 
        y='CV', 
        data=df_plot, 
        color='lightgray', 
        showfliers=False, 
        width=0.5,
        ax=ax
    )
    
    sns.stripplot(
        x='Apariciones', 
        y='CV', 
        data=df_plot, 
        hue='Apariciones',
        palette='plasma', 
        alpha=0.4, 
        jitter=True, 
        size=4,
        legend=False,
        ax=ax
    )
    
    ax.set_title('CV Boxplot with spreading', fontsize=14)
    ax.set_xlabel('Occurrence', fontsize=12)
    ax.set_ylabel('Variation coefficient (CV)', fontsize=12)
    ax.grid(True, axis='y', linestyle='--', alpha=0.6)
    
    fig.tight_layout()
    _save(fig, out_path, dpi)
    

def plot_cv_distribution(
    cv_hist_values: np.ndarray, out_path: Path, n_bins: int = 50, dpi: int = 300
) -> None:
    max_cv = np.max(cv_hist_values) if cv_hist_values.size else 1.0
    bins = np.linspace(0, max_cv, n_bins + 1)
    counts, _ = np.histogram(cv_hist_values, bins=bins)
    widths = np.diff(bins)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(bins[:-1], counts, width=widths, align="edge", color="#9370DB", edgecolor="black", alpha=0.7)
    ax.set_title("Coefficient of Variation (CV) Distribution", fontweight="bold")
    ax.set_xlabel("Coefficient of Variation, CV")
    ax.set_ylabel("Counts")
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    fig.tight_layout()
    _save(fig, out_path, dpi)


def plot_cv_survival_curve(df_cv_survival: pd.DataFrame, out_path: Path, dpi: int = 300) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df_cv_survival["cv_threshold"], df_cv_survival["pct_of_edges"], color="teal", linewidth=2.5)
    ax.fill_between(df_cv_survival["cv_threshold"], df_cv_survival["pct_of_edges"], color="teal", alpha=0.1)
    ax.invert_xaxis()
    ax.set_title("Survival Curve: Maximum CV Criterion", fontweight="bold")
    ax.set_xlabel(r"Threshold: Maximum CV Allowed ($CV \leq CV_{Threshold}$)")
    ax.set_ylabel(r"Percentage of the Connectome Conserved, $P_{Cons}\,/\,\%$")
    ax.grid(axis="both", linestyle="--", alpha=0.7)
    fig.tight_layout()
    _save(fig, out_path, dpi)


def plot_cv_comparison_across_multipliers(
    cv_dist_dict: dict[str, np.ndarray], out_path: Path, n_bins: int = 50, dpi: int = 300
) -> None:
    """Compare CV distributions before/after removing outliers at multiple IQR multipliers."""
    baseline = cv_dist_dict.get("original")
    max_cv = np.max(baseline) if baseline is not None and baseline.size else 1.0
    bins = np.linspace(0, max_cv, n_bins + 1)
    centers = bins[:-1] + np.diff(bins) / 2

    style_cycle = [
        {"color": "black", "marker": "o", "ls": "--"},
        {"color": "#1f77b4", "marker": "s", "ls": "-"},
        {"color": "#2ca02c", "marker": "^", "ls": "-"},
        {"color": "#d62728", "marker": "D", "ls": "-"},
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    for idx, (label, values) in enumerate(cv_dist_dict.items()):
        counts, _ = np.histogram(values, bins=bins)
        cfg = style_cycle[idx % len(style_cycle)]
        ax.plot(
            centers,
            counts,
            label=label,
            color=cfg["color"],
            marker=cfg["marker"],
            markersize=5,
            linewidth=2,
            linestyle=cfg["ls"],
            alpha=0.85,
        )

    ax.set_title("Evolution of CV After Outlier Removal (High-Consistency Edges)", fontweight="bold")
    ax.set_xlabel("Coefficient of Variation (CV)")
    ax.set_ylabel("Counts")
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.legend(loc="upper right", title="Cleaning level")
    fig.tight_layout()
    _save(fig, out_path, dpi)


def plot_outlier_map(
    n_nodes: int,
    i_idx: np.ndarray,
    j_idx: np.ndarray,
    max_is_outlier: np.ndarray,
    min_is_outlier: np.ndarray,
    out_path: Path,
    dpi: int = 300,
) -> None:
    """Spatial RGB map of which edges have anomalous max/min values (Tukey fences)."""
    from matplotlib.patches import Patch

    rgb = np.zeros((n_nodes, n_nodes, 3))
    for i, j, a_max, a_min in zip(i_idx, j_idx, max_is_outlier, min_is_outlier, strict=False):
        if a_max and a_min:
            color = [0, 1, 0]
        elif a_max:
            color = [1, 0, 0]
        elif a_min:
            color = [0, 0, 1]
        else:
            color = [1, 1, 1]
        rgb[i, j] = color

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(rgb, interpolation="nearest")
    ax.set_title("Spatial Outlier Map (Interquartile Range Test)", fontsize=15, fontweight="bold")
    ax.set_xlabel("ROIs (Target)")
    ax.set_ylabel("ROIs (Source)")
    ax.set_xticks(np.arange(-0.5, n_nodes, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_nodes, 1), minor=True)
    ax.grid(which="minor", color="black", linestyle="-", linewidth=0.2, alpha=0.3)
    ax.tick_params(which="minor", bottom=False, left=False)

    legend = [
        Patch(facecolor="red", edgecolor="black", label="Only max is an outlier"),
        Patch(facecolor="blue", edgecolor="black", label="Only min is an outlier"),
        Patch(facecolor="green", edgecolor="black", label="Max and min are outliers"),
        Patch(facecolor="white", edgecolor="black", label="No anomalies"),
        Patch(facecolor="black", edgecolor="white", label="Edge does not exist"),
    ]
    ax.legend(handles=legend, loc="lower left")
    fig.tight_layout()
    _save(fig, out_path, dpi)
