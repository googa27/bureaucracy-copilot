"""Approval policy for external mutations."""
from __future__ import annotations

from dataclasses import dataclass

from .types import MutationProposal, MutationResult


@dataclass(frozen=True)
class ApprovalPolicy:
    """Fail-closed policy: dry-run unless a human approves mutation mode."""

    dry_run: bool = True
    approved_by: str | None = None
    approval_reason: str | None = None

    def evaluate(self, proposal: MutationProposal) -> MutationResult:
        if self.dry_run:
            return MutationResult(
                proposal=proposal,
                status="planned",
                reason="dry-run mode: no external mutation executed",
            )
        if not self.approved_by or not self.approval_reason:
            return MutationResult(
                proposal=proposal,
                status="blocked",
                reason="mutation mode requires approved_by and approval_reason",
            )
        return MutationResult(
            proposal=proposal,
            status="applied",
            reason=f"approved by {self.approved_by}: {self.approval_reason}",
        )
