"""Expected contract input failures are diagnostics; defects retain their traceback."""

import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def policy():
    path = Path(__file__).resolve().parents[2] / "scripts/check_ai_hierarchy_policy.py"
    spec = importlib.util.spec_from_file_location("quality_policy", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("error_type", [RuntimeError, TypeError, ValueError, MemoryError])
def test_policy_validation_defects_propagate(policy, monkeypatch, error_type):
    error = error_type("synthetic validation defect")

    def fail(contract):
        raise error

    monkeypatch.setattr(policy, "validate", fail)
    with pytest.raises(error_type) as caught:
        policy.main()
    assert caught.value is error


@pytest.mark.parametrize("contents", ["[unterminated", "[]"])
def test_bad_contract_input_is_a_failed_diagnostic(policy, monkeypatch, tmp_path, capsys, contents):
    path = tmp_path / "contract.yaml"
    path.write_text(contents)
    monkeypatch.setattr(policy, "CONTRACT", path)
    assert policy.main() == 1
    assert "AI/hierarchy policy FAILED" in capsys.readouterr().out


def test_missing_contract_is_a_failed_diagnostic(policy, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(policy, "CONTRACT", tmp_path / "absent.yaml")
    assert policy.main() == 1
    assert "FileNotFoundError" in capsys.readouterr().out
