"""
classifier.py — Classify Gmail messages using sender rules and LLM fallback.
"""
import re
import yaml
from pathlib import Path
from typing import Optional
import anthropic

RULES_PATH = Path(__file__).parent.parent.parent / "rules" / "gmail_sender_rules.yaml"
PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "classify_email.md"

_rules: list[dict] | None = None
_prompt_template: str | None = None


def _load_rules() -> list[dict]:
    global _rules
    if _rules is None:
        with open(RULES_PATH) as f:
            data = yaml.safe_load(f)
        _rules = data.get("rules", [])
    return _rules


def _load_prompt() -> str:
    global _prompt_template
    if _prompt_template is None:
        _prompt_template = PROMPT_PATH.read_text()
    return _prompt_template


def classify_by_rules(email: dict) -> Optional[dict]:
    """
    Try to classify an email using deterministic sender rules.
    Returns a classification dict or None if no rule matched.
    """
    rules = _load_rules()
    sender = email.get("from", "").lower()
    subject = email.get("subject", "").lower()

    for rule in rules:
        for domain in rule.get("domains", []):
            if domain.lower() in sender:
                return {
                    "label": rule["label"],
                    "category": rule.get("category", ""),
                    "action": rule.get("action", "label"),
                    "confidence": 1.0,
                    "method": "rule",
                    "matched_rule": rule.get("name", domain),
                }

        for keyword in rule.get("subject_keywords", []):
            if keyword.lower() in subject:
                return {
                    "label": rule["label"],
                    "category": rule.get("category", ""),
                    "action": rule.get("action", "label"),
                    "confidence": 0.9,
                    "method": "rule_keyword",
                    "matched_rule": rule.get("name", keyword),
                }

    return None


def classify_by_llm(email: dict, client: anthropic.Anthropic) -> dict:
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
        import json
        result = json.loads(response_text)
    except Exception:
        result = {
            "label": "BC/misc/unclassified",
            "category": "unknown",
            "action": "label",
            "confidence": 0.3,
            "method": "llm_parse_error",
        }

    result["method"] = "llm"
    return result


def classify(email: dict, client: Optional[anthropic.Anthropic] = None) -> dict:
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
