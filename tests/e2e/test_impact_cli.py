"""Explicit synthetic CLI: machine-readable scope, never a provider route."""

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("statsmodels")
impact = importlib.import_module("examples.impact_evaluation.reminder_impact")


def test_capabilities_do_not_fit_or_write(tmp_path, monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("discovery must not generate data or fit")

    monkeypatch.setattr(impact, "simulate_rollout", forbidden)
    monkeypatch.chdir(tmp_path)
    assert impact.main(["--capabilities"]) == 0
    item = json.loads(capsys.readouterr().out)
    assert item["scope"] == "public_synthetic_only"
    assert item["raw_score_overlap"] is True
    assert item["estimated_weight_inference"] == "not_supplied"
    assert item["live_provider_calls"] is False
    assert list(tmp_path.iterdir()) == []


def test_actual_json_cli_labels_uncertainty_and_reports_clipping():
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "examples.impact_evaluation.reminder_impact",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        timeout=45,
        check=True,
    )
    data = json.loads(result.stdout)
    assert data["schema"] == "bureaucracy-copilot.impact-example.v1"
    assert data["scope"] == "public_synthetic_only"
    assert data["overlap"]["score_basis"] == "unclipped_fitted"
    assert isinstance(data["overlap"]["clipped_count"], int)
    weighted = next(row for row in data["estimates"] if row["method"].startswith("IPW"))
    assert (
        weighted["uncertainty_scope"] == "conditional_on_supplied_weights_no_first_stage_adjustment"
    )
    assert all(row["coverage_validated"] is False for row in data["estimates"])
