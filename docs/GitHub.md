# GitHub Setup & Contribution Guide

This document explains how to publish this project to GitHub and how to
work with it once it's there.

## 1. Publish this repository

```bash
cd rat-connectome-analysis

git init
git branch -M main
git add .

#git reset
#git rm --cached old_versions

git status

# Create an empty repository on GitHub first (via the web UI or `gh repo create`), then:
git remote add origin git@github.com:alep0/rat-connectome-analysis.git
git remote set-url origin git@github.com:alep0/rat-connectome-analysis.git
git remote -v
git commit -m "Initial commit: refactored rat connectome analysis pipeline"
git push -u origin main

ls -al ~/.ssh
ssh-keygen -t ed25519 -C "aaaguado@ifisc.uib-csic.es"

eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

cat ~/.ssh/id_ed25519.pub
ssh -T git@github.com

git clone https://github.com/alep0/rat-connectome-analysis.git

```

Using the GitHub CLI instead:

```bash
gh repo create <your-org>/rat-connectome-analysis --private --source=. --remote=origin --push
```

> **Before pushing:** double-check `.gitignore` excludes `data/raw/*` and
> `data/processed/*` — this pipeline is designed to never commit subject
> data to version control. Also replace the analysis rat IDs / paths in
> `config/config.json` with placeholders if the real ones are sensitive.

## 2. Repository settings to enable

- **Branch protection** on `main`: require the `CI` workflow (`lint`,
  `test`, `validate-config`, `docker` jobs) to pass before merging.
- **Secrets**: none are required for the default CI workflow. If you add
  steps that push Docker images to a registry, add registry credentials
  under *Settings → Secrets and variables → Actions*.
- **Issue/PR templates**: consider adding `.github/ISSUE_TEMPLATE/` and
  `.github/PULL_REQUEST_TEMPLATE.md` for your team's workflow.

## 3. Branching model

- `main` — always deployable; protected.
- `develop` (optional) — integration branch; CI also runs here.
- `feature/<short-description>` — one branch per change.
- `fix/<short-description>` — bug fixes.

```bash
git checkout -b feature/add-group-comparison-stats
# ... make changes ...
pytest validations/ -v
git commit -am "Add group-level comparison statistics"
git push -u origin feature/add-group-comparison-stats
```

Then open a pull request against `main` (or `develop`).

## 4. Continuous Integration

`.github/workflows/ci.yml` runs automatically on every push and pull
request to `main`/`develop`, with four jobs:

1. **lint** — `ruff check` + `black --check`.
2. **test** — `pytest` with coverage, on Python 3.10/3.11/3.12.
3. **validate-config** — schema-validates `config/config.json`.
4. **docker** — builds the Docker image and runs the test suite inside it.

All four must pass before merging if branch protection is enabled.

## 5. Local pre-commit checklist

Before pushing, run what CI will run:

```bash
ruff check source scripts validations
black --check source scripts validations
pytest validations/ -v --cov=source
python scripts/validate_setup.py --config config/config.json
docker build -t rat-connectome-analysis:local .
```

## 6. Releasing

Tag releases using semantic versioning:

```bash
git tag -a v1.0.0 -m "First stable release"
git push origin v1.0.0
```

Update `version` in `pyproject.toml` and `config/config.json`'s
`project.version` field to match.

## 7. Recommended repository metadata

- **Description**: "Consensus connectome construction and QA pipeline for
  rat structural-connectivity data across experimental groups."
- **Topics**: `neuroscience`, `connectomics`, `dti`, `python`, `docker`,
  `data-pipeline`, `reproducibility`.
- **License**: add a `LICENSE` file (MIT is referenced in `README.md`;
  swap for your institution's preferred license if different).
