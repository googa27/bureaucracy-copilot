"""Public-synthetic controls for rule matching and strict JSON proposal values."""

import json
import math

import pytest
import yaml
from jsonschema import ValidationError

from src.classification import classifier
from src.medical import case_tracker
from src.utils.resources import default_resource
from src.utils.rule_contracts import load_rule_document, matches


def edited_default(tmp_path, kind, path, value):
    document = yaml.safe_load(default_resource(f"rules/{kind}.yaml").read_text())
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    resource = tmp_path / f"{kind}.yaml"
    resource.write_text(yaml.safe_dump(document), encoding="utf-8")
    return resource


PATTERN_LOCATIONS = [
    ("gmail_sender_rules", ["rules", 0, "pattern"]),
    ("finance_classification", ["classification_rules", 0, "patterns", 0, "sender_domain"]),
    ("medical_routes", ["routes", 0, "pattern"]),
]


@pytest.mark.parametrize("kind,path", PATTERN_LOCATIONS)
@pytest.mark.parametrize(
    "pattern", ["invoice|", "|invoice", "invoice||salary", "invoice| \t", " \n"]
)
def test_rule_loader_rejects_empty_literal_alternatives(tmp_path, kind, path, pattern):
    resource = edited_default(tmp_path, kind, path, pattern)
    with pytest.raises(ValidationError):
        load_rule_document(resource, kind)


@pytest.mark.parametrize(
    "kind", ["domain", "sender_domain", "email", "sender_name", "subject_keyword", "keyword"]
)
def test_direct_matching_refuses_an_empty_alternative_instead_of_matching_every_email(kind):
    with pytest.raises(ValidationError):
        matches(kind, "invoice|", {})


@pytest.mark.parametrize(
    "payload,expected",
    [({}, False), ({"subject": "INVOICE"}, True), ({"subject": "salary"}, True)],
)
def test_valid_keyword_alternatives_keep_literal_matching(payload, expected):
    assert matches("subject_keyword", "invoice|salary", payload) is expected


NUMBER_LOCATIONS = [
    ("gmail_sender_rules", ["rules", 0, "confidence_boost"]),
    ("medical_routes", ["routes", 0, "confidence"]),
    ("finance_classification", ["confidence_thresholds", "high"]),
    (
        "summary_rules",
        [
            "weekly_hygiene_summary",
            "sections",
            "unsubscribe_suggestions",
            "min_open_rate_threshold",
        ],
    ),
]


@pytest.mark.parametrize("kind,path", NUMBER_LOCATIONS)
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_rule_loader_refuses_nonfinite_confidence_and_rate_values(tmp_path, kind, path, value):
    resource = edited_default(tmp_path, kind, path, value)
    with pytest.raises(ValidationError):
        load_rule_document(resource, kind)


@pytest.mark.parametrize("kind,path", NUMBER_LOCATIONS)
@pytest.mark.parametrize("value", [0.0, 0.25, 1.0])
def test_finite_confidence_endpoints_and_interior_values_remain_strict_json(
    tmp_path, kind, path, value
):
    document = load_rule_document(edited_default(tmp_path, kind, path, value), kind)
    target = document
    for key in path:
        target = target[key]
    assert target == value
    json.dumps(document, allow_nan=False)


@pytest.mark.parametrize("value", [float("nan"), 0.0, 0.25, 1.0])
@pytest.mark.parametrize("kind", ["gmail_sender_rules", "medical_routes"])
def test_real_proposals_refuse_nan_and_preserve_finite_confidence(
    tmp_path, monkeypatch, kind, value
):
    if kind == "gmail_sender_rules":
        resource = edited_default(tmp_path, kind, ["rules", 0, "confidence_boost"], value)
        monkeypatch.setattr(classifier, "RULES_PATH", resource)
        monkeypatch.setattr(classifier, "_rules", None)
        propose = classifier.classify_by_rules
    else:
        resource = edited_default(tmp_path, kind, ["routes", 0, "confidence"], value)
        monkeypatch.setattr(case_tracker, "ROUTES_PATH", resource)
        monkeypatch.setattr(case_tracker, "_route_rules", None)
        propose = case_tracker.propose_route
    if math.isnan(value):
        with pytest.raises(ValidationError):
            propose({"from": "synthetic@esencial.cl"})
    else:
        proposal = propose({"from": "synthetic@esencial.cl"})
        assert proposal["confidence"] == value
        json.dumps(proposal, allow_nan=False)
