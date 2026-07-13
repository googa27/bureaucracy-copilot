"""Redaction helpers for audit-safe previews and notebook DTOs."""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
TOKEN_RE = re.compile(r"(?i)(api[_-]?key|token|secret|authorization|password)\s*[:=]\s*[^\s,;]+")
SENSITIVE_KEYS = {
    "authorization",
    "body",
    "case_id",
    "email",
    "from",
    "id",
    "message",
    "message_id",
    "phone",
    "raw",
    "description",
    "label",
    "label_name",
    "subject",
    "summary",
    "secret",
    "text",
    "thread_id",
    "to",
    "token",
}


def redact_text(value: str, placeholder: str = "[REDACTED]") -> str:
    """Remove common personal identifiers and credentials from free text."""
    redacted = EMAIL_RE.sub(placeholder, value)
    redacted = PHONE_RE.sub(placeholder, redacted)
    redacted = TOKEN_RE.sub(lambda match: f"{match.group(1)}={placeholder}", redacted)
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, Mapping):
        return redact_mapping(value)
    return value


def redact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return an audit-safe shallow/deep copy of a mapping."""
    result: dict[str, Any] = {}
    for key, value in payload.items():
        normalized = key.lower().replace("-", "_")
        if normalized in SENSITIVE_KEYS or normalized.endswith(("_token", "_secret", "_key")):
            result[key] = "[REDACTED]"
        else:
            result[key] = redact_value(value)
    return result
