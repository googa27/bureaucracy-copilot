"""
event_extractor.py — Extract structured financial events from bank/payment emails.
"""

import json
import re
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from src.utils.resources import default_resource
from src.utils.rule_contracts import RuleDecision, load_rule_document, matches

RULES_PATH = default_resource("rules/finance_classification.yaml")
EVENTS_DIR = Path("~/.bureaucracy_copilot/finance_events").expanduser()

_rules: dict | None = None


def _load_rules() -> dict:
    global _rules
    if _rules is None:
        _rules = load_rule_document(RULES_PATH, "finance_classification")
    return _rules


def extract_amount_clp(text: str) -> int | None:
    """Extract a CLP amount from text. Returns integer pesos."""
    patterns = [
        r"\$\s*([\d\.]+)",
        r"CLP\s*([\d\.]+)",
        r"([\d\.]+)\s*pesos",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(".", "")
            try:
                return int(raw)
            except ValueError:
                pass
    return None


class FinanceDecision(RuleDecision):
    source: str
    event_type: str
    account_source: str
    account: str
    category: str | None
    extraction: dict
    archive: bool
    label: str


def classify_finance_email(email: dict[str, str]) -> FinanceDecision | None:
    """Propose declared metadata; domains before subject keywords, then YAML order.

    No extraction or financial action is performed. Missing category remains None.
    """
    rules = _load_rules()["classification_rules"]
    for kind in ("sender_domain", "subject_keyword"):
        for rule in rules:
            for pattern in rule["patterns"]:
                if kind in pattern and matches(kind, pattern[kind], email):
                    return {
                        "source": rule["source"],
                        "event_type": rule["event_type"],
                        "account_source": rule["account_source"],
                        "account": rule["account_source"],
                        "category": rule.get("category"),
                        "extraction": deepcopy(rule["extraction"]),
                        "archive": rule["archive"],
                        "label": rule["label"],
                        "rule": deepcopy(rule),
                        "confidence": 0.9 if kind == "sender_domain" else 0.85,
                        "method": "rule" if kind == "sender_domain" else "rule_keyword",
                    }
    return None


def create_event(email: dict, classification: dict, amount_clp: int | None = None) -> dict:
    """Create a FinancialEvent object from an email."""
    return {
        "event_id": str(uuid.uuid4()),
        "created_at": datetime.now(UTC).replace(tzinfo=None).isoformat(),
        "email_id": email.get("id"),
        "email_date": email.get("date"),
        "subject": email.get("subject"),
        "from": email.get("from"),
        "category": classification.get("category"),
        "subcategory": classification.get("subcategory"),
        "account": classification.get("account"),
        "amount_clp": amount_clp
        or extract_amount_clp(email.get("subject", "") + " " + email.get("body", "")[:500]),
        "currency": "CLP",
        "confidence": classification.get("confidence", 0.0),
        "method": classification.get("method"),
        "notes": "",
    }


def save_event(event: dict) -> Path:
    """Persist a financial event as JSON."""
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EVENTS_DIR / f"{event['event_id']}.json"
    path.write_text(json.dumps(event, indent=2, ensure_ascii=False))
    return path


def list_events(month: str | None = None, category: str | None = None) -> list[dict]:
    """List financial events, optionally filtered by month (YYYY-MM) or category."""
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    events = []
    for f in EVENTS_DIR.glob("*.json"):
        ev = json.loads(f.read_text())
        if month and not ev.get("email_date", "").startswith(month):
            continue
        if category and ev.get("category") != category:
            continue
        events.append(ev)
    return sorted(events, key=lambda e: e.get("email_date", ""), reverse=True)
