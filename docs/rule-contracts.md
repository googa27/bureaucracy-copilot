# Deterministic rule proposals (issue #13)

The four bundled YAML documents are the canonical configuration shapes. Gmail
uses `rules` and the existing `schemas/sender_rule.schema.json` vocabulary;
finance uses `classification_rules`, `patterns`, `event_type`, `account_source`
and `extraction`; medical uses `routes`, `combined_route`,
`expense_type_modifiers` and `fallback`. Summary configuration is shape-validated
without adding summary behavior. Legacy `domains/label`, finance `rules/account`
and medical `insurers/triggers` shapes are refused, not implicitly migrated.

`src.utils.rule_contracts.load_rule_document(resource: TextResource, kind: str)
-> dict[str, Any]` accepts a pathlib or Traversable text resource and one of
`gmail_sender_rules`, `finance_classification`, `medical_routes`, `summary_rules`.
PyYAML `safe_load` handles syntax/standard tags; existing direct dependency
jsonschema's `Draft7Validator.check_schema` and `validate` enforce the declared
shape. Closed objects reject typos, required fields reject incomplete inputs.
YAML, schema, I/O and unexpected failures propagate; no fallback catches hide them.
No dependencies were added. Schema definitions live in `src.utils.rule_contracts`
so normal wheels need no checkout-relative schema paths; architecture fitness
compares the sender definition with the existing public schema (strengthening
empty identifiers/patterns/labels only).

Public APIs accept `dict[str, str]` email payloads with optional `from`, `subject`,
and `body` fields:

- `src.classification.classifier.classify_by_rules -> SenderDecision | None`:
  first active matching rule in YAML order. `labels`, `classification`, `archive`
  and complete independent `rule` metadata are retained. Compatibility `label`
  is the first proposed label, `category` aliases classification, `action` is
  `label`. This does not claim the pipeline applied every label or archive flag.
- `src.finance.event_extractor.classify_finance_email -> FinanceDecision | None`:
  all sender-domain patterns precede subject-keyword patterns; ties follow YAML
  order. `account` explicitly aliases `account_source`; `category` is the declared
  value or None, never invented from `event_type`. Complete `rule` and `extraction`
  metadata survive. Extraction/normalization/threshold policies are retained by
  the document loader; classification does not execute them.
- `src.medical.case_tracker.propose_route -> RouteDecision`: all matched signals
  survive with complete `policy`. Esencial plus BICE VIDA means `combined`, with
  the existing Esencial-first description and additional confirmation requirement
  preserved in policy. Otherwise first YAML signal wins, including Alemana;
  fallback is `unknown`, zero confidence, manual review. Combined confidence is
  the minimum of matching Esencial/BICE VIDA signal heuristics. Expense modifiers
  are retained metadata and do not establish eligibility or change routing.
  `infer_insurer -> str` is an explicit compatibility alias for the route name.

Sender matching uses stdlib `email.utils.parseaddr` without the Python-3.13-only
`strict` argument. Domain comparisons use the actual mailbox's exact casefolded
domain. Subdomains require explicit rules; suffix/lookalike/display-name domains
never match. This is not sender authentication. The existing sender schema's
`email` matches the parsed address; `sender_name` is a display-name substring
heuristic. `subject_keyword` inspects subject only; medical `keyword` inspects
subject and body, excluding sender display text. Keywords are casefolded literal
substrings; `|` separates literal alternatives, not arbitrary regex syntax.
Confidence is heuristic metadata, not calibrated probability or coverage proof.

A deterministic source-only demonstration (no network or persistence):

```python
from src.classification.classifier import classify_by_rules
from src.finance.event_extractor import classify_finance_email
from src.medical.case_tracker import propose_route

assert classify_by_rules({"from": "Synthetic <x@previred.com>"})["labels"] == [
    "BC/Records/Finance/Bank",
    "BC/Records/Career/Payslip",
]
assert classify_finance_email({"subject": "liquidación"})["event_type"] == "salary"
assert propose_route({"subject": "isapre y seguro complementario"})["route"] == "combined"
assert propose_route({})["route"] == "unknown"
```

Run `python -m pytest -q tests/integration/test_rule_contracts.py
 tests/architecture/test_rule_contract_fitness.py` (one command line).
Tests cover all actual default rules and shape refusal with synthetic inputs.
These classifications are not full `financial_event` or `medical_case` schema
acceptance. Existing event/case persistence and extraction remain separately
limited. No provider, insurer coverage, financial action, human review or maturity
claim follows from source tests. Exact final archives/normal installations,
independent review, dedicated real human/security review and resulting-main
verification remain pending with the parent.

Parent-supplied maintained API research: [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation)
handles parsing rather than shape validation;
[jsonschema validation](https://python-jsonschema.readthedocs.io/en/stable/validate/)
provides checked supported validators. Public domain semantics were checked against
sender/financial schemas, data-model, label-taxonomy, PRD, README and actual defaults.
No FPF/PDP imports or data transfers are involved.
