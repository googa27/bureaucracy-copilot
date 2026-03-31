"""
gmail_reader.py — Fetch and normalize Gmail messages via the Gmail API.
"""
import base64
import json
from datetime import datetime
from typing import Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


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


def apply_label(service, message_id: str, label_ids: list[str]) -> dict:
    """Apply Gmail labels to a message."""
    return service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": label_ids},
    ).execute()


def archive_message(service, message_id: str) -> dict:
    """Remove INBOX label to archive a message."""
    return service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["INBOX"]},
    ).execute()


def get_or_create_label(service, name: str) -> str:
    """Return label ID for a given label name, creating it if missing."""
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label["name"] == name:
            return label["id"]

    created = service.users().labels().create(
        userId="me",
        body={
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        },
    ).execute()
    return created["id"]
