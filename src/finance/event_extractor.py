"""
event_extractor.py — Extract structured financial events from bank/payment emails.
"""

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

import yaml

from src.utils.resources import default_resource

RULES_PATH = default_resource("rules/finance_classification.yaml")
EVENTS_DIR = Path("~/.bureaucracy_copilot/finance_events").expanduser()

_rules: dict | None = None


def _load_rules() -> dict:
    global _rules
    if _rules is None:
        with RULES_PATH.open("r", encoding="utf-8") as f:
            _rules = yaml.safe_load(f)
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


def classify_finance_email(email: dict) -> dict | None:
    """Try to classify using deterministic finance rules."""
    rules = _load_rules()
    sender = email.get("from", "").lower()
    subject = email.get("subject", "").lower()
    body = email.get("body", "").lower()

    for rule in rules.get("rules", []):
        for domain in rule.get("domains", []):
            if domain.lower() in sender:
                return {
                    "category": rule["category"],
                    "subcategory": rule.get("subcategory", ""),
                    "account": rule.get("account", ""),
                    "confidence": 1.0,
                    "method": "rule",
                }
        for keyword in rule.get("subject_keywords", []):
            if keyword.lower() in subject or keyword.lower() in body[:200]:
                return {
                    "category": rule["category"],
                    "subcategory": rule.get("subcategory", ""),
                    "account": rule.get("account", ""),
                    "confidence": 0.85,
                    "method": "rule_keyword",
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
