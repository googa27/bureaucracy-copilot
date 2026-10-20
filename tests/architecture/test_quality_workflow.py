"""Check executable workflow steps, rather than commands mentioned in comments."""

import shlex
from pathlib import Path

import yaml


def test_locked_python312_job_runs_complete_ruff_gates_after_install():
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / ".github/workflows/portfolio-architecture.yml").read_text())
    steps = workflow["jobs"]["architecture-contract"]["steps"]
    assert any(step.get("with", {}).get("python-version") == "3.12" for step in steps)
    commands = [
        (index, shlex.split(line, comments=True))
        for index, step in enumerate(steps)
        for line in step.get("run", "").splitlines()
        if shlex.split(line, comments=True)
    ]
    install = next(
        index
        for index, argv in commands
        if argv
        == [
            "python",
            "-m",
            "pip",
            "install",
            "--require-hashes",
            "--only-binary=:all:",
            "-r",
            "requirements-impact.lock",
        ]
    )
    for gate in (
        ["python", "-m", "ruff", "check", "."],
        ["python", "-m", "ruff", "format", "--check", "."],
    ):
        assert any(index > install and argv == gate for index, argv in commands), gate
    for step in steps:
        if "run" in step and "ruff" in step["run"]:
            assert step.get("continue-on-error", False) is False
            assert "if" not in step
