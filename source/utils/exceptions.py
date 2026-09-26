"""Custom exception hierarchy for the rat-connectome-analysis pipeline.

Using dedicated exception types (instead of bare ``Exception`` or
``ValueError`` everywhere) makes error handling in callers precise and
makes log messages/tests easier to reason about.
"""

from __future__ import annotations


class RatConnectomeError(Exception):
    """Base class for all custom errors raised by this package."""


class ConfigurationError(RatConnectomeError):
    """Raised when the configuration file is missing, malformed, or invalid."""


class DataLoadError(RatConnectomeError):
    """Raised when raw connectome matrices cannot be located or read."""


class MatrixShapeError(RatConnectomeError):
    """Raised when matrices do not have the expected/consistent shape."""


class MatrixValidationError(RatConnectomeError):
    """Raised when a matrix fails a sanity/validation check (NaNs, negatives, asymmetry, etc.)."""


class AnalysisError(RatConnectomeError):
    """Raised when an analysis step fails to complete (e.g. empty input, degenerate stats)."""
