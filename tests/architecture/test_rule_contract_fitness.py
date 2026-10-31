"""Rule contract stays packaged, documented and tied to public schema."""

import json
from pathlib import Path

from src.utils.rule_contracts import SENDER

ROOT = Path(__file__).resolve().parents[2]


def test_sender_contract_tracks_public_schema():
    expected = json.loads((ROOT / "schemas/sender_rule.schema.json").read_text())
    for key in ("rule_id", "pattern"):
        expected["properties"][key]["minLength"] = 1
    expected["properties"]["labels"]["items"]["minLength"] = 1
    assert SENDER == expected


def test_rule_contract_architecture_and_docs():
    contract = json.loads((ROOT / "docs/ARCHITECTURE.yaml").read_text())
    rules = contract["tests"]["rule_contracts"]
    assert rules["reference"] == "docs/rule-contracts.md"
    assert rules["providers"] is False
    text = (ROOT / rules["reference"]).read_text()
    for name in (
        "classify_by_rules",
        "classify_finance_email",
        "propose_route",
        "load_rule_document",
    ):
        assert name in text
