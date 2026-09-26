#!/usr/bin/env bash
# setup_env.sh
#
# Creates a local Python virtual environment and installs project
# dependencies. For a Conda-based setup, see docs/QUICKSTART.md /
# environment.yml instead.
#
# Usage: ./scripts/setup_env.sh [venv_dir]

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/run.log"
mkdir -p "$LOG_DIR"

log() {
    local level="$1"; shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') | ${level} | setup_env.sh | $*" | tee -a "$LOG_FILE"
}

trap 'log "ERROR" "setup_env.sh failed at line $LINENO."; exit 1' ERR

VENV_DIR="${1:-.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log "INFO" "Creating virtual environment at '$VENV_DIR' using $($PYTHON_BIN --version 2>&1)..."
"$PYTHON_BIN" -m venv "$VENV_DIR"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

log "INFO" "Upgrading pip..."
pip install --upgrade pip >>"$LOG_FILE" 2>&1

log "INFO" "Installing project requirements..."
pip install -r requirements.txt >>"$LOG_FILE" 2>&1

log "INFO" "Environment ready. Activate it with: source $VENV_DIR/bin/activate"
