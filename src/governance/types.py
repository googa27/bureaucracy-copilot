"""Typed records for dry-run, approval, and audit decisions."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

Classification = Literal["public", "internal", "private", "restricted"]
MutationStatus = Literal["planned", "applied", "blocked", "failed"]


@dataclass(frozen=True)
class MutationProposal:
    """A human-reviewable external side-effect proposal."""

    action: str
    scope: str
    description: str
    payload: dict[str, Any] = field(default_factory=dict)
    required_scopes: tuple[str, ...] = ()
    classification: Classification = "private"
    proposal_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MutationResult:
    """Recorded outcome for a proposed mutation."""

    proposal: MutationProposal
    status: MutationStatus
    reason: str
    applied_reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["proposal"] = self.proposal.to_dict()
        return payload
