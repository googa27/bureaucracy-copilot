"""
main.py -- Main pipeline entry point for Bureaucracy Copilot.

Usage:
    python -m src.main --run classify            # Dry-run classification preview
    python -m src.main --run classify --approve-mutations --approved-by USER --approval-reason "manual review"
    python -m src.main --run weekly              # Generate weekly summary
    python -m src.main --run monthly --month YYYY-MM
    python -m src.main --run cases               # List open cases
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:  # pragma: no cover - exercised when optional dependency is installed
    import anthropic
except ImportError:  # pragma: no cover - keeps dry architecture/unit tests importable
    anthropic = None

from src.classification.classifier import classify
from src.finance.event_extractor import (
    classify_finance_email,
    create_event,
    list_events,
    save_event,
)
from src.governance.approval import ApprovalPolicy
from src.governance.executor import MutationGuard
from src.governance.redaction import redact_mapping
from src.ingestion.auth import GMAIL_MODIFY_SCOPE, READONLY_SCOPES, get_credentials
from src.ingestion.gmail_reader import (
    apply_label,
    archive_message,
    build_service as build_gmail,
    get_message,
    get_or_create_label,
    list_messages,
    parse_message,
)
from src.medical.case_tracker import (
    create_case,
    extract_case_fields,
    list_cases,
    save_case,
)
from src.summaries.monthly_finance_summary import (
    aggregate_monthly_events,
    generate_monthly_summary,
    save_monthly_summary,
)
from src.summaries.weekly_summary import (
    collect_weekly_data,
    generate_weekly_summary,
    save_summary,
)
from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)
DEFAULT_AUDIT_LOG = Path("~/.bureaucracy_copilot/audit.ndjson")


def run_classify(cfg: dict[str, Any], gmail: Any, anthropic_client: Any, guard: MutationGuard) -> None:
    """Fetch unclassified emails, classify, and plan/apply labels with approval controls."""
    logger.info("Starting classification run")
    messages = list_messages(gmail, query="in:inbox -label:BC")
    classified = 0
    for msg in messages:
        raw = get_message(gmail, msg["id"])
        email = parse_message(raw)
        result = classify(email, anthropic_client)
        label_name = result.get("label", "BC/misc/unclassified")
        label_id = get_or_create_label(gmail, label_name, guard=guard)
        if label_id is not None:
            label_result = apply_label(
                gmail,
                email["id"],
                [label_id],
                guard=guard,
                subject=email.get("subject"),
                label_name=label_name,
            )
            if label_result.status == "planned":
                print(json.dumps({"dry_run": redact_mapping(label_result.to_dict())}, indent=2, ensure_ascii=False))

        if result.get("action") == "archive":
            archive_result = archive_message(
                gmail,
                email["id"],
                guard=guard,
                subject=email.get("subject"),
            )
            if archive_result.status == "planned":
                print(json.dumps({"dry_run": redact_mapping(archive_result.to_dict())}, indent=2, ensure_ascii=False))

        classified += 1
        safe_email = redact_mapping(email)
        logger.info("Classified message -> %s; preview=%s", label_name, safe_email.get("subject"))

        if result.get("category") in ("medical", "reimbursement"):
            fields = extract_case_fields(email, anthropic_client)
            case = create_case(email, fields)
            save_case(case)
            logger.info("Created case %s for %s", case["case_id"][:8], label_name)
        elif result.get("category") in ("finance", "banking", "investment"):
            fin_class = classify_finance_email(email) or result
            event = create_event(email, fin_class)
            save_event(event)
    logger.info("Classification complete: %s emails processed", classified)


def run_weekly(cfg: dict[str, Any], anthropic_client: Any) -> None:
    """Generate and print the weekly summary."""
    cases = list_cases()
    data = collect_weekly_data(cases, emails_classified=0, emails_pending=0)
    summary = generate_weekly_summary(data, anthropic_client)
    path = save_summary(summary, data["week_start"])
    print(summary)
    logger.info("Weekly summary saved to %s", path)


def run_monthly(cfg: dict[str, Any], anthropic_client: Any, month: str) -> None:
    """Generate and print the monthly finance digest."""
    events = list_events(month=month)
    aggregated = aggregate_monthly_events(events)
    summary = generate_monthly_summary(month, aggregated, anthropic_client)
    path = save_monthly_summary(summary, month)
    print(summary)
    logger.info("Monthly finance summary saved to %s", path)


def run_cases(_cfg: dict[str, Any]) -> None:
    """Print open cases as redacted JSON."""
    cases = [redact_mapping(case) for case in list_cases(status="open")]
    print(json.dumps(cases, indent=2, ensure_ascii=False))


def build_anthropic_client(cfg: dict[str, Any]) -> Any:
    if anthropic is None:
        logger.error("anthropic package is not installed")
        sys.exit(1)
    api_key = cfg.get("anthropic_api_key")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bureaucracy Copilot")
    parser.add_argument("--run", choices=["classify", "weekly", "monthly", "cases"], required=True)
    parser.add_argument("--month", default=None, help="Month for monthly digest (YYYY-MM)")
    parser.add_argument(
        "--approve-mutations",
        action="store_true",
        help="Execute external Gmail/Calendar mutations. Default is dry-run planning only.",
    )
    parser.add_argument("--approved-by", default=None, help="Human approver for mutation mode")
    parser.add_argument("--approval-reason", default=None, help="Why mutation mode is approved")
    parser.add_argument("--audit-log", default=str(DEFAULT_AUDIT_LOG), help="NDJSON audit path")
    args = parser.parse_args()
    if args.run == "classify" and args.approve_mutations and (
        not args.approved_by or not args.approval_reason
    ):
        parser.error("--approve-mutations requires --approved-by and --approval-reason")

    cfg = load_config()

    if args.run == "cases":
        run_cases(cfg)
        return

    anthropic_client = build_anthropic_client(cfg)

    if args.run == "weekly":
        run_weekly(cfg, anthropic_client)
        return
    if args.run == "monthly":
        from datetime import datetime

        month = args.month or datetime.utcnow().strftime("%Y-%m")
        run_monthly(cfg, anthropic_client, month)
        return

    scopes = (GMAIL_MODIFY_SCOPE,) if args.approve_mutations else READONLY_SCOPES
    creds = get_credentials(scopes=scopes)
    gmail = build_gmail(creds)
    policy = ApprovalPolicy(
        dry_run=not args.approve_mutations,
        approved_by=args.approved_by,
        approval_reason=args.approval_reason,
    )
    guard = MutationGuard(policy=policy, audit_path=args.audit_log)
    run_classify(cfg, gmail, anthropic_client, guard)


if __name__ == "__main__":
    main()
