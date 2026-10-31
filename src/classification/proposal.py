"""Adapt documented rule, prompt and legacy results for pipeline composition."""

from collections.abc import Mapping
from typing import Any, TypedDict


class ClassificationPlan(TypedDict):
    labels: list[str]
    archive: bool
    medical: bool
    finance: bool


def plan_classification(result: Mapping[str, Any]) -> ClassificationPlan:
    """Consume canonical labels/archive with explicit legacy compatibility.

    Sender decisions use labels; the bundled LLM prompt uses sub_labels.
    Older callers may use label/category/action. An explicit archive bool wins
    over the legacy action. Domain dispatch follows complete taxonomy segments,
    with the former category vocabulary retained for legacy callers.
    """
    labels = result.get(
        "labels", result.get("sub_labels", [result.get("label", "BC/misc/unclassified")])
    )
    if (
        not isinstance(labels, list)
        or not labels
        or any(not isinstance(label, str) or not label.strip() for label in labels)
    ):
        raise ValueError("classification labels must be a nonempty list of nonblank strings")
    labels = list(dict.fromkeys(labels))
    archive = result.get("archive", result.get("action") == "archive")
    if not isinstance(archive, bool):
        raise TypeError("classification archive must be a boolean")

    def has_branch(branch: str) -> bool:
        return any(label == branch or label.startswith(branch + "/") for label in labels)

    return {
        "labels": labels,
        "archive": archive,
        "medical": has_branch("BC/Records/Medical")
        or result.get("category") in ("medical", "reimbursement"),
        "finance": has_branch("BC/Records/Finance")
        or "BC/Records/Career/Payslip" in labels
        or result.get("category") in ("finance", "banking", "investment"),
    }
