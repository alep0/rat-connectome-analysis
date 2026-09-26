# Quickstart

Get the pipeline running in under five minutes.

## Option 1 — pip + virtualenv

```bash
git clone <your-fork-url> rat-connectome-analysis
cd rat-connectome-analysis

./scripts/setup_env.sh
source .venv/bin/activate

python scripts/validate_setup.py --config config/config.json
./scripts/run_pipeline.sh
```

## Option 2 — Conda

The pinned, up-to-date environment specification lives in
[`environment.yml`](../environment.yml) at the project root:

```yaml
name: rat-connectome-analysis
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - numpy>=1.26,<2.2
  - pandas>=2.1,<2.3
  - matplotlib>=3.8,<3.10
  - seaborn>=0.13,<0.14
  - scipy>=1.11,<1.15
  - networkx>=3.2,<3.4
  - tqdm>=4.66,<5.0
  - pyyaml>=6.0,<7.0
  - pytest>=8.0,<9.0
  - pytest-cov>=5.0,<6.0
  - pip
  - pip:
      - ruff>=0.6,<0.8
      - black>=24.0,<25.0
```

Create and activate it:

```bash
git clone <your-fork-url> rat-connectome-analysis
cd rat-connectome-analysis

conda env create -f config/environment.yml
conda activate rat-connectome-analysis

python scripts/validate_setup.py --config config/config.json
./scripts/run_pipeline.sh
```

To pick up changes after editing `environment.yml`:

```bash
conda env update -f environment.yml --prune
```

## Option 3 — Docker (no local Python/Conda needed)

```bash
git clone <your-fork-url> rat-connectome-analysis
cd rat-connectome-analysis

docker compose build
docker compose run --rm analysis
```

See [`Docker.md`](Docker.md) for volume mounts, running a single rat/group,
and running the test suite in the container.

## Point it at your data

Edit `config/config.json`:

```json
"data": {
  "base_path": "data/",
  "data_history": "FA_RN_SI_v0-1_th-0.0_N/filter_kick_out/",
  "groups": {
    "t1":   ["R01", "R02", "R03"],
    "t2": ["R06", "R07", "R08"]
  },
  "n_repetitions": 10
}
```

Expected on-disk layout (default pattern, configurable):

```
data/t1/FA_RN_SI_v0-1_th-0.0_N/filter_kick_out/
├── R01_r1/th-0.0_R01_w.txt
├── R01_r1/th-0.0_R01_d.txt
├── R01_r2/th-0.0_R01_w.txt
├── ...
└── R08_r10/th-0.0_R08_d.txt
```

## Run just one rat or one group

```bash
python scripts/run_analysis.py --config config/config.json --group t1
python scripts/run_analysis.py --config config/config.json --group t1 --rat R01
```

## Where results go

```
results/
├── run_summary.csv                       # one row per rat: success/failure
├── consensus/<group>/<rat_id>/*.txt      # mean/std weight, mean distance, occurrence
├── tables/<group>/<rat_id>/*.csv         # nan_report, survival_curve, cv_edges, outliers, ...
└── figures/<group>/<rat_id>/*.png        # heatmaps, survival curves, CV plots, outlier maps
```

## Run the tests

```bash
pytest validations/ -v --cov=source
bash validations/validate_environment.sh
```

## Next steps

- [`installation.md`](installation.md) — detailed setup & troubleshooting.
- [`api.md`](api.md) — module/function reference.
- [`Docker.md`](Docker.md) — containerized workflow.
- [`GitHub.md`](GitHub.md) — publishing and CI.

## Run all rats and groups

```bash

# 4. Run the pipeline
./scripts/run_pipeline.sh
bash scripts/run_pipeline.sh --config config/config.json

bash scripts/run_pipeline.sh --config config/config_tau.json

```
