"""
main.py -- Main pipeline entry point for Bureaucracy Copilot.

Usage:
    python -m src.main --run classify    # Classify new emails
    python -m src.main --run weekly      # Generate weekly summary
    python -m src.main --run monthly     # Generate monthly finance digest
    python -m src.main --run cases       # List open cases
"""
import argparse
import json
import sys
from pathlib import Path

import anthropic

from src.ingestion.auth import get_credentials
from src.ingestion.gmail_reader import (
    build_service as build_gmail,
    list_messages,
    get_message,
    parse_message,
    apply_label,
    archive_message,
    get_or_create_label,
)
from src.classification.classifier import classify
from src.medical.case_tracker import (
    extract_case_fields,
    create_case,
    save_case,
    list_cases,
)
from src.finance.event_extractor import (
    classify_finance_email,
    create_event,
    save_event,
    list_events,
)
from src.summaries.weekly_summary import (
    collect_weekly_data,
    generate_weekly_summary,
    save_summary,
)
from src.summaries.monthly_finance_summary import (
    aggregate_monthly_events,
    generate_monthly_summary,
    save_monthly_summary,
)
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_classify(cfg: dict, gmail, anthropic_client):
    """Fetch unclassified emails, classify, label, and archive."""
    logger.info("Starting classification run")
    messages = list_messages(gmail, query="in:inbox -label:BC")
    classified = 0
    for msg in messages:
        raw = get_message(gmail, msg["id"])
        email = parse_message(raw)
        result = classify(email, anthropic_client)
        label_name = result.get("label", "BC/misc/unclassified")
        label_id = get_or_create_label(gmail, label_name)
        apply_label(gmail, email["id"], [label_id])
        if result.get("action") == "archive":
            archive_message(gmail, email["id"])
        classified += 1
        logger.info(f"Classified {email['subject'][:60]!r} -> {label_name}")
        if result.get("category") in ("medical", "reimbursement"):
            fields = extract_case_fields(email, anthropic_client)
            case = create_case(email, fields)
            save_case(case)
            logger.info(f"Created case {case['case_id'][:8]} for {label_name}")
        elif result.get("category") in ("finance", "banking", "investment"):
            fin_class = classify_finance_email(email) or result
            event = create_event(email, fin_class)
            save_event(event)
    logger.info(f"Classification complete: {classified} emails processed")


def run_weekly(cfg: dict, anthropic_client):
    """Generate and print the weekly summary."""
    cases = list_cases()
    data = collect_weekly_data(cases, emails_classified=0, emails_pending=0)
    summary = generate_weekly_summary(data, anthropic_client)
    path = save_summary(summary, data["week_start"])
    print(summary)
    logger.info(f"Weekly summary saved to {path}")


def run_monthly(cfg: dict, anthropic_client, month: str):
    """Generate and print the monthly finance digest."""
    events = list_events(month=month)
    aggregated = aggregate_monthly_events(events)
    summary = generate_monthly_summary(month, aggregated, anthropic_client)
    path = save_monthly_summary(summary, month)
    print(summary)
    logger.info(f"Monthly finance summary saved to {path}")


def run_cases(_cfg: dict):
    """Print open cases as JSON."""
    cases = list_cases(status="open")
    print(json.dumps(cases, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Bureaucracy Copilot")
    parser.add_argument("--run", choices=["classify", "weekly", "monthly", "cases"], required=True)
    parser.add_argument("--month", default=None, help="Month for monthly digest (YYYY-MM)")
    args = parser.parse_args()

    cfg = load_config()

    api_key = cfg.get("anthropic_api_key")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    ac = anthropic.Anthropic(api_key=api_key)

    if args.run == "cases":
        run_cases(cfg)
        return

    creds = get_credentials()
    gmail = build_gmail(creds)

    if args.run == "classify":
        run_classify(cfg, gmail, ac)
    elif args.run == "weekly":
        run_weekly(cfg, ac)
    elif args.run == "monthly":
        from datetime import datetime
        month = args.month or datetime.utcnow().strftime("%Y-%m")
        run_monthly(cfg, ac, month)


if __name__ == "__main__":
    main()
