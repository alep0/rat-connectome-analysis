# syntax=docker/dockerfile:1
# ============================================================================
# Dockerfile — Rat Connectome Analysis
#
# Multi-stage build:
#   1. "builder" installs dependencies into a virtual environment.
#   2. "runtime" is a slim final image that only carries the venv + source,
#      runs as a non-root user, and defaults to the full pipeline entrypoint.
# ============================================================================

ARG PYTHON_VERSION=3.11

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL org.opencontainers.image.title="rat-connectome-analysis" \
      org.opencontainers.image.description="Consensus connectome construction and QA pipeline for rat structural connectivity data." \
      org.opencontainers.image.licenses="MIT"

# Runtime OS deps needed by matplotlib for headless PNG rendering.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libfreetype6 libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg

WORKDIR /app

COPY --chown=appuser:appuser source/ source/
COPY --chown=appuser:appuser scripts/ scripts/
COPY --chown=appuser:appuser config/ config/
COPY --chown=appuser:appuser pytest.ini .

RUN mkdir -p data/raw data/processed logs results validations \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser validations/ validations/

USER appuser

VOLUME ["/app/data", "/app/results", "/app/logs"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import source" || exit 1

ENTRYPOINT ["python", "scripts/run_analysis.py"]
CMD ["--config", "config/config.json"]
