"""Strict, pure YAML rule loading and matching; no provider or persistence access."""

import json
from collections.abc import Mapping
from email.utils import parseaddr
from typing import Any, Protocol, TypedDict

import yaml
from jsonschema import Draft7Validator, ValidationError


class TextResource(Protocol):
    """Path and importlib Traversable read contract."""

    def read_text(self, encoding: str = "utf-8") -> str: ...


class RuleDecision(TypedDict):
    """Shared proposal evidence; rule is a complete independent metadata copy."""

    rule: dict[str, Any]
    confidence: float
    method: str


def obj(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties) if required is None else required,
        "additionalProperties": False,
    }


def array(items: dict) -> dict:
    return {"type": "array", "items": items, "minItems": 1}


STR = {"type": "string", "minLength": 1}
BOOL = {"type": "boolean"}
NUM = {"type": "number", "minimum": 0, "maximum": 1}
INT = {"type": "integer", "minimum": 0}
STRINGS = array(STR)
SENDER = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://github.com/googa27/bureaucracy-copilot/schemas/sender_rule.schema.json",
    "title": "SenderRule",
    "description": "A rule mapping email sender patterns to classification labels",
    "type": "object",
    "required": ["rule_id", "pattern_type", "pattern", "labels"],
    "properties": {
        "rule_id": {"type": "string", "description": "Unique rule identifier"},
        "pattern_type": {
            "type": "string",
            "enum": ["domain", "email", "subject_keyword", "sender_name"],
            "description": "Type of pattern to match",
        },
        "pattern": {
            "type": "string",
            "description": "The pattern to match (domain, email address, keyword, or name substring)",
        },
        "labels": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "description": "Gmail label paths to apply (e.g. BC/Records/Medical/Invoice)",
        },
        "classification": {
            "type": ["string", "null"],
            "enum": ["Action", "Pipeline", "Records", "Waiting", "Feeds", None],
            "description": "Top-level classification to assign",
        },
        "archive": {
            "type": "boolean",
            "default": False,
            "description": "Whether to archive immediately after labeling",
        },
        "confidence_boost": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "default": 0.9,
            "description": "Confidence level when this rule matches",
        },
        "notes": {
            "type": ["string", "null"],
            "description": "Human-readable explanation of the rule",
        },
        "active": {
            "type": "boolean",
            "default": True,
            "description": "Whether this rule is enabled",
        },
    },
    "additionalProperties": False,
}
# Same public sender schema, strengthened only for empty matching identifiers.
for _key in ("rule_id", "pattern"):
    SENDER["properties"][_key]["minLength"] = 1
SENDER["properties"]["labels"]["items"]["minLength"] = 1
PATTERN = {"oneOf": [obj({"sender_domain": STR}), obj({"subject_keyword": STR})]}
EXTRACTION = obj(
    {
        "amount_regex": STR,
        "direction_signals": obj({"in": STRINGS, "out": STRINGS}),
        "direction": {"enum": ["in", "out"]},
        "counterparty_field": STR,
        "counterparty": STR,
    },
    ["amount_regex"],
)
FINANCE_RULE = obj(
    {
        "source": STR,
        "patterns": array(PATTERN),
        "event_type": {
            "enum": [
                "bank_transfer",
                "payment",
                "investment_purchase",
                "investment_dividend",
                "subscription",
                "salary",
                "receipt",
                "reimbursement",
                "club_dues",
                "transport",
                "other",
            ]
        },
        "account_source": {"enum": ["tenpo", "bice", "bice_inversiones", "other"]},
        "category": {
            "enum": [
                "medical",
                "transport",
                "subscription",
                "investment",
                "salary",
                "food",
                "housing",
                "admin",
                "other",
                None,
            ]
        },
        "extraction": EXTRACTION,
        "archive": BOOL,
        "label": STR,
    },
    ["source", "patterns", "event_type", "account_source", "extraction", "archive", "label"],
)
ROUTE = obj(
    {
        "signal": STR,
        "description": STR,
        "pattern_type": {"enum": ["sender_domain", "keyword"]},
        "pattern": STR,
        "route": {"enum": ["esencial", "bicevida", "alemana"]},
        "confidence": NUM,
    }
)
MODIFIER = obj(
    {"expense_type": STR, "default_route": STR, "required_docs": STRINGS, "notes": STR},
    ["expense_type", "notes"],
)
SECTION = obj(
    {
        "enabled": BOOL,
        "show_counts_by_label": BOOL,
        "highlight_action_items": BOOL,
        "show_all_open_cases": BOOL,
        "highlight_overdue": BOOL,
        "overdue_threshold_days": INT,
        "waiting_stale_days": INT,
        "submitted_stale_days": INT,
        "pending_stale_days": INT,
        "max_suggestions": INT,
        "priority_order": STRINGS,
        "min_emails_in_period": INT,
        "min_open_rate_threshold": NUM,
        "period_days": INT,
        "show_net": BOOL,
        "show_in_out": BOOL,
        "categories": STRINGS,
        "flag_if_amount_changed": BOOL,
        "flag_if_unused": BOOL,
        "known_benefits": array(obj({"name": STR, "frequency": STR, "estimated_value_clp": INT})),
    },
    ["enabled"],
)
SCHEDULE = {"cadence": STR, "time": STR, "timezone": STR}
SCHEMAS = {
    "gmail_sender_rules": obj({"rules": array(SENDER)}),
    "finance_classification": obj(
        {
            "classification_rules": array(FINANCE_RULE),
            "amount_normalization": obj(
                {
                    "description": STR,
                    "remove_chars": STRINGS,
                    "decimal_separator": STR,
                    "thousands_separator": STR,
                }
            ),
            "confidence_thresholds": obj(
                dict.fromkeys(["high", "medium", "low", "min_to_store"], NUM)
            ),
        }
    ),
    "medical_routes": obj(
        {
            "routes": array(ROUTE),
            "combined_route": obj(
                {
                    "description": STR,
                    "trigger": {"const": "both_esencial_and_bicevida_signals"},
                    "required_docs_additional": STRINGS,
                }
            ),
            "expense_type_modifiers": array(MODIFIER),
            "fallback": obj(
                {
                    "route": {"const": "unknown"},
                    "confidence": {"const": 0.0},
                    "action": {"const": "manual_review"},
                    "notes": STR,
                }
            ),
        }
    ),
    "summary_rules": obj(
        {
            "weekly_hygiene_summary": obj(
                {
                    **SCHEDULE,
                    "day_of_week": STR,
                    "sections": obj(
                        {
                            "inbox_state": obj(
                                {
                                    k: SECTION["properties"][k]
                                    for k in (
                                        "enabled",
                                        "show_counts_by_label",
                                        "highlight_action_items",
                                    )
                                }
                            ),
                            "reimbursement_queue": obj(
                                {
                                    k: SECTION["properties"][k]
                                    for k in (
                                        "enabled",
                                        "show_all_open_cases",
                                        "highlight_overdue",
                                        "overdue_threshold_days",
                                    )
                                }
                            ),
                            "stale_items": obj(
                                {
                                    k: SECTION["properties"][k]
                                    for k in (
                                        "enabled",
                                        "waiting_stale_days",
                                        "submitted_stale_days",
                                        "pending_stale_days",
                                    )
                                }
                            ),
                            "suggested_actions": obj(
                                {
                                    k: SECTION["properties"][k]
                                    for k in ("enabled", "max_suggestions", "priority_order")
                                }
                            ),
                            "unsubscribe_suggestions": obj(
                                {
                                    k: SECTION["properties"][k]
                                    for k in (
                                        "enabled",
                                        "min_emails_in_period",
                                        "min_open_rate_threshold",
                                        "period_days",
                                    )
                                }
                            ),
                        }
                    ),
                }
            ),
            "monthly_finance_digest": obj(
                {
                    **SCHEDULE,
                    "day_of_month": INT,
                    "sections": obj(
                        {
                            "summary_stats": obj(
                                {
                                    k: SECTION["properties"][k]
                                    for k in ("enabled", "show_net", "show_in_out")
                                }
                            ),
                            "by_category": obj(
                                {k: SECTION["properties"][k] for k in ("enabled", "categories")}
                            ),
                            "reimbursements_received": obj({"enabled": BOOL}),
                            "subscription_audit": obj(
                                {
                                    k: SECTION["properties"][k]
                                    for k in ("enabled", "flag_if_amount_changed", "flag_if_unused")
                                }
                            ),
                            "benefits_review": obj(
                                {k: SECTION["properties"][k] for k in ("enabled", "known_benefits")}
                            ),
                        }
                    ),
                }
            ),
            "reimbursement_queue_summary": obj(
                {"cadence": STR, "include_in_weekly": BOOL, "columns": STRINGS}
            ),
            "stale_case_alerting": obj(
                {
                    "enabled": BOOL,
                    "thresholds": obj(
                        dict.fromkeys(
                            [
                                "submitted_to_alert_days",
                                "pending_to_alert_days",
                                "new_unreviewed_days",
                            ],
                            INT,
                        )
                    ),
                    "alert_methods": STRINGS,
                }
            ),
            "sport_frances_handoff": obj(
                {
                    "cadence": STR,
                    "months": array({"type": "integer", "minimum": 1, "maximum": 12}),
                    "day_of_month": INT,
                    "content": STRINGS,
                }
            ),
        }
    ),
}


def load_rule_document(resource: TextResource, kind: str) -> dict[str, Any]:
    """Load exactly a named canonical shape; YAML/schema/I/O errors propagate.

    No legacy shape guessing or coercion. Metadata is retained in full.
    """
    schema = SCHEMAS[kind]
    Draft7Validator.check_schema(schema)
    document = yaml.safe_load(resource.read_text(encoding="utf-8"))
    Draft7Validator(schema).validate(document)
    if kind == "gmail_sender_rules":
        patterns = (rule["pattern"] for rule in document["rules"])
    elif kind == "finance_classification":
        patterns = (
            value
            for rule in document["classification_rules"]
            for pattern in rule["patterns"]
            for value in pattern.values()
        )
    elif kind == "medical_routes":
        patterns = (rule["pattern"] for rule in document["routes"])
    else:
        patterns = ()
    for pattern in patterns:
        _literal_alternatives(pattern)
    # YAML admits NaN, which does not obey JSON Schema's comparison bounds.
    # Strict JSON serialization refuses every nonfinite numeric value without
    # changing valid values or the canonical default payloads.
    try:
        json.dumps(document, allow_nan=False)
    except ValueError as exc:
        raise ValidationError("Rule documents must contain finite JSON numbers") from exc
    return document


def _literal_alternatives(pattern: str) -> list[str]:
    alternatives = pattern.casefold().split("|")
    if any(not part.strip() for part in alternatives):
        raise ValidationError("Rule patterns require nonempty literal alternatives")
    return alternatives


def mailbox(sender: str) -> tuple[str, str]:
    """Parse a single mailbox consistently on Python 3.11+ (no strict keyword)."""
    name, address = parseaddr(sender)
    return name.casefold(), address.casefold()


def matches(kind: str, pattern: str, email: Mapping[str, str]) -> bool:
    """Exact mailbox domains; literal casefolded keyword alternatives split by |.

    Subject keywords inspect subject only; medical keywords inspect subject/body.
    Subdomains must be explicitly listed. Display names never prove a domain.
    """
    alternatives = _literal_alternatives(pattern)
    name, address = mailbox(email.get("from", ""))
    domain = address.rsplit("@", 1)[1] if address.count("@") == 1 else ""
    if kind in ("domain", "sender_domain"):
        return bool(domain) and domain in alternatives
    if kind == "email":
        return address in alternatives
    if kind == "sender_name":
        return any(part in name for part in alternatives)
    text = email.get("subject", "")
    if kind == "keyword":
        text += " " + email.get("body", "")
    return any(part in text.casefold() for part in alternatives)
