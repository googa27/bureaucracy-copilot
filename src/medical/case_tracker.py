"""
case_tracker.py — Build and track medical reimbursement cases from classified emails.
"""

import json
import uuid
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from src.utils.resources import default_resource
from src.utils.rule_contracts import load_rule_document, matches

PROMPT_PATH = default_resource("prompts/build_claim_case.md")
ROUTES_PATH = default_resource("rules/medical_routes.yaml")
CASES_DIR = Path("~/.bureaucracy_copilot/cases").expanduser()

_route_rules: dict | None = None


def _load_route_rules() -> dict:
    global _route_rules
    if _route_rules is None:
        _route_rules = load_rule_document(ROUTES_PATH, "medical_routes")
    return _route_rules


class RouteDecision(TypedDict):
    route: str
    confidence: float
    signals: list[dict]
    policy: dict


def propose_route(email: dict[str, str]) -> RouteDecision:
    """Pure route proposal, never coverage/eligibility or submission advice.

    All matching signals are retained; esencial+bicevida yields combined.
    Otherwise the first YAML signal wins. Expense modifiers remain metadata.
    """
    rules = _load_route_rules()
    signals = [r for r in rules["routes"] if matches(r["pattern_type"], r["pattern"], email)]
    routes = {r["route"] for r in signals}
    combined = {"esencial", "bicevida"}.issubset(routes)
    route = (
        "combined" if combined else signals[0]["route"] if signals else rules["fallback"]["route"]
    )
    confidence = (
        min(r["confidence"] for r in signals if r["route"] in ("esencial", "bicevida"))
        if combined
        else signals[0]["confidence"]
        if signals
        else rules["fallback"]["confidence"]
    )
    return {
        "route": route,
        "confidence": confidence,
        "signals": deepcopy(signals),
        "policy": deepcopy(rules),
    }


def infer_insurer(email: dict[str, str]) -> str:
    """Compatibility alias returning the named proposed route, including unknown."""
    return propose_route(email)["route"]


def extract_case_fields(email: dict, client: Any) -> dict:
    """Use Claude to extract structured fields from a medical email."""
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_message = (
        f"FROM: {email.get('from', '')}\n"
        f"SUBJECT: {email.get('subject', '')}\n"
        f"DATE: {email.get('date', '')}\n\n"
        f"{email.get('body', '')[:2000]}"
    )
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    response = message.content[0].text.strip()
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"parse_error": response}


def create_case(email: dict, fields: dict) -> dict:
    """Create a new MedicalCase object."""
    insurer = fields.get("insurer") or infer_insurer(email)
    return {
        "case_id": str(uuid.uuid4()),
        "created_at": datetime.now(UTC).replace(tzinfo=None).isoformat(),
        "updated_at": datetime.now(UTC).replace(tzinfo=None).isoformat(),
        "status": "open",
        "insurer": insurer,
        "provider": fields.get("provider"),
        "service_date": fields.get("service_date"),
        "claimed_amount_clp": fields.get("claimed_amount_clp"),
        "reimbursed_amount_clp": fields.get("reimbursed_amount_clp"),
        "documents_received": fields.get("documents_received", []),
        "documents_missing": fields.get("documents_missing", []),
        "email_ids": [email.get("id")],
        "notes": fields.get("notes", ""),
    }


def save_case(case: dict) -> Path:
    """Persist a case as JSON."""
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    path = CASES_DIR / f"{case['case_id']}.json"
    path.write_text(json.dumps(case, indent=2, ensure_ascii=False))
    return path


def load_case(case_id: str) -> dict:
    """Load a case from disk."""
    path = CASES_DIR / f"{case_id}.json"
    return json.loads(path.read_text())


def list_cases(status: str | None = None) -> list[dict]:
    """List all cases, optionally filtered by status."""
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    cases = []
    for f in CASES_DIR.glob("*.json"):
        case = json.loads(f.read_text())
        if status is None or case.get("status") == status:
            cases.append(case)
    return sorted(cases, key=lambda c: c.get("created_at", ""), reverse=True)
