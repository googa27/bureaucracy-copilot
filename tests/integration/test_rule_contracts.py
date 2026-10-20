"""Synthetic witnesses for the declared defaults, without provider or state access."""

import copy

import pytest
import yaml
from jsonschema import ValidationError

from src.classification import classifier
from src.finance import event_extractor
from src.medical import case_tracker
from src.utils.resources import default_resource


@pytest.fixture(autouse=True)
def isolated_caches(monkeypatch):
    monkeypatch.setattr(classifier, "_rules", None)
    monkeypatch.setattr(event_extractor, "_rules", None)
    monkeypatch.setattr(case_tracker, "_route_rules", None)


def raw(name):
    return yaml.safe_load(default_resource("rules/" + name + ".yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("rule", raw("gmail_sender_rules")["rules"], ids=lambda r: r["rule_id"])
def test_every_sender_default(rule):
    payload = (
        {"from": "user@" + rule["pattern"]}
        if rule["pattern_type"] == "domain"
        else {"subject": rule["pattern"]}
    )
    result = classifier.classify_by_rules(payload)
    assert result is not None
    assert result["labels"] == rule["labels"]
    assert result["archive"] == rule["archive"]
    assert result["classification"] == rule["classification"]
    assert result["rule"] == rule


@pytest.mark.parametrize(
    "rule", raw("finance_classification")["classification_rules"], ids=lambda r: r["source"]
)
def test_every_finance_default(rule):
    domain = next(p["sender_domain"] for p in rule["patterns"] if "sender_domain" in p)
    result = event_extractor.classify_finance_email(
        {"from": "Synthetic <x@" + domain.upper() + ">"}
    )
    assert result is not None
    assert result["rule"] == rule
    assert result["account"] == rule["account_source"]
    assert result["category"] == rule.get("category")
    assert result["event_type"] == rule["event_type"]


@pytest.mark.parametrize(
    "payload,route",
    [
        ({"from": "x@esencial.cl"}, "esencial"),
        ({"body": "ISAPRE"}, "esencial"),
        ({"subject": "bonificación"}, "esencial"),
        ({"from": "x@bicevida.cl"}, "bicevida"),
        ({"subject": "BICE VIDA"}, "bicevida"),
        ({"body": "complementaria"}, "bicevida"),
        ({"from": "x@alemana.cl"}, "alemana"),
        ({"subject": "Clínica Alemana"}, "alemana"),
        ({"subject": "isapre y seguro complementario"}, "combined"),
        ({}, "unknown"),
        ({"body": "dental medication consultation"}, "unknown"),
    ],
)
def test_medical_routes(payload, route):
    assert case_tracker.infer_insurer(payload) == route


@pytest.mark.parametrize(
    "sender",
    [
        "tenpo.cl <x@evil.invalid>",
        "x@tenpo.cl.evil.invalid",
        "x@eviltenpo.cl",
        "tenpo.cl@evil.invalid",
        "x@sub.tenpo.cl",
    ],
)
def test_sender_boundaries(sender):
    assert classifier.classify_by_rules({"from": sender}) is None
    assert event_extractor.classify_finance_email({"from": sender}) is None


def test_priority_and_keywords():
    assert (
        classifier.classify_by_rules({"from": "X@LINKEDIN.COM", "subject": "AFP"})["matched_rule"]
        == "afp_01"
    )
    assert classifier.classify_by_rules({"body": "AFP"}) is None
    assert (
        event_extractor.classify_finance_email({"subject": "LIQUIDACION"})["source"] == "previred"
    )
    assert event_extractor.classify_finance_email({"body": "tenpo"}) is None
    assert (
        event_extractor.classify_finance_email({"from": "x@bice.cl", "subject": "spotify"})[
            "source"
        ]
        == "bice_bank"
    )
    assert case_tracker.infer_insurer({"from": "alemana.cl <x@evil.invalid>"}) == "unknown"


@pytest.mark.parametrize(
    "name", ["gmail_sender_rules", "finance_classification", "medical_routes", "summary_rules"]
)
def test_validated_defaults(name):
    from src.utils.rule_contracts import load_rule_document

    assert load_rule_document(default_resource("rules/" + name + ".yaml"), name) == raw(name)


@pytest.mark.parametrize(
    "name", ["gmail_sender_rules", "finance_classification", "medical_routes", "summary_rules"]
)
def test_refuse_unknown_fields(name, tmp_path):
    from src.utils.rule_contracts import load_rule_document

    data = raw(name)
    data["typo"] = True
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValidationError):
        load_rule_document(path, name)


def test_validation_and_unexpected_errors(tmp_path, monkeypatch):
    from src.utils import rule_contracts

    data = copy.deepcopy(raw("gmail_sender_rules"))
    data["rules"][0]["labels"] = []
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValidationError):
        rule_contracts.load_rule_document(path, "gmail_sender_rules")

    def broken(*args, **kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(rule_contracts.yaml, "safe_load", broken)
    with pytest.raises(RuntimeError, match="unexpected"):
        rule_contracts.load_rule_document(path, "gmail_sender_rules")


@pytest.mark.parametrize(
    "kind,path,value",
    [
        ("gmail_sender_rules", ["rules", 0, "archive"], "yes"),
        ("finance_classification", ["classification_rules", 0, "event_type"], "invented_event"),
        ("finance_classification", ["classification_rules", 0, "category"], "invented_category"),
        (
            "finance_classification",
            ["classification_rules", 0, "patterns"],
            [{"domain": "tenpo.cl"}],
        ),
        ("medical_routes", ["routes", 0, "confidence"], 2),
        ("summary_rules", ["weekly_hygiene_summary", "sections", "inbox_state"], {"enabled": True}),
    ],
)
def test_nested_shape_refusals(kind, path, value, tmp_path):
    from src.utils.rule_contracts import load_rule_document

    data = raw(kind)
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    file = tmp_path / "invalid.yaml"
    file.write_text(yaml.safe_dump(data))
    with pytest.raises(ValidationError):
        load_rule_document(file, kind)


@pytest.mark.parametrize("text", ["null", "[]", "rules: []", "rules: [", "!!python/object:foo {}"])
def test_invalid_document_refusal(text, tmp_path):
    from src.utils.rule_contracts import load_rule_document

    path = tmp_path / "invalid.yaml"
    path.write_text(text)
    with pytest.raises((ValidationError, yaml.YAMLError)):
        load_rule_document(path, "gmail_sender_rules")


def test_medical_priority_and_metadata():
    result = case_tracker.propose_route({"from": "x@alemana.cl", "subject": "isapre"})
    assert result["route"] == "esencial"
    assert [s["route"] for s in result["signals"]] == ["esencial", "alemana"]
    combined = case_tracker.propose_route({"subject": "isapre bicevida"})
    assert combined["policy"]["combined_route"]["required_docs_additional"] == [
        "esencial_confirmation"
    ]
    combined["policy"]["routes"].clear()
    assert case_tracker.propose_route({"subject": "isapre"})["route"] == "esencial"


def test_unknown_finance_and_unknown_gmail():
    assert (
        event_extractor.classify_finance_email({"from": "x@unknown.invalid", "subject": "hello"})
        is None
    )
    assert classifier.classify_by_rules({"from": "x@unknown.invalid", "subject": "hello"}) is None
