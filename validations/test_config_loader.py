from __future__ import annotations

import json
from pathlib import Path

import pytest

from source.utils.config_loader import load_config, validate_config
from source.utils.exceptions import ConfigurationError


def _minimal_valid_config() -> dict:
    return {
        "data": {
            "base_path": "data/raw",
            "groups": {"control": ["R01"]},
            "n_repetitions": 2,
            "folder_pattern": "{rat_id}_r{rep}",
            "file_pattern": {"weight": "th-0.0_{rat_id}_w.txt", "distance": "th-0.0_{rat_id}_d.txt"},
        },
        "preprocessing": {"fictitious_nodes": [0]},
        "analysis": {"occurrence_thresholds": [1, 2], "cv_threshold": 0.2},
        "output": {"results_dir": "results"},
        "logging": {"log_dir": "logs"},
    }


def test_validate_config_accepts_minimal_valid_config():
    validate_config(_minimal_valid_config())  # should not raise


def test_validate_config_rejects_missing_key():
    config = _minimal_valid_config()
    del config["analysis"]["cv_threshold"]
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_validate_config_rejects_empty_groups():
    config = _minimal_valid_config()
    config["data"]["groups"] = {}
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_validate_config_rejects_bad_n_repetitions():
    config = _minimal_valid_config()
    config["data"]["n_repetitions"] = 0
    with pytest.raises(ConfigurationError):
        validate_config(config)


def test_load_config_missing_file(tmp_path: Path):
    with pytest.raises(ConfigurationError):
        load_config(tmp_path / "does_not_exist.json")


def test_load_config_invalid_json(tmp_path: Path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json")
    with pytest.raises(ConfigurationError):
        load_config(bad_file)


def test_load_config_valid_roundtrip(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(_minimal_valid_config()))
    config = load_config(config_file)
    assert config["data"]["groups"] == {"control": ["R01"]}
