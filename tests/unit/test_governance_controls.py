from __future__ import annotations

import json

import pytest

from src.governance.approval import ApprovalPolicy
from src.governance.executor import MutationGuard
from src.governance.redaction import redact_mapping, redact_text
from src.governance.types import MutationProposal
from src.ingestion.gmail_reader import apply_label, archive_message, get_or_create_label


class ExecuteCall:
    def __init__(self, result: dict):
        self.result = result
        self.called = False

    def execute(self) -> dict:
        self.called = True
        return self.result


class FakeMessages:
    def __init__(self) -> None:
        self.modify_call: ExecuteCall | None = None

    def modify(self, **_kwargs) -> ExecuteCall:
        self.modify_call = ExecuteCall({"id": "msg-1"})
        return self.modify_call


class FakeLabels:
    def __init__(self, labels: list[dict] | None = None) -> None:
        self.labels = labels or []
        self.create_call: ExecuteCall | None = None

    def list(self, **_kwargs) -> ExecuteCall:
        return ExecuteCall({"labels": self.labels})

    def create(self, **_kwargs) -> ExecuteCall:
        self.create_call = ExecuteCall({"id": "label-1"})
        return self.create_call


class FakeUsers:
    def __init__(self, labels: list[dict] | None = None) -> None:
        self.messages_obj = FakeMessages()
        self.labels_obj = FakeLabels(labels)

    def messages(self) -> FakeMessages:
        return self.messages_obj

    def labels(self) -> FakeLabels:
        return self.labels_obj


class FakeGmail:
    def __init__(self, labels: list[dict] | None = None) -> None:
        self.users_obj = FakeUsers(labels)

    def users(self) -> FakeUsers:
        return self.users_obj


def test_redaction_removes_personal_identifiers_and_tokens() -> None:
    text = "Email a.person@example.com or +56 9 7563 2368 token=abc123"

    assert "example.com" not in redact_text(text)
    assert "+56" not in redact_text(text)
    assert "abc123" not in redact_text(text)


def test_redaction_replaces_sensitive_mapping_values() -> None:
    payload = {
        "subject": "hello",
        "label": "BC/private/bank",
        "description": "private calendar details",
        "from": "person@example.com",
        "message_id": "gmail-message-id",
        "nested": {"api_key": "secret"},
    }

    assert redact_mapping(payload) == {
        "subject": "[REDACTED]",
        "label": "[REDACTED]",
        "description": "[REDACTED]",
        "from": "[REDACTED]",
        "message_id": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]"},
    }


def test_mutation_guard_dry_run_does_not_call_adapter(tmp_path) -> None:
    called = False

    def apply() -> dict[str, str]:
        nonlocal called
        called = True
        return {"id": "remote-id"}

    guard = MutationGuard(ApprovalPolicy(dry_run=True), audit_path=tmp_path / "audit.ndjson")
    result = guard.execute(
        MutationProposal(action="gmail.archive", scope="gmail.modify", description="archive"),
        apply,
    )

    assert result.status == "planned"
    assert called is False
    events = [json.loads(line) for line in (tmp_path / "audit.ndjson").read_text().splitlines()]
    assert [event["event"] for event in events] == ["mutation.attempt", "mutation.outcome"]
    assert events[0]["mutation"]["status"] == "planned"


def test_mutation_guard_requires_human_approval_before_apply() -> None:
    guard = MutationGuard(ApprovalPolicy(dry_run=False))
    result = guard.execute(
        MutationProposal(action="gmail.label", scope="gmail.modify", description="label"),
        lambda: {"id": "remote-id"},
    )

    assert result.status == "blocked"


def test_mutation_guard_applies_after_approval() -> None:
    guard = MutationGuard(
        ApprovalPolicy(dry_run=False, approved_by="tester", approval_reason="unit test")
    )
    result = guard.execute(
        MutationProposal(action="gmail.label", scope="gmail.modify", description="label"),
        lambda: {"id": "remote-id"},
    )

    assert result.status == "applied"
    assert result.applied_reference == "remote-id"


def test_mutation_guard_audits_failures(tmp_path) -> None:
    guard = MutationGuard(
        ApprovalPolicy(dry_run=False, approved_by="tester", approval_reason="unit test"),
        audit_path=tmp_path / "audit.ndjson",
    )

    with pytest.raises(RuntimeError):
        guard.execute(
            MutationProposal(action="gmail.label", scope="gmail.modify", description="label"),
            lambda: (_ for _ in ()).throw(RuntimeError("boom private subject")),
        )

    events = [json.loads(line) for line in (tmp_path / "audit.ndjson").read_text().splitlines()]
    assert [event["event"] for event in events] == ["mutation.attempt", "mutation.failure"]
    assert events[-1]["mutation"]["status"] == "failed"


def test_gmail_mutators_are_guarded_at_adapter_boundary(tmp_path) -> None:
    service = FakeGmail(labels=[{"name": "BC/private", "id": "label-1"}])
    guard = MutationGuard(ApprovalPolicy(dry_run=True), audit_path=tmp_path / "audit.ndjson")

    label_id = get_or_create_label(service, "BC/private", guard=guard)
    label_result = apply_label(
        service,
        "msg-1",
        [label_id or "label-1"],
        guard=guard,
        subject="Private bank subject",
        label_name="BC/private",
    )
    archive_result = archive_message(
        service,
        "msg-1",
        guard=guard,
        subject="Private bank subject",
    )

    assert label_id == "label-1"
    assert label_result.status == "planned"
    assert archive_result.status == "planned"
    assert service.users_obj.messages_obj.modify_call is None
    audit_text = (tmp_path / "audit.ndjson").read_text()
    assert "Private bank subject" not in audit_text
    assert "BC/private" not in audit_text


def test_create_label_requires_guard_and_dry_run_skips_remote_create(tmp_path) -> None:
    service = FakeGmail(labels=[])
    guard = MutationGuard(ApprovalPolicy(dry_run=True), audit_path=tmp_path / "audit.ndjson")

    label_id = get_or_create_label(service, "BC/private", guard=guard)

    assert label_id is None
    assert service.users_obj.labels_obj.create_call is None
    audit_text = (tmp_path / "audit.ndjson").read_text()
    assert "BC/private" not in audit_text
    assert "gmail.create_label" in audit_text
