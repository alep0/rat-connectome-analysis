# Rat Connectome Analysis

A robust, testable, containerized pipeline for building **consensus structural
connectomes** from repeated rat DTI/tractography acquisitions, and for
studying their **inter-subject consistency**, **coefficient of variation
(CV)**, and **outliers** — across two (or more) experimental groups.

This project is a full software-engineering refactor of an exploratory
Jupyter notebook (`1b_Analisis_Individuos_aag_t2_R02.ipynb`). The original
notebook analyzed a single, hard-coded rat; this pipeline generalizes the
same analysis to run automatically over **every rat in every configured
group**, with proper error handling, logging, configuration, tests, and
packaging.

## What it does

For every rat listed in `config/config.json`:

1. **Load** the weight (`W`) and distance (`D`) matrices for each repeated
   acquisition ("repetition"), tolerating missing files.
2. **Clean** the data: detect and report `NaN` values, remove self-connections,
   and drop known non-ROI ("fictitious") nodes (e.g. background, white
   matter, ventricles).
3. **Build a raw consensus connectome**: per-edge mean/std across
   repetitions, ignoring unobserved (zero) edges.
4. **Analyze inter-subject consistency**: how many repetitions each edge
   appears in, and survival curves under minimum-occurrence thresholds.
5. **Analyze the coefficient of variation (CV)** per edge, its relation to
   distance/weight/consistency, and its own survival curve.
6. **Detect outliers** with Tukey's IQR fences (configurable multiplier or a
   p-value-derived multiplier), and quantify how much outlier removal
   improves CV.
7. **Persist results**: per-rat CSV tables, consensus matrices (`.txt`), and
   PNG figures, plus a run-level summary CSV (`results/run_summary.csv`).

## Project layout

```
rat-connectome-analysis/
├── source/
│   ├── analysis/        # consistency, CV, outlier analyses + pipeline orchestration
│   ├── core/             # data loading, matrix cleaning, consensus building
│   └── utils/            # config loading, logging, validation, plotting
├── data/                 # raw/ and processed/ data (not committed, see .gitignore)
├── docs/                 # installation.md, api.md, GitHub.md, QUICKSTART.md, Docker.md
├── logs/                 # run.log (rotating)
├── validations/          # pytest test suite + bash environment validator
├── results/              # figures/, tables/, consensus/, run_summary.csv
├── config/               # config.json, logging_config.yaml
├── scripts/              # run_analysis.py, run_pipeline.sh, validate_setup.py, setup_env.sh
├── Dockerfile, docker-compose.yml
├── requirements.txt, environment.yml
└── .github/workflows/ci.yml
```

## Quick start

```bash
# 1. Clone and enter the project
git clone <your-fork-url> rat-connectome-analysis
cd rat-connectome-analysis

# 2. Set up the environment (pip or conda — see docs/QUICKSTART.md)
./scripts/setup_env.sh
source .venv/bin/activate

# 3. Point config/config.json at your data (see docs/installation.md)

# 4. Run the pipeline
./scripts/run_pipeline.sh
```

See **[docs/QUICKSTART.md](docs/QUICKSTART.md)** for the full walkthrough
(including the Conda option), **[docs/installation.md](docs/installation.md)**
for detailed setup, **[docs/Docker.md](docs/Docker.md)** for the containerized
workflow, and **[docs/api.md](docs/api.md)** for the module/function reference.

## Configuring your data

Edit `config/config.json`:

```json
"data": {
  "base_path": "data/raw",
  "groups": {
    "control":   ["R01", "R02", "R03"],
    "treatment": ["R06", "R07", "R08"]
  },
  "n_repetitions": 10
}
```

Raw data is expected under `data/raw/<rat_id>_r<rep>/th-0.0_<rat_id>_{w,d}.txt`
(configurable via `folder_pattern` / `file_pattern`).

## Running tests

```bash
pytest validations/ -v --cov=source
bash validations/validate_environment.sh
```

## License

MIT — see `LICENSE` (add your institution's license file before publishing).

## Citation / origin

Derived from the analysis notebook `1b_Analisis_Individuos_aag_t2_R02.ipynb`
(TFM: Análisis y Procesamiento de los Datos, M. Cerdán and A. Aguado).
