#!/usr/bin/env bash
# validate_environment.sh
#
# Sanity-checks that the tools required to build/run/test this project
# are present and meet minimum version requirements. Safe to run in CI
# before installing dependencies, or locally before `setup_env.sh`.
#
# Usage: ./validations/validate_environment.sh

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/run.log"
mkdir -p "$LOG_DIR"

log() {
    local level="$1"; shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') | ${level} | validate_environment.sh | $*" | tee -a "$LOG_FILE"
}

MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10
EXIT_CODE=0

log "INFO" "=== Environment validation started ==="

# --- Python -------------------------------------------------------------
if command -v python3 &>/dev/null; then
    PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    PY_MAJOR="$(echo "$PY_VERSION" | cut -d. -f1)"
    PY_MINOR="$(echo "$PY_VERSION" | cut -d. -f2)"
    if [[ "$PY_MAJOR" -gt "$MIN_PYTHON_MAJOR" || ( "$PY_MAJOR" -eq "$MIN_PYTHON_MAJOR" && "$PY_MINOR" -ge "$MIN_PYTHON_MINOR" ) ]]; then
        log "INFO" "Python $PY_VERSION found (>= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}, OK)."
    else
        log "ERROR" "Python $PY_VERSION found, but >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} is required."
        EXIT_CODE=1
    fi
else
    log "ERROR" "python3 not found on PATH."
    EXIT_CODE=1
fi

# --- pip ------------------------------------------------------------------
if python3 -m pip --version &>/dev/null; then
    log "INFO" "pip is available."
else
    log "WARNING" "pip is not available for python3; 'setup_env.sh' will fail."
fi

# --- Docker (optional but recommended) ------------------------------------
if command -v docker &>/dev/null; then
    log "INFO" "Docker found: $(docker --version)."
else
    log "WARNING" "Docker not found. Docker-based runs (see docs/Docker.md) will not be available."
fi

# --- Conda (optional) -------------------------------------------------------
if command -v conda &>/dev/null; then
    log "INFO" "Conda found: $(conda --version)."
else
    log "INFO" "Conda not found (optional; only needed for the Conda install path)."
fi

# --- Required project files -------------------------------------------------
for f in "config/config.json" "requirements.txt" "environment.yml" "Dockerfile"; do
    if [[ -f "$PROJECT_ROOT/$f" ]]; then
        log "INFO" "Found required file: $f"
    else
        log "ERROR" "Missing required file: $f"
        EXIT_CODE=1
    fi
done

if [[ $EXIT_CODE -eq 0 ]]; then
    log "INFO" "=== Environment validation PASSED ==="
else
    log "ERROR" "=== Environment validation FAILED ==="
fi

exit "$EXIT_CODE"
