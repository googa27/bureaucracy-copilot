"""
classifier.py — Classify Gmail messages using sender rules and LLM fallback.
"""

import json
from copy import deepcopy
from typing import Any

from src.utils.resources import default_resource
from src.utils.rule_contracts import RuleDecision, load_rule_document, matches

RULES_PATH = default_resource("rules/gmail_sender_rules.yaml")
PROMPT_PATH = default_resource("prompts/classify_email.md")

_rules: list[dict] | None = None
_prompt_template: str | None = None


def _load_rules() -> list[dict]:
    global _rules
    if _rules is None:
        _rules = load_rule_document(RULES_PATH, "gmail_sender_rules")["rules"]
    return _rules


def _load_prompt() -> str:
    global _prompt_template
    if _prompt_template is None:
        _prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    return _prompt_template


class SenderDecision(RuleDecision):
    labels: list[str]
    label: str
    classification: str | None
    archive: bool
    category: str | None
    action: str
    matched_rule: str


def classify_by_rules(email: dict[str, str]) -> SenderDecision | None:
    """Propose first active YAML match, preserving all labels and metadata.

    Compatibility label is the first label; category aliases classification.
    Confidence is a heuristic, not authenticated sender evidence.
    """
    for rule in _load_rules():
        if rule.get("active", True) and matches(rule["pattern_type"], rule["pattern"], email):
            keyword = rule["pattern_type"] == "subject_keyword"
            return {
                "labels": list(rule["labels"]),
                "label": rule["labels"][0],
                "classification": rule.get("classification"),
                "category": rule.get("classification"),
                "archive": rule.get("archive", False),
                "action": "label",
                "confidence": rule.get("confidence_boost", 0.9),
                "method": "rule_keyword" if keyword else "rule",
                "matched_rule": rule["rule_id"],
                "rule": deepcopy(rule),
            }
    return None


def classify_by_llm(email: dict, client: Any) -> dict:
    """
    Classify an email using Claude when no rule matches.
    """
    prompt = _load_prompt()
    user_message = (
        f"FROM: {email.get('from', '')}\n"
        f"SUBJECT: {email.get('subject', '')}\n"
        f"SNIPPET: {email.get('snippet', '')}\n\n"
        f"Body (first 500 chars):\n{email.get('body', '')[:500]}"
    )

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        system=prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = message.content[0].text.strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {
            "label": "BC/misc/unclassified",
            "category": "unknown",
            "action": "label",
            "confidence": 0.3,
            "method": "llm_parse_error",
        }

    result["method"] = "llm"
    return result


def classify(email: dict, client: Any | None = None) -> dict:
    """
    Main classification entry point. Tries rules first, falls back to LLM.
    """
    result = classify_by_rules(email)
    if result:
        return result

    if client:
        return classify_by_llm(email, client)

    return {
        "label": "BC/misc/unclassified",
        "category": "unknown",
        "action": "label",
        "confidence": 0.0,
        "method": "no_match",
    }
