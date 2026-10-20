"""Every canonical default must be selected by the build configuration."""

import io
import subprocess
import sys
import tarfile
import tomllib
import warnings
import zipfile
from pathlib import Path

import pytest


def test_default_payloads_are_explicit_package_data():
    root = Path(__file__).resolve().parents[2]
    config = tomllib.loads((root / "pyproject.toml").read_text())
    declared = config["tool"]["setuptools"].get("package-data", {}).get("src.utils", [])
    expected = {
        "assets/prompts/classify_email.md",
        "assets/prompts/build_claim_case.md",
        "assets/prompts/draft_followup.md",
        "assets/prompts/summarize_weekly_hygiene.md",
        "assets/prompts/summarize_finance_monthly.md",
        "assets/rules/gmail_sender_rules.yaml",
        "assets/rules/medical_routes.yaml",
        "assets/rules/finance_classification.yaml",
        "assets/rules/summary_rules.yaml",
    }
    selected = {
        str(p.relative_to(root / "src/utils"))
        for pattern in declared
        for p in (root / "src/utils").glob(pattern)
        if p.is_file()
    }
    assert selected == expected


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize("damage", [None, "missing", "altered", "duplicate"])
def test_archive_gate_detects_payload_damage(tmp_path, kind, damage):
    """Archive damage must fail independently of successful source reads."""
    root = Path(__file__).resolve().parents[2]
    resources = sorted((root / "src/utils/assets").rglob("*"))
    payloads = [(str(p.relative_to(root)), p.read_bytes()) for p in resources if p.is_file()]
    if damage == "missing":
        payloads.pop()
    elif damage == "altered":
        payloads[0] = (payloads[0][0], b"changed")
    elif damage == "duplicate":
        payloads.append(payloads[0])
    archive = tmp_path / ("candidate.whl" if kind == "wheel" else "candidate.tar.gz")
    if kind == "wheel":
        with zipfile.ZipFile(archive, "w") as output:
            for name, data in payloads:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    output.writestr(name, data)
    else:
        with tarfile.open(archive, "w:gz") as output:
            for name, data in payloads:
                member = tarfile.TarInfo("candidate/" + name)
                member.size = len(data)
                output.addfile(member, io.BytesIO(data))
    result = subprocess.run(
        [sys.executable, "-B", str(root / "scripts/check_distribution_resources.py"), str(archive)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (result.returncode == 0) == (damage is None), result.stdout + result.stderr
    if damage:
        assert "payload" in result.stdout + result.stderr
