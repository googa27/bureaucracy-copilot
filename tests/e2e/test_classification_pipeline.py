"""Synthetic CLI acceptance of real defaults and documented LLM/legacy proposals."""

from __future__ import annotations

import base64
import json
import sys
from types import SimpleNamespace

import pytest
import yaml

from src import main
from src.classification import classifier
from src.finance import event_extractor
from src.ingestion import auth, gmail_reader
from src.medical import case_tracker
from src.utils.resources import default_resource

SENDER_RULES = yaml.safe_load(
    default_resource("rules/gmail_sender_rules.yaml").read_text(encoding="utf-8")
)["rules"]
MEDICAL_RULES = {
    "esencial_01",
    "esencial_02",
    "bicevida_01",
    "bicevida_02",
    "alemana_01",
    "alemana_02",
    "integramedica_01",
    "bice_seguros_01",
}
FINANCE_RULES = {
    "tenpo_01",
    "bice_bank_01",
    "bice_inversiones_01",
    "mercadopago_01",
    "transbank_01",
    "previred_01",
    "afp_01",
    "spotify_01",
    "netflix_01",
    "github_01",
    "uber_01",
    "cabify_01",
}


class Call:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class Gmail:
    def __init__(self, email, labels):
        self.email = email
        self.labels_by_name = {name: f"label-{i}" for i, name in enumerate(labels)}
        self.modifications = []
        self.created_labels = []
        self.queries = []

    def users(self):
        return self

    def messages(self):
        return self

    def labels(self):
        return SimpleNamespace(list=self.list_labels, create=self.create)

    def list(self, **kwargs):
        self.queries.append(kwargs["q"])
        return Call({"messages": [{"id": "synthetic-message"}]})

    def list_labels(self, **kwargs):
        return Call({"labels": [{"name": k, "id": v} for k, v in self.labels_by_name.items()]})

    def get(self, **kwargs):
        return Call(
            {
                "id": "synthetic-message",
                "threadId": "synthetic-thread",
                "payload": {
                    "headers": [
                        {"name": k, "value": v} for k, v in self.email.items() if k != "body"
                    ],
                    "mimeType": "text/plain",
                    "body": {
                        "data": base64.urlsafe_b64encode(
                            self.email.get("body", "").encode()
                        ).decode()
                    },
                },
            }
        )

    def create(self, **kwargs):
        name = kwargs["body"]["name"]
        label_id = f"created-{len(self.created_labels)}"
        self.created_labels.append(name)
        self.labels_by_name[name] = label_id
        return Call({"id": label_id})

    def modify(self, **kwargs):
        self.modifications.append(kwargs["body"])
        return Call({"id": "synthetic-message"})


@pytest.fixture
def pipeline(monkeypatch, tmp_path):
    monkeypatch.setattr(classifier, "_rules", None)
    monkeypatch.setattr(event_extractor, "_rules", None)
    monkeypatch.setattr(case_tracker, "_route_rules", None)
    monkeypatch.setattr(case_tracker, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(event_extractor, "EVENTS_DIR", tmp_path / "events")
    llm_requests = []
    credentials_scopes = []

    def run(email, labels, response=None, mode="dry-run"):
        service = Gmail(email, labels)
        run.gmail = service

        def llm_create(**kwargs):
            llm_requests.append(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(text=json.dumps(response or {}))])

        client = SimpleNamespace(messages=SimpleNamespace(create=llm_create))
        monkeypatch.setattr(main, "load_config", dict)
        monkeypatch.setattr(main, "build_anthropic_client", lambda cfg: client)
        monkeypatch.setattr(gmail_reader, "build_service", lambda creds: service)
        monkeypatch.setattr(
            auth, "get_credentials", lambda *, scopes: credentials_scopes.append(scopes)
        )
        argv = ["bureaucracy-copilot", "--run", "classify", "--audit-log", str(tmp_path / "audit")]
        if mode == "approved":
            argv += [
                "--approve-mutations",
                "--approved-by",
                "synthetic-tester",
                "--approval-reason",
                "synthetic test",
            ]
        monkeypatch.setattr(sys, "argv", argv)
        main.main()
        audit = [json.loads(line) for line in (tmp_path / "audit").read_text().splitlines()]
        return SimpleNamespace(
            gmail=service,
            audit=audit,
            llm_requests=llm_requests,
            scopes=credentials_scopes,
            cases=[json.loads(p.read_text()) for p in (tmp_path / "cases").glob("*.json")],
            events=[json.loads(p.read_text()) for p in (tmp_path / "events").glob("*.json")],
        )

    return run


@pytest.mark.parametrize("rule", SENDER_RULES, ids=lambda r: r["rule_id"])
def test_cli_consumes_every_real_sender_rule(pipeline, rule, capsys):
    email = {"from": "Synthetic <x@unmatched.invalid>", "subject": "synthetic private subject"}
    if rule["pattern_type"] == "domain":
        email["from"] = f"Synthetic <x@{rule['pattern']}>"
    else:
        email["subject"] += " " + rule["pattern"]
    result = pipeline(email, rule["labels"])
    outcomes = [e["mutation"] for e in result.audit if e["event"] == "mutation.outcome"]
    applied_labels = [m for m in outcomes if m["proposal"]["action"] == "gmail.apply_label"]
    assert [m["proposal"]["payload"]["label_ids"] for m in applied_labels] == [
        [result.gmail.labels_by_name[name]] for name in rule["labels"]
    ]
    assert sum(m["proposal"]["action"] == "gmail.archive_message" for m in outcomes) == int(
        rule["archive"]
    )
    assert all(m["status"] == "planned" for m in outcomes)
    assert result.gmail.modifications == result.gmail.created_labels == []
    assert result.scopes == [auth.READONLY_SCOPES]
    assert len(result.cases) == int(rule["rule_id"] in MEDICAL_RULES)
    assert len(result.events) == int(rule["rule_id"] in FINANCE_RULES)
    assert len(result.llm_requests) == len(result.cases)
    preview = capsys.readouterr().out + json.dumps(result.audit)
    assert email["subject"] not in preview
    assert email["from"] not in preview
    assert "synthetic-message" not in preview
    assert all(label not in preview for label in rule["labels"])


@pytest.mark.parametrize("mode", ["dry-run", "approved"])
def test_cli_multiple_missing_labels_and_archive_stay_guarded(pipeline, mode):
    labels = ["BC/Records/Finance/Bank", "BC/Records/Career/Payslip"]
    result = pipeline({"from": "x@previred.com"}, [], mode=mode)
    if mode == "approved":
        assert result.gmail.created_labels == labels
        assert result.gmail.modifications == [
            {"addLabelIds": ["created-0"]},
            {"addLabelIds": ["created-1"]},
            {"removeLabelIds": ["INBOX"]},
        ]
        assert result.scopes == [(auth.GMAIL_MODIFY_SCOPE,)]
    else:
        assert result.gmail.created_labels == result.gmail.modifications == []
        assert result.scopes == [auth.READONLY_SCOPES]
    outcomes = [e["mutation"] for e in result.audit if e["event"] == "mutation.outcome"]
    assert sum(m["proposal"]["action"] == "gmail.create_label" for m in outcomes) == 2
    assert all(m["status"] == ("applied" if mode == "approved" else "planned") for m in outcomes)


@pytest.mark.parametrize(
    "sender", ["x@esencial.cl.evil.invalid", '"esencial.cl" <x@other.invalid>']
)
def test_cli_negative_sender_uses_legacy_llm_fallback(pipeline, sender):
    label = "BC/misc/unclassified"
    result = pipeline(
        {"from": sender}, [label], {"label": label, "category": "unknown", "action": "label"}
    )
    assert len(result.llm_requests) == 1
    assert not result.cases and not result.events
    assert [
        e["mutation"]["proposal"]["action"]
        for e in result.audit
        if e["event"] == "mutation.outcome"
    ] == ["gmail.apply_label"]


@pytest.mark.parametrize("key", ["labels", "sub_labels"])
def test_cli_canonical_llm_multiple_domains_and_archive_override(pipeline, key):
    labels = ["BC/Records/Medical/Invoice", "BC/Records/Finance/Receipt"]
    result = pipeline(
        {"from": "x@other.invalid"},
        labels,
        {
            key: labels,
            "classification": "Records",
            "archive": False,
            "action": "archive",
        },
    )
    outcomes = [
        e["mutation"]["proposal"]["action"]
        for e in result.audit
        if e["event"] == "mutation.outcome"
    ]
    assert outcomes == ["gmail.apply_label", "gmail.apply_label"]
    assert len(result.cases) == len(result.events) == 1


@pytest.mark.parametrize(
    "category", ["medical", "reimbursement", "finance", "banking", "investment"]
)
def test_cli_legacy_llm_category_and_archive_compatibility(pipeline, category):
    result = pipeline(
        {"from": "x@other.invalid"},
        ["BC/legacy"],
        {
            "label": "BC/legacy",
            "category": category,
            "action": "archive",
        },
    )
    assert len(result.cases) == int(category in ("medical", "reimbursement"))
    assert len(result.events) == int(category in ("finance", "banking", "investment"))
    assert any(e["mutation"]["proposal"]["action"] == "gmail.archive_message" for e in result.audit)


def test_cli_taxonomy_boundary_does_not_infer_domains_from_records_or_lookalikes(pipeline):
    labels = [
        "BC/Records/Medicalish/Invoice",
        "BC/Records/Financial/Receipt",
        "BC/Records/Career/PayslipExtra",
    ]
    result = pipeline(
        {"from": "x@other.invalid"},
        labels,
        {
            "classification": "Records",
            "sub_labels": labels,
            "archive": False,
        },
    )
    assert not result.cases and not result.events


@pytest.mark.parametrize(
    "sender,medical,finance",
    [
        ("x@esencial.cl", 1, 0),
        ("x@tenpo.cl", 0, 1),
        ("x@previred.com", 0, 1),
    ],
)
def test_cli_canonical_taxonomy_dispatches_local_domain_processing(
    pipeline, sender, medical, finance
):
    rule = next(r for r in SENDER_RULES if r["pattern"] == sender.split("@")[1])
    result = pipeline({"from": sender}, rule["labels"])
    assert (len(result.cases), len(result.events)) == (medical, finance)


@pytest.mark.parametrize(
    "bad",
    [
        {"labels": "BC/Records/Finance/Bank"},
        {"sub_labels": [None]},
        {"labels": []},
        {"label": " "},
        {"label": "BC/legacy", "archive": "false"},
    ],
)
def test_cli_invalid_proposal_fails_before_any_remote_mutation(pipeline, bad):
    with pytest.raises((ValueError, TypeError)):
        pipeline({"from": "x@other.invalid"}, [], bad, mode="approved")
    assert pipeline.gmail.created_labels == pipeline.gmail.modifications == []


def test_cli_prompt_archive_and_label_precedence(pipeline):
    label = "BC/Records/Career/Payslip"
    result = pipeline(
        {"from": "x@other.invalid"},
        [label],
        {
            "labels": [label, label],
            "sub_labels": ["BC/Pipeline/Jobs/Application"],
            "label": "BC/legacy",
            "classification": "Records",
            "archive": True,
        },
    )
    outcomes = [
        e["mutation"]["proposal"]["action"]
        for e in result.audit
        if e["event"] == "mutation.outcome"
    ]
    assert outcomes == ["gmail.apply_label", "gmail.archive_message"]
    assert len(result.events) == 1 and not result.cases


def test_cli_conflicting_sender_and_subject_retains_yaml_priority(pipeline):
    label = "BC/Records/Finance/Bank"
    result = pipeline({"from": "x@linkedin.com", "subject": "AFP"}, [label])
    assert not result.llm_requests and not result.cases and len(result.events) == 1
    assert any(e["mutation"]["proposal"]["action"] == "gmail.archive_message" for e in result.audit)
