"""
case_tracker.py — Build and track medical reimbursement cases from classified emails.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import anthropic

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "build_claim_case.md"
ROUTES_PATH = Path(__file__).parent.parent.parent / "rules" / "medical_routes.yaml"
CASES_DIR = Path("~/.bureaucracy_copilot/cases").expanduser()

_route_rules: dict | None = None


def _load_route_rules() -> dict:
    global _route_rules
    if _route_rules is None:
        import yaml
        with open(ROUTES_PATH) as f:
            _route_rules = yaml.safe_load(f)
    return _route_rules


def infer_insurer(email: dict) -> Optional[str]:
    """Infer the relevant insurer from sender domain or subject keywords."""
    rules = _load_route_rules()
    sender = email.get("from", "").lower()
    subject = email.get("subject", "").lower()
    body = email.get("body", "").lower()
    text = sender + " " + subject + " " + body[:200]

    for insurer_rule in rules.get("insurers", []):
        for trigger in insurer_rule.get("triggers", []):
            if trigger.lower() in text:
                return insurer_rule["name"]

    return None


def extract_case_fields(email: dict, client: anthropic.Anthropic) -> dict:
    """Use Claude to extract structured fields from a medical email."""
    prompt = PROMPT_PATH.read_text()
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
    except Exception:
        return {"parse_error": response}


def create_case(email: dict, fields: dict) -> dict:
    """Create a new MedicalCase object."""
    insurer = fields.get("insurer") or infer_insurer(email)
    return {
        "case_id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
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


def list_cases(status: Optional[str] = None) -> list[dict]:
    """List all cases, optionally filtered by status."""
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    cases = []
    for f in CASES_DIR.glob("*.json"):
        case = json.loads(f.read_text())
        if status is None or case.get("status") == status:
            cases.append(case)
    return sorted(cases, key=lambda c: c.get("created_at", ""), reverse=True)
