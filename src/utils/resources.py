"""Read-only access to the application's bundled default payloads."""

from importlib.resources import files
from importlib.resources.abc import Traversable

_DEFAULT_NAMES = frozenset(
    {
        "prompts/build_claim_case.md",
        "prompts/classify_email.md",
        "prompts/draft_followup.md",
        "prompts/summarize_finance_monthly.md",
        "prompts/summarize_weekly_hygiene.md",
        "rules/finance_classification.yaml",
        "rules/gmail_sender_rules.yaml",
        "rules/medical_routes.yaml",
        "rules/summary_rules.yaml",
    }
)


def default_resource(name: str) -> Traversable:
    """Return a bundled default; reject names outside the fixed payload registry.

    The result is a read-only resource handle, not a writable filesystem path.
    Missing payloads retain the loader's FileNotFoundError when opened.
    """
    if name not in _DEFAULT_NAMES:
        raise ValueError(f"Unknown default resource: {name!r}")
    return files("src.utils").joinpath("assets", *name.split("/"))
