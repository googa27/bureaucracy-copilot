"""
gmail_reader.py — Fetch and normalize Gmail messages via the Gmail API.
"""
from __future__ import annotations

import base64

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.governance.executor import MutationGuard
from src.governance.types import MutationProposal, MutationResult

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MUTATION_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"


def build_service(credentials: Credentials):
    """Build authenticated Gmail API service."""
    return build("gmail", "v1", credentials=credentials)


def list_messages(service, query: str = "", max_results: int = 100) -> list[dict]:
    """List Gmail messages matching a query."""
    messages = []
    response = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages.extend(response.get("messages", []))

    while "nextPageToken" in response and len(messages) < max_results:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
            pageToken=response["nextPageToken"],
        ).execute()
        messages.extend(response.get("messages", []))

    return messages[:max_results]


def get_message(service, message_id: str) -> dict:
    """Fetch a full message by ID."""
    return service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()


def parse_message(raw: dict) -> dict:
    """Extract key fields from a raw Gmail API message."""
    headers = {h["name"].lower(): h["value"] for h in raw["payload"]["headers"]}
    body = _extract_body(raw["payload"])
    return {
        "id": raw["id"],
        "thread_id": raw["threadId"],
        "subject": headers.get("subject", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "date": headers.get("date", ""),
        "snippet": raw.get("snippet", ""),
        "body": body,
        "labels": raw.get("labelIds", []),
        "size_estimate": raw.get("sizeEstimate", 0),
    }


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    if "parts" in payload:
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result

    return ""


def get_or_create_label(service, name: str, *, guard: MutationGuard) -> str | None:
    """Return a label ID, creating a missing label only through MutationGuard."""
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label["name"] == name:
            return label["id"]

    proposal = MutationProposal(
        action="gmail.create_label",
        scope="gmail.modify",
        description="Create Gmail classification label",
        payload={"label_name": name},
        required_scopes=(GMAIL_MODIFY_SCOPE,),
        classification="private",
    )

    def create_label() -> dict:
        return service.users().labels().create(
            userId="me",
            body={
                "name": name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()

    result = guard.execute(proposal, create_label)
    return result.applied_reference if result.status == "applied" else None


def apply_label(
    service,
    message_id: str,
    label_ids: list[str],
    *,
    guard: MutationGuard,
    subject: str | None = None,
    label_name: str | None = None,
) -> MutationResult:
    """Apply Gmail labels through MutationGuard at the adapter boundary."""
    proposal = MutationProposal(
        action="gmail.apply_label",
        scope="gmail.modify",
        description="Apply Gmail classification label to one message",
        payload={
            "message_id": message_id,
            "subject": subject,
            "label": label_name,
            "label_ids": label_ids,
        },
        required_scopes=(GMAIL_MODIFY_SCOPE,),
        classification="private",
    )
    return guard.execute(
        proposal,
        lambda: service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": label_ids},
        ).execute(),
    )


def archive_message(
    service,
    message_id: str,
    *,
    guard: MutationGuard,
    subject: str | None = None,
) -> MutationResult:
    """Remove INBOX label through MutationGuard at the adapter boundary."""
    proposal = MutationProposal(
        action="gmail.archive_message",
        scope="gmail.modify",
        description="Remove INBOX label after classification",
        payload={"message_id": message_id, "subject": subject},
        required_scopes=(GMAIL_MODIFY_SCOPE,),
        classification="private",
    )
    return guard.execute(
        proposal,
        lambda: service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["INBOX"]},
        ).execute(),
    )
