"""Controlled execution wrappers for Gmail/Calendar side effects."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .approval import ApprovalPolicy
from .audit import append_audit_event
from .types import MutationProposal, MutationResult


class MutationGuard:
    """Plan, audit, and optionally apply external mutations.

    The guard is intentionally used at adapter boundaries. Every proposal writes an
    attempt/begin record before any side effect is evaluated, then writes an
    outcome record for planned/blocked/applied decisions or a failure record when
    the adapter raises.
    """

    def __init__(self, policy: ApprovalPolicy, audit_path: str | Path | None = None) -> None:
        self.policy = policy
        self.audit_path = audit_path

    def execute(
        self,
        proposal: MutationProposal,
        apply: Callable[[], Any] | None = None,
    ) -> MutationResult:
        decision = self.policy.evaluate(proposal)
        append_audit_event(
            {
                "event": "mutation.attempt",
                "phase": "begin",
                "mutation": decision.to_dict(),
            },
            self.audit_path,
        )

        if decision.status != "applied":
            append_audit_event(
                {
                    "event": "mutation.outcome",
                    "phase": "after",
                    "mutation": decision.to_dict(),
                },
                self.audit_path,
            )
            return decision

        if apply is None:
            blocked = MutationResult(
                proposal=proposal,
                status="blocked",
                reason="no mutation adapter supplied",
            )
            append_audit_event(
                {
                    "event": "mutation.outcome",
                    "phase": "after",
                    "mutation": blocked.to_dict(),
                },
                self.audit_path,
            )
            return blocked

        try:
            result = apply()
        except Exception as exc:
            failed = MutationResult(
                proposal=proposal,
                status="failed",
                reason=f"adapter failure: {exc.__class__.__name__}",
            )
            append_audit_event(
                {
                    "event": "mutation.failure",
                    "phase": "after",
                    "mutation": failed.to_dict(),
                    "error_type": exc.__class__.__name__,
                },
                self.audit_path,
            )
            raise

        applied = MutationResult(
            proposal=proposal,
            status="applied",
            reason=decision.reason,
            applied_reference=_reference(result),
        )
        append_audit_event(
            {
                "event": "mutation.outcome",
                "phase": "after",
                "mutation": applied.to_dict(),
            },
            self.audit_path,
        )
        return applied


def _reference(result: Any) -> str | None:
    if isinstance(result, dict):
        for key in ("id", "threadId", "htmlLink", "status"):
            if key in result:
                return str(result[key])
    return None
