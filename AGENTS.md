# AGENTS.md — bureaucracy-copilot

## Purpose and safety

`bureaucracy-copilot` is classified as `Product App` under Portfolio Project #24. Preserve public/upstream compatibility, privacy, and evidence boundaries; do not infer maturity beyond executable tests.

## Canonical documentation

- `README.md` where present
- `docs/ARCHITECTURE.yaml` — machine-readable source of truth
- `docs/ARCHITECTURE.md` — rationale and extension guidance

<!-- PORTFOLIO-CONSTITUTION:START -->
## Portfolio engineering constitution

This repository follows [Portfolio Project #24](https://github.com/users/googa27/projects/24) and [bureaucracy-copilot rollout issue](https://github.com/googa27/bureaucracy-copilot/issues/3). A repository-specific, evidence-backed exception in `docs/ARCHITECTURE.yaml` may specialize a rule; undocumented drift is not an exception.

### Research and maintained-library preference

- Research domain theory, maintained libraries, standards, interfaces, datasets, licenses, adjacent repositories, and probable extension paths before design or implementation.
- **Maintained-library preference:** use well-maintained libraries for solved algorithms, protocols, parsers, persistence, orchestration, dataframes, numerical methods, and security controls instead of implementing them from scratch. Record capability, selected library, alternatives, maintenance/API/license evidence, adapter boundary, and any custom-code justification.
- Custom code belongs to domain semantics, composition, adapters/contracts, or genuinely missing algorithms and must be tested against an oracle/reference.
- Turn reusable findings into maintained Hermes skills and concise support files. Add a plugin or MCP server only when stable CLI/contracts have multiple measured consumers or real interoperable external-tool needs.

### Clean and evolutionary architecture

After the dependency route is sound, apply SOLID, DRY knowledge ownership, suitable design patterns, explicit dependencies, low coupling, cohesive modules, extensibility, maintainability, and technical-debt minimization. Design for probable extensions, not speculative frameworks. Every meaningful change reduces named debt or adds an executable fitness function.

`docs/ARCHITECTURE.yaml` is the machine-readable source of truth. Update it in the same change as architecture, public API, test, CI, data, AI-interface, or exception changes.

- At each Python `src/` level, count immediate runtime `.py` files and package directories, excluding `__init__.py` and architecture/readme/typing metadata. Default maximum: 10. Deepen hierarchy around stable responsibilities instead of widening it.
- Default Python module maximum: 500 physical lines. Larger legacy files are exact no-growth exceptions with reason, owner/context, risk, accepted ceiling, and refactoring trigger.
- Keep `tests/unit`, `tests/integration`, `tests/e2e`, and `tests/architecture`; mirror source where useful. Empty suites document their intended boundary and activation trigger.
- Architecture tests enforce the YAML contract, source fan-out, module-size ratchets, exception metadata, required docs/suites, and repository-specific import/public-API rules.

### Two first-class users

1. **Hermes Agent and compatible agents:** this concise root file, deterministic CLI/public contracts, exact verification commands, and capability discovery are the baseline. Skills encode recurring procedures. Plugins/MCP are optional escalation layers, never substitutes for a stable public interface; mutation tools must be explicit, typed, least-privileged, and separately verifiable.
2. **Human programmer/notebook user:** provide a typed, documented importable API independent of CLI/UI internals and deterministic public-synthetic notebook examples where the repository is a library. Use only lawful Python protocols: compact `__repr__`, value equality/hash for deeply immutable objects, true collection/context/NumPy protocols, and pure IPython display hooks. Prefer named methods for policy, configuration, I/O, diagnostics, expensive/stateful behavior, or ambiguous mathematics. Test every claimed algebraic law and named-method/operator parity.

### AI-assisted change controls

- Treat agent output as untrusted until a human reviews it and executable repository gates verify it. The human author remains accountable.
- Keep agent changes small, single-purpose, and completely reviewable. Generated tests are not a sufficient sole oracle for generated implementation.
- New dependencies require human approval plus package-existence, maintenance, API, license, vulnerability, and typosquat checks; lock reproducibly.
- Security-sensitive code (authentication, cryptography, parsers, serialization, SQL, filesystem, subprocess, network, permissions, or private data) requires dedicated human review.
- Use least privilege: workspace-scoped writes, network/secret access only when approved, no autonomous merge/deploy, and exact command/result provenance.
- Measure AI impact with lead time, review time, CI failures, reverts, escaped defects, and churn; do not infer productivity from self-report.

### Semantic source-tree hierarchy

- Do **not** balance source folders like AVL/B-trees. Package boundaries follow information hiding, cohesion, coupling, public contracts, ownership, and change patterns; naturally heavy-tailed sizes are expected.
- Empty marker packages and speculative folder scaffolds are forbidden unless an exact, dated structural-role exception exists. Keep future plans in architecture/roadmap documents.
- `__init__.py` is a compatibility/public facade only: imports, re-exports, `__all__`, metadata, and bounded lazy hooks. Domain classes and business functions belong in cohesive modules.
- Severe branch concentration is a review trigger, not a command to redistribute files. Fix it only when dependency, churn, ownership, or comprehension evidence shows a bad boundary.


### GitHub Actions supply-chain controls

- Pin every third-party action to a full-length commit SHA; keep the human-readable release in a comment.
- Declare least-privilege workflow `permissions`; read-only `contents` is the default.
- Set `persist-credentials: false` on checkout and provide narrowly scoped credentials only to the step that needs mutation.
- Validate workflow changes with `python scripts/selftest_ai_hierarchy_policy.py`, `pinact run --fix=false --no-api`, and `zizmor --offline --min-severity medium .`.

### Data and core-repository boundaries

For data-consuming work, design `source registry -> typed acquisition -> immutable Bronze -> canonical Silver -> curated Gold/features -> formulation/model -> governed output -> read-only UI/API/notebook` before implementation. Record grain, units, classification, lineage, quality, freshness/vintage/effective time, identity, replay, and validation.

- `PDP` owns reusable/public data acquisition and products.
- `financial_problem_formulations` owns general problem/formulation/formula/workflow semantics.
- `ui_and_artifacts` owns reusable audience-aware rendering and artifact QA.
- Consume stable public contracts/CLIs, not repository internals. Keep canonical names theoretical/general rather than deal/product-specific.

Repository posture: Avoid FPF; use ui_and_artifacts only for redacted governed reports; do not put private personal data in PDP. Data posture: Private local data custody with dry-run-first mutation proposals, redacted audit logs, explicit human approval, least requested Google scopes, and source -> validated records -> governed outputs.

Mutation architecture: classifiers/extractors propose Gmail/Calendar changes; `src.governance.executor.MutationGuard` records redacted audit events and executes only when `--approve-mutations`, `--approved-by`, and `--approval-reason` are supplied. Do not claim or imply leaked secrets; treat this as preventive privacy architecture.

### Exact commands

- Setup: `python -m pip install -r requirements.txt`
- Tests: `python -m pytest -q`
- Lint: `python -m ruff check .`
- Format: `python -m ruff format --check .`
- Portfolio architecture: `python scripts/check_portfolio_architecture.py`
- Governance setup: `python3 -m pip install -r requirements-architecture.txt`
- AI/hierarchy policy: `python3 scripts/check_ai_hierarchy_policy.py`

If a command is declared unavailable, the activation trigger and replacement command belong in `docs/ARCHITECTURE.yaml`; do not fabricate successful output.
<!-- PORTFOLIO-CONSTITUTION:END -->

## Issue #10: synthetic impact contract

The public-synthetic example preserves raw fitted propensity support separately from bounded ordinary ATT weighting scores and reports clipping count/fraction. Weighted DiD uncertainty is conditional on supplied weights, without first-stage adjustment; coverage is unvalidated. See [example API and limits](examples/impact_evaluation/README.md).

```bash
python -m examples.impact_evaluation.reminder_impact --capabilities
python -m examples.impact_evaluation.reminder_impact --format json
python -m pytest -q tests/integration/test_impact_evaluation.py tests/integration/test_impact_evaluation_controls.py tests/e2e/test_impact_cli.py
```

These CPU-only commands use generated public-synthetic user-period data (days; seed 7; 6400 rows per design; 12000-row panel cap). No provider access is involved. Python 3.12/Linux x86_64 is the hash-locked configured gate. Use `requirements-impact.lock` with `--require-hashes --only-binary=:all:`; its header records generation inputs. PR #9 and issues #10/#11 track executed evidence and remaining acceptance, including installed/copied origins and dedicated human/security review; configuration alone is not proof.


## Issue #11: repository quality gates

The Python 3.12 hash-locked CI job runs the complete Ruff lint and format gates
above after dependency installation. `python -m pytest -q` includes executable
workflow invocation checks and synthetic JSON error/UTC compatibility regressions.
Expected JSON decode failures retain legacy fallback outputs; unexpected failures
propagate. Legacy event/case/log timestamps remain naive UTC ISO strings; audit
records remain offset-qualified. See `docs/ARCHITECTURE.md` for boundary contracts.
Human/security review and verification on actual resulting main remain outstanding;
local gates and configured CI are not evidence of those approvals or hosted success.


## Issue #12: bundled defaults

The single canonical default source is `src/utils/assets/prompts/` (five templates)
and `src/utils/assets/rules/` (four YAML files). Explicit setuptools package-data
includes them in wheel and sdist. `src.utils.resources.default_resource` rejects
names outside the fixed registry and returns an importlib.resources Traversable;
consumers use UTF-8 `read_text`/`open`, including non-filesystem loaders. Existing
`PROMPT_PATH`, `RULES_PATH`, and `ROUTES_PATH` constants are resource handles now;
pathlib-only operations and writes through those constants are unsupported.
Private state paths and mutation approval requirements are unchanged.

Issue #13 corrects only the malformed medical description quoting and reconciles
consumers with the declared rule shapes. All nine original hashes remain in
`tests/integration/test_default_resources.py`, alongside the corrected medical
hash and a reversible original-byte witness. The five prompts and three other
YAML defaults remain byte identical. See [rule contracts](docs/rule-contracts.md)
for typed proposal APIs, matching policy, metadata retention and limits.
Rule loading and direct matching reject empty or whitespace-only literal OR
alternatives; rule documents reject nonfinite numbers before proposals are built.
Source tests do not certify exact installed artifacts, human/security approval,
whole medical/financial schemas, or resulting main.

`src.classification.proposal.plan_classification` adapts canonical sender `labels`,
prompt `sub_labels`, and legacy `label/category/action` results. The CLI consumes
every label and explicit archive bool through MutationGuard; medical/finance
taxonomy branches and payslips select the existing local processing paths.
`python -m pytest -q tests/e2e/test_classification_pipeline.py` exercises all real
sender defaults, canonical/legacy outputs and guarded execution with synthetic
Gmail/LLM fakes. Dry-run blocks external mutations, not LLM use or local JSON
persistence; tests must redirect case/event/audit state to temporary paths.
