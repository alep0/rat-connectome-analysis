# Docker

The pipeline is fully packaged in a multi-stage Docker image so it can run
identically on any machine (or in CI) without installing Python locally.

## Build the image

```bash
docker build -t rat-connectome-analysis:latest .
```

or via Compose:

```bash
docker compose build
```

## Run the full pipeline

```bash
docker compose run --rm analysis
```

This mounts:

| Host path   | Container path | Purpose |
|-------------|-----------------|---------|
| `./data`    | `/app/data`     | Read your raw connectome data. |
| `./results` | `/app/results`  | Persist figures/tables/consensus matrices back to the host. |
| `./logs`    | `/app/logs`     | Persist `run.log` back to the host. |
| `./config`  | `/app/config`   | Edit `config.json` without rebuilding the image. |

Equivalently, with plain `docker run`:

```bash
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/results:/app/results" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/config:/app/config" \
  rat-connectome-analysis:latest --config config/config.json
```

## Run a single group or rat

Override the default command:

```bash
docker compose run --rm analysis --config config/config.json --group control
docker compose run --rm analysis --config config/config.json --group control --rat R01
```

## Run the test suite inside the container

```bash
docker compose run --rm test
```

or:

```bash
docker run --rm --entrypoint python rat-connectome-analysis:latest -m pytest validations/ -v
```

## Validate configuration inside the container

```bash
docker run --rm --entrypoint python \
  -v "$(pwd)/config:/app/config" \
  rat-connectome-analysis:latest scripts/validate_setup.py --config config/config.json
```

## Image details

- **Base image**: `python:3.11-slim` (configurable via the `PYTHON_VERSION`
  build arg).
- **Multi-stage build**: dependencies are installed into a virtual
  environment in a `builder` stage; the final `runtime` stage copies only
  the venv and source code, keeping the image small.
- **Non-root user**: the container runs as `appuser` (UID 1000), not root.
- **Headless plotting**: `MPLBACKEND=Agg` is set so Matplotlib never tries
  to open a display.
- **Healthcheck**: `python -c "import source"` verifies the package is
  importable.
- **Entrypoint**: `python scripts/run_analysis.py`, so any arguments passed
  to `docker run`/`docker compose run` after the image name are forwarded to
  the CLI (e.g. `--group`, `--rat`, `--log-level`).

## Building for a different Python version

```bash
docker build --build-arg PYTHON_VERSION=3.12 -t rat-connectome-analysis:py312 .
```

## Pushing to a registry

```bash
docker tag rat-connectome-analysis:latest ghcr.io/<your-org>/rat-connectome-analysis:1.0.0
docker push ghcr.io/<your-org>/rat-connectome-analysis:1.0.0
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `permission denied` writing to `results/`/`logs/` on the host | The container runs as UID 1000; ensure the host directories are writable by that UID, or `chmod -R a+rwX results logs` before running. |
| Container exits immediately with code 1 | Almost always a configuration error — check `logs/run.log` on the host (mounted volume) for the exact message. |
| Container exits with code 2 | One or more rats failed; this is not a Docker problem — inspect `results/run_summary.csv`. |
| Image build fails installing dependencies | Check your network/proxy settings; `pip install` runs during the `builder` stage and needs internet access. |
