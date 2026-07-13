"""
draft_generator.py -- Draft follow-up emails for pending reimbursement cases.
"""
from __future__ import annotations

import base64
import json
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import anthropic

from src.governance.executor import MutationGuard
from src.governance.types import MutationProposal, MutationResult

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "draft_followup.md"
GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"


def build_followup_context(case: dict) -> str:
    """Build the user message context for a follow-up draft."""
    lines = [
        f"Insurer: {case.get('insurer', 'unknown')}",
        f"Provider: {case.get('provider', 'unknown')}",
        f"Service date: {case.get('service_date', 'unknown')}",
        f"Claimed amount: {case.get('claimed_amount_clp', 'unknown')} CLP",
        f"Status: {case.get('status', 'open')}",
        f"Missing documents: {case.get('documents_missing', [])}",
        f"Notes: {case.get('notes', '')}",
    ]
    return "\n".join(lines)


def draft_followup_email(
    case: dict,
    client: anthropic.Anthropic,
    language: str = "es",
) -> dict:
    """Use Claude to draft a follow-up email for a reimbursement case."""
    prompt = PROMPT_PATH.read_text()
    context = build_followup_context(case)
    user_message = f"Language: {language}\n\n{context}"

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
        return {
            "subject": "Seguimiento reembolso",
            "body": response,
            "to": "",
            "parse_error": True,
        }


def create_gmail_draft(
    service,
    draft_data: dict,
    thread_id: Optional[str] = None,
    *,
    guard: MutationGuard,
) -> MutationResult:
    """Create a Gmail draft through MutationGuard at the adapter boundary."""
    msg = MIMEText(draft_data.get("body", ""), "plain", "utf-8")
    msg["Subject"] = draft_data.get("subject", "")
    msg["To"] = draft_data.get("to", "")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {"message": {"raw": raw}}
    if thread_id:
        body["message"]["threadId"] = thread_id

    proposal = MutationProposal(
        action="gmail.create_draft",
        scope="gmail.compose",
        description="Create Gmail draft for private reimbursement follow-up",
        payload={
            "subject": draft_data.get("subject"),
            "to": draft_data.get("to"),
            "body": draft_data.get("body"),
            "thread_id": thread_id,
        },
        required_scopes=(GMAIL_COMPOSE_SCOPE,),
        classification="private",
    )
    return guard.execute(
        proposal,
        lambda: service.users().drafts().create(userId="me", body=body).execute(),
    )
