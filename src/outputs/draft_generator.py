"""
draft_generator.py -- Draft follow-up emails for pending reimbursement cases.
"""
from pathlib import Path
from typing import Optional
import anthropic

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "draft_followup.md"


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

    import json
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
) -> dict:
    """Create a Gmail draft from draft data."""
    import base64
    from email.mime.text import MIMEText

    msg = MIMEText(draft_data.get("body", ""), "plain", "utf-8")
    msg["Subject"] = draft_data.get("subject", "")
    msg["To"] = draft_data.get("to", "")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {"message": {"raw": raw}}
    if thread_id:
        body["message"]["threadId"] = thread_id

    return service.users().drafts().create(userId="me", body=body).execute()
