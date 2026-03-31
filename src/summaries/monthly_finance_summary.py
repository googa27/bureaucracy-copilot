"""
monthly_finance_summary.py -- Generate monthly finance digest from financial events.
"""
import json
from collections import defaultdict
from pathlib import Path
from typing import Optional
import anthropic

PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "summarize_finance_monthly.md"


def aggregate_monthly_events(events: list[dict]) -> dict:
    """Aggregate financial events into a structured monthly report."""
    by_category = defaultdict(list)
    total_clp = 0

    for ev in events:
        cat = ev.get("category", "uncategorized")
        by_category[cat].append(ev)
        amount = ev.get("amount_clp") or 0
        total_clp += amount

    category_totals = {}
    for cat, evs in by_category.items():
        cat_total = sum(e.get("amount_clp") or 0 for e in evs)
        category_totals[cat] = {
            "count": len(evs),
            "total_clp": cat_total,
            "events": [
                {
                    "date": e.get("email_date", ""),
                    "description": e.get("subject", ""),
                    "amount": e.get("amount_clp"),
                    "account": e.get("account"),
                }
                for e in evs[:5]
            ],
        }

    return {
        "total_events": len(events),
        "total_clp": total_clp,
        "by_category": category_totals,
    }


def generate_monthly_summary(month: str, aggregated: dict, client: anthropic.Anthropic) -> str:
    """Use Claude to generate a readable monthly finance digest."""
    prompt = PROMPT_PATH.read_text()
    user_message = f"Month: {month}\n\n" + json.dumps(aggregated, indent=2, ensure_ascii=False)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text.strip()


def save_monthly_summary(summary: str, month: str, output_dir: Optional[Path] = None) -> Path:
    """Save a generated monthly summary to disk."""
    if output_dir is None:
        output_dir = Path("~/.bureaucracy_copilot/summaries").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"finance_{month}.md"
    path.write_text(summary)
    return path
