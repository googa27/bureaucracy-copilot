"""Append-only audit helpers with redacted payloads."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .redaction import redact_mapping


def append_audit_event(event: dict[str, Any], audit_path: str | Path | None = None) -> dict[str, Any]:
    """Return and optionally append a redacted audit event as NDJSON."""
    safe_event = redact_mapping(
        {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            **event,
        }
    )
    if audit_path is not None:
        path = Path(audit_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(safe_event, sort_keys=True, ensure_ascii=False) + "\n")
    return safe_event
