"""Default payload contracts: missing packaging or altered bytes must fail."""

import hashlib
from importlib.resources import files

import pytest
import yaml

DEFAULT_HASHES = {
    "prompts/build_claim_case.md": "55c24f24fed8d0a6b413bfb774775db908611c71a5b2b296d070bfa188c1a0d8",
    "prompts/classify_email.md": "98c5f199ced81ff008330c4266afcefecaf92c935b5a1099b0359960e44dcf81",
    "prompts/draft_followup.md": "62247ed0a806be0ae8988e36fcbb8dc29d4aba1c63b35210b13e30562e42cb67",
    "prompts/summarize_finance_monthly.md": "2e2460a5a9440f9628e9c00c1e23e721a49f80cf4cd664aa612c3e2fb20b43cf",
    "prompts/summarize_weekly_hygiene.md": "69d0e33ac05099b317af99dc195b20645a9197ae0c95639c3371813cb7a85aaf",
    "rules/finance_classification.yaml": "84245694b1d0d82021f93c2be232e02d822241eb46f815b6f8b388caa422a6f2",
    "rules/gmail_sender_rules.yaml": "c003ee6a40f13e165701a20584f03bf85a77ea9045b0c80a38ddecf6a9c8c7e3",
    "rules/medical_routes.yaml": "299a4c5079cfceafd555557c6538d7abbd66c6389f3deb55efb9409c4bc49d88",
    "rules/summary_rules.yaml": "325d94156aed7a1d68ac0051c3a37c15742640dc0ac52c74fead5923b3ab3e8f",
}


@pytest.mark.parametrize("name,digest", DEFAULT_HASHES.items())
def test_packaged_defaults_preserve_original_bytes(name, digest):
    resource = files("src.utils").joinpath("assets", name)
    assert hashlib.sha256(resource.read_bytes()).hexdigest() == digest
    text = resource.read_text(encoding="utf-8")
    if name.endswith(".yaml"):
        if name == "rules/medical_routes.yaml":
            with pytest.raises(yaml.parser.ParserError):
                yaml.safe_load(text)
        else:
            assert isinstance(yaml.safe_load(text), dict)
    else:
        assert text.strip()


@pytest.mark.parametrize("name", ["../secret", "/etc/passwd", "prompts/../rules/x", r"prompts\x"])
def test_default_lookup_rejects_unknown_or_traversing_names(name):
    from src.utils.resources import default_resource

    with pytest.raises(ValueError):
        default_resource(name)


def test_missing_default_retains_file_not_found(monkeypatch, tmp_path):
    from src.utils import resources

    monkeypatch.setattr(resources, "files", lambda package: tmp_path)
    with pytest.raises(FileNotFoundError):
        resources.default_resource("prompts/classify_email.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "module_name,function,resource,returns_json",
    [
        ("src.classification.classifier", "classify_by_llm", "classify_email.md", True),
        ("src.medical.case_tracker", "extract_case_fields", "build_claim_case.md", True),
        ("src.outputs.draft_generator", "draft_followup_email", "draft_followup.md", True),
        (
            "src.summaries.weekly_summary",
            "generate_weekly_summary",
            "summarize_weekly_hygiene.md",
            False,
        ),
        (
            "src.summaries.monthly_finance_summary",
            "generate_monthly_summary",
            "summarize_finance_monthly.md",
            False,
        ),
    ],
)
def test_real_prompt_read_paths(module_name, function, resource, returns_json):
    from importlib import import_module
    from types import SimpleNamespace

    module = import_module(module_name)
    if hasattr(module, "_prompt_template"):
        module._prompt_template = None

    class SyntheticMessages:
        def create(self, **kwargs):
            assert (
                hashlib.sha256(kwargs["system"].encode("utf-8")).hexdigest()
                == DEFAULT_HASHES["prompts/" + resource]
            )
            assert "synthetic-marker" in kwargs["messages"][0]["content"]
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        text='{"synthetic": true}' if returns_json else "synthetic summary"
                    )
                ]
            )

    payload = {"subject": "synthetic-marker", "notes": "synthetic-marker"}
    client = SimpleNamespace(messages=SyntheticMessages())
    result = (
        getattr(module, function)("2026-01", payload, client)
        if function == "generate_monthly_summary"
        else getattr(module, function)(payload, client)
    )
    if returns_json:
        assert result["synthetic"] is True
    else:
        assert result == "synthetic summary"


def test_real_yaml_loaders_preserve_existing_schema():
    from src.classification import classifier
    from src.finance import event_extractor
    from src.medical import case_tracker

    classifier._rules = None
    event_extractor._rules = None
    case_tracker._route_rules = None
    assert classifier._load_rules()[0]["rule_id"] == "esencial_01"
    assert event_extractor._load_rules()["classification_rules"][0]["source"] == "tenpo"
    with pytest.raises(yaml.parser.ParserError):
        case_tracker._load_route_rules()
    # Existing rule-schema/consumer mismatch is preserved, not repaired here.
    assert classifier.classify_by_rules({"from": "synthetic@example.invalid"}) is None
    assert event_extractor.classify_finance_email({}) is None
    with pytest.raises(yaml.parser.ParserError):
        case_tracker.infer_insurer({})
