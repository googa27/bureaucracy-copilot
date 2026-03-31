"""
weekly_summary.py -- Generate weekly inbox hygiene and case status summaries.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import anthropic

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "summarize_weekly_hygiene.md"


def collect_weekly_data(
    cases: list[dict],
    emails_classified: int,
    emails_pending: int,
    week_start: Optional[str] = None,
) -> dict:
    """Aggregate data for the weekly summary."""
    if week_start is None:
        today = datetime.utcnow().date()
        week_start = str(today - timedelta(days=today.weekday()))

    open_cases = [c for c in cases if c.get("status") == "open"]
    cases_with_missing = [c for c in open_cases if c.get("documents_missing")]

    return {
        "week_start": week_start,
        "emails_classified": emails_classified,
        "emails_pending": emails_pending,
        "open_cases": len(open_cases),
        "cases_with_missing_docs": len(cases_with_missing),
        "case_summaries": [
            {
                "insurer": c.get("insurer"),
                "provider": c.get("provider"),
                "amount": c.get("claimed_amount_clp"),
                "missing": c.get("documents_missing", []),
                "status": c.get("status"),
            }
            for c in open_cases[:10]
        ],
    }


def generate_weekly_summary(data: dict, client: anthropic.Anthropic) -> str:
    """Use Claude to produce a readable weekly summary."""
    prompt = PROMPT_PATH.read_text()
    user_message = json.dumps(data, indent=2, ensure_ascii=False)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text.strip()


def save_summary(summary: str, week_start: str, output_dir: Optional[Path] = None) -> Path:
    """Save a generated summary to disk."""
    if output_dir is None:
        output_dir = Path("~/.bureaucracy_copilot/summaries").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"weekly_{week_start}.md"
    path.write_text(summary)
    return path
