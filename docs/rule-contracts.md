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
Literal `|` alternatives must each contain a non-whitespace character. Empty,
leading/trailing empty, and whitespace-only alternatives raise `ValidationError`
at loading and direct `matches` calls; no alternatives are silently removed.
Nonempty alternatives retain their existing literal spaces and casefold matching.
After shape validation, stdlib `json.dumps(..., allow_nan=False)` rejects all
nonfinite numeric metadata with `ValidationError`, including YAML `.nan` values
that do not satisfy ordinary comparison semantics. Finite confidence endpoints
0 and 1 and interior values remain valid and unchanged.
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
  `label`. Execution remains separately guarded at the Gmail adapter boundary.
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

## CLI proposal consumption

`src.classification.proposal.plan_classification(result: Mapping[str, Any])
-> ClassificationPlan` is a pure typed composition adapter. Label precedence is
sender `labels`, bundled-prompt `sub_labels`, then legacy `label` (defaulting to
`BC/misc/unclassified` only when no label field exists). It retains label order,
deduplicates exact duplicates, and rejects empty/non-list arrays or blank/non-string
items before Gmail mutations. Explicit `archive` must be a bool and takes precedence
over legacy `action == "archive"`; malformed proposals raise rather than silently
falling back. The original classifier result and its rule metadata are not changed.

`run_classify` plans/applies every label and the declared archive flag through the
existing MutationGuard adapters. Medical processing follows the exact
`BC/Records/Medical` branch; finance follows `BC/Records/Finance` and the exact
`BC/Records/Career/Payslip` label. A branch matches itself or children separated by
`/`, never lookalike prefixes. `Records` alone does not identify a domain. Legacy
`category` values medical/reimbursement and finance/banking/investment still select
their old processing paths. A message with both medical and finance labels runs
each local path once. Finance's canonical classification proposal is passed into
the existing event builder; no missing event category is invented from event_type.

Dry-run retains its existing boundary: it prevents Gmail/Calendar mutations,
requests readonly Gmail scope, and records redacted proposals. It can still call
the LLM and persist local case/event JSON under `~/.bureaucracy_copilot/`.
This change makes previously missed canonical domains reach that existing behavior;
it does not introduce a no-LLM/no-local-write mode. Tests use synthetic Gmail and
LLM fakes and temporary local-state/audit paths only. Case/event schema completeness,
extraction-policy execution, insurer eligibility, and idempotent local processing
remain separate limitations. No Calendar, submission or new provider action is added.

`python -m pytest -q tests/e2e/test_classification_pipeline.py` exercises every
actual sender default, matching priority, negative senders, multiple labels,
canonical prompt and legacy outputs, archive precedence, invalid proposals,
domain dispatch and approved/dry-run adapter paths without provider access.

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

Run `python -m pytest -q tests/integration/test_rule_contracts.py tests/integration/test_rule_value_validation.py
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

The strict numeric boundary follows the maintained standard-library
[JSON encoder contract](https://docs.python.org/3.12/library/json.html#json.dump).
Canonical defaults and their pinned byte hashes are unchanged by these checks.
