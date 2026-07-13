"""
reminder_creator.py -- Create Google Calendar events for medical follow-ups and review blocks.
"""
from __future__ import annotations

from datetime import date, timedelta

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.governance.executor import MutationGuard
from src.governance.types import MutationProposal, MutationResult

CALENDAR_EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"
SCOPES = [CALENDAR_EVENTS_SCOPE]


def build_service(credentials: Credentials):
    """Build authenticated Google Calendar API service."""
    return build("calendar", "v3", credentials=credentials)


def create_followup_event(
    service,
    case: dict,
    days_from_now: int = 14,
    calendar_id: str = "primary",
    *,
    guard: MutationGuard,
) -> MutationResult:
    """Create a calendar follow-up event through MutationGuard."""
    follow_date = date.today() + timedelta(days=days_from_now)
    insurer = case.get("insurer", "Insurer")
    provider = case.get("provider", "Provider")
    case_id = case.get("case_id", "")[:8]
    amount = case.get("claimed_amount_clp")
    amount_str = f" -- ${amount:,} CLP" if amount else ""

    event = {
        "summary": f"Follow up: {insurer} reimbursement{amount_str}",
        "description": (
            f"Case ID: {case_id}\n"
            f"Insurer: {insurer}\n"
            f"Provider: {provider}\n"
            f"Service date: {case.get('service_date', 'unknown')}\n"
            f"Missing docs: {case.get('documents_missing', [])}\n"
        ),
        "start": {"date": follow_date.isoformat()},
        "end": {"date": (follow_date + timedelta(days=1)).isoformat()},
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 480}]},
        "colorId": "6",
    }
    return _insert_event(service, calendar_id, event, guard=guard, action="calendar.create_followup_event")


def create_weekly_review_block(
    service,
    review_date=None,
    calendar_id: str = "primary",
    *,
    guard: MutationGuard,
) -> MutationResult:
    """Create a weekly inbox hygiene review block through MutationGuard."""
    if review_date is None:
        today = date.today()
        days_ahead = 6 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        review_date = today + timedelta(days=days_ahead)

    event = {
        "summary": "Weekly Bureaucracy Review",
        "description": "Weekly inbox hygiene pass: open cases, reimbursements, finance events.",
        "start": {"dateTime": f"{review_date.isoformat()}T19:00:00", "timeZone": "America/Santiago"},
        "end": {"dateTime": f"{review_date.isoformat()}T20:00:00", "timeZone": "America/Santiago"},
        "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=SU"],
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 30}]},
        "colorId": "2",
    }
    return _insert_event(service, calendar_id, event, guard=guard, action="calendar.create_weekly_review_block")


def create_quarterly_handoff(
    service,
    quarter_end,
    calendar_id: str = "primary",
    *,
    guard: MutationGuard,
) -> MutationResult:
    """Create a quarterly review/handoff event through MutationGuard."""
    event = {
        "summary": "Quarterly Bureaucracy Handoff",
        "description": "Close resolved cases, quarterly finance summary, review benefit utilization.",
        "start": {"dateTime": f"{quarter_end.isoformat()}T10:00:00", "timeZone": "America/Santiago"},
        "end": {"dateTime": f"{quarter_end.isoformat()}T12:00:00", "timeZone": "America/Santiago"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 1440},
                {"method": "popup", "minutes": 60},
            ],
        },
        "colorId": "9",
    }
    return _insert_event(service, calendar_id, event, guard=guard, action="calendar.create_quarterly_handoff")


def _insert_event(
    service,
    calendar_id: str,
    event: dict,
    *,
    guard: MutationGuard,
    action: str,
) -> MutationResult:
    proposal = MutationProposal(
        action=action,
        scope="calendar.events",
        description="Insert private planner event into Google Calendar",
        payload={
            "calendar_id": calendar_id,
            "summary": event.get("summary"),
            "description": event.get("description"),
            "start": event.get("start"),
            "end": event.get("end"),
        },
        required_scopes=(CALENDAR_EVENTS_SCOPE,),
        classification="private",
    )
    return guard.execute(
        proposal,
        lambda: service.events().insert(calendarId=calendar_id, body=event).execute(),
    )
