# Installation

This guide covers a full, from-scratch installation of the pipeline on
Linux/macOS/WSL. For a condensed version see `QUICKSTART.md`; for a
containerized install see `Docker.md`.

## 1. Prerequisites

| Tool     | Minimum version | Required? |
|----------|-----------------|-----------|
| Python   | 3.10             | Yes (unless using Docker) |
| pip      | 23+              | Yes (pip install path) |
| Conda / Miniconda | 23+     | Optional (Conda install path) |
| Docker   | 24+              | Optional (containerized install) |
| Git      | 2.30+            | Yes, to clone the repository |

Verify what you have:

```bash
python3 --version
pip --version
docker --version   # optional
conda --version    # optional
```

You can also run the bundled checker, which validates all of the above and
that required project files are present:

```bash
bash validations/validate_environment.sh
```

## 2. Clone the repository

```bash
git clone <your-fork-url> rat-connectome-analysis
cd rat-connectome-analysis
```

## 3. Install dependencies

### Option A — pip + virtualenv (recommended for development)

```bash
./scripts/setup_env.sh          # creates .venv/ and installs requirements.txt
source .venv/bin/activate
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Option B — Conda

```bash
conda env create -f environment.yml
conda activate rat-connectome-analysis
```

To update an existing environment after `environment.yml` changes:

```bash
conda env update -f environment.yml --prune
```

### Option C — Docker (no local Python required)

See `Docker.md` for the full containerized workflow.

## 4. Configure your data location

Open `config/config.json` and set:

- `data.base_path`: directory containing one subfolder per
  rat/repetition (e.g. `data/raw`).
- `data.groups`: mapping of group name → list of rat IDs.
- `data.n_repetitions`: number of repeated acquisitions per rat.
- `data.folder_pattern` / `data.file_pattern`: naming conventions for your
  files, if different from the default `th-0.0_<rat_id>_{w,d}.txt`.

## 5. Validate the setup

```bash
python scripts/validate_setup.py --config config/config.json
```

This checks the configuration schema and reports (without failing hard)
any rat/repetition files that cannot be found, so you can catch data-path
typos before a long run.

## 6. Run the pipeline

```bash
./scripts/run_pipeline.sh
```

or directly:

```bash
python scripts/run_analysis.py --config config/config.json
```

## 7. Run the test suite

```bash
pytest validations/ -v --cov=source
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ConfigurationError: Missing required configuration key` | `config.json` edited incorrectly | Compare against `config/config.json` in this repo; every key under "Required keys" in `docs/api.md` must be present. |
| `DataLoadError: No repetitions could be loaded for rat 'RXX'` | Wrong `base_path` or file naming pattern | Run `scripts/validate_setup.py` to see exactly which paths were checked. |
| Matplotlib errors about display/`$DISPLAY` | Running with a GUI backend in a headless environment | The pipeline already forces `matplotlib.use("Agg")`; ensure you're calling `source.analysis.group_pipeline`, not importing matplotlib yourself first. |
| `ModuleNotFoundError: No module named 'source'` | Running a script from a different working directory | Run from the project root, or use `scripts/run_pipeline.sh` which `cd`s there automatically. |
