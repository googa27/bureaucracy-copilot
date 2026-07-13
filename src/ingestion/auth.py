"""
auth.py — Google OAuth2 authentication for Gmail and Calendar APIs.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"
CALENDAR_EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"

READONLY_SCOPES = (GMAIL_READONLY_SCOPE,)
MUTATION_SCOPES = (GMAIL_MODIFY_SCOPE, CALENDAR_EVENTS_SCOPE)
SCOPES = list(READONLY_SCOPES)

TOKEN_PATH = Path("~/.bureaucracy_copilot/token.json").expanduser()
CREDENTIALS_PATH = Path("~/.bureaucracy_copilot/credentials.json").expanduser()


def get_credentials(scopes: Sequence[str] | None = None) -> Credentials:
    """Load or refresh OAuth2 credentials for the least requested scopes."""
    requested_scopes = list(scopes or READONLY_SCOPES)
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), requested_scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Google credentials not found at {CREDENTIALS_PATH}.\n"
                    "Download credentials.json from Google Cloud Console and place it there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), requested_scopes)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return creds
