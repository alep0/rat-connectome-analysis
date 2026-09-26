#!/usr/bin/env bash
# run_pipeline.sh
#
# Validates the configuration/data layout and then runs the full rat
# connectome analysis pipeline. Every step is logged both to stdout and
# to logs/run.log so that CI, Docker, and interactive runs share one
# consistent audit trail.
#
# Usage:
#   ./scripts/run_pipeline.sh [--config config/config.json] [--group NAME] [--rat ID]
#
# Exit codes:
#   0 success, 1 validation/config error, 2 one or more rats failed.

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/run.log"
mkdir -p "$LOG_DIR" "$PROJECT_ROOT/results"

log() {
    local level="$1"; shift
    local msg="$*"
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "${ts} | ${level} | run_pipeline.sh | ${msg}" | tee -a "$LOG_FILE"
}

on_error() {
    local exit_code=$?
    local line_no=$1
    log "ERROR" "run_pipeline.sh failed at line ${line_no} (exit code ${exit_code})."
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

PYTHON_BIN="${PYTHON_BIN:-python3}"
CONFIG_PATH="config/config.json"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config) CONFIG_PATH="$2"; shift 2 ;;
        --group)  EXTRA_ARGS+=("--group" "$2"); shift 2 ;;
        --rat)    EXTRA_ARGS+=("--rat" "$2"); shift 2 ;;
        *) log "ERROR" "Unknown argument: $1"; exit 1 ;;
    esac
done

log "INFO" "=== Rat Connectome Analysis: pipeline run started ==="
log "INFO" "Project root: $PROJECT_ROOT"
log "INFO" "Config path:  $CONFIG_PATH"

if ! command -v "$PYTHON_BIN" &>/dev/null; then
    log "ERROR" "Python interpreter '$PYTHON_BIN' not found on PATH."
    exit 1
fi
log "INFO" "Using Python interpreter: $($PYTHON_BIN --version 2>&1)"

log "INFO" "Step 1/2: validating configuration and data layout..."
if ! "$PYTHON_BIN" scripts/validate_setup.py --config "$CONFIG_PATH"; then
    log "ERROR" "Configuration validation failed. Aborting before running the pipeline."
    exit 1
fi
log "INFO" "Validation passed."

log "INFO" "Step 2/2: running analysis pipeline..."
set +e
"$PYTHON_BIN" scripts/run_analysis.py --config "$CONFIG_PATH" "${EXTRA_ARGS[@]}"
PIPELINE_EXIT_CODE=$?
set -e

if [[ $PIPELINE_EXIT_CODE -eq 0 ]]; then
    log "INFO" "=== Pipeline finished successfully. ==="
elif [[ $PIPELINE_EXIT_CODE -eq 2 ]]; then
    log "WARNING" "=== Pipeline finished with some rat-level failures (exit 2). See results/run_summary.csv. ==="
else
    log "ERROR" "=== Pipeline aborted (exit code ${PIPELINE_EXIT_CODE}). ==="
fi

exit "$PIPELINE_EXIT_CODE"
