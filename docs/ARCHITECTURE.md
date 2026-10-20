# Architecture — bureaucracy-copilot

<!-- PORTFOLIO-CONSTITUTION:START -->
## Portfolio architecture baseline

Source of truth: `docs/ARCHITECTURE.yaml`. Tracking: [Project #24](https://github.com/users/googa27/projects/24), [bureaucracy-copilot issue](https://github.com/googa27/bureaucracy-copilot/issues/3). Profile: `application`; enforcement: `Blocking`.

### Research-backed defaults

| Decision | Evidence | Repository application |
|---|---|---|
| Agent context | [Hermes context files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files), [AGENTS.md](https://agents.md/) | Root `AGENTS.md`; progressive detail stays in linked docs. |
| AI tool escalation | [MCP tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) | Stable CLI/contracts and skills first; plugin/MCP only after measured need and least-privilege review. |
| Python source layout | [PyPA src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) | Declared Python roots: `src`. |
| Test layout | [pytest good practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) | Unit/integration/e2e/architecture boundaries are explicit. |
| Module budget | [Pylint too-many-lines rationale](https://pylint.readthedocs.io/en/latest/user_guide/messages/convention/too-many-lines.html) plus AI review locality | 500 physical lines is stricter than Pylint's broad default; existing excess is a no-growth ratchet. |
| Evolution | [Evolutionary architecture](https://evolutionaryarchitecture.com/precis.html) | Architecture characteristics have executable fitness functions and incremental exceptions. |
| Data layers | [Medallion architecture](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion) | Applied only where data is consumed; simple repos record an explicit non-use decision. |
| Python protocols | [Python data model](https://docs.python.org/3/reference/datamodel.html), [NumPy dispatch](https://numpy.org/doc/stable/user/basics.dispatch.html) | Dunders express true protocols/laws; named methods own policy and effects. |

### Maintained-library decision table

| Capability | Selected route | Alternatives | Boundary / custom-code rule |
|---|---|---|---|
| Existing runtime stack | No stable runtime dependency manifest was detected; revival requires a dependency decision table. | Reimplementation from scratch | Preserve public adapters; research maintenance/API/license before additions. |
| Architecture contract bootstrap | Python standard-library JSON parser over the JSON subset of YAML 1.2 | Hand-written YAML parser; mandatory platform service | Repo-local dependency-free structural gate; richer maintained tools remain repo-specific. |
| Import/dependency rules | Existing repo lint/import tools where configured; declarative YAML boundary is authoritative | Custom import framework | Keep custom AST checks narrow; use maintained Import Linter/Tach/Ruff/deptry when warranted. |
| AI interaction | AGENTS + deterministic CLI/contracts + capability discovery + skills | MCP/plugin in every repo | Escalate only after measured interoperability/lifecycle need. |
| Causal-impact research example | Optional NumPy + pandas + statsmodels `impact` profile; stdlib SQLite for SQL execution | Hand-coded estimators; a general causal framework | Isolated to `examples/impact_evaluation`; the core runtime does not import the scientific stack. |

### Two-user design

- AI: AGENTS + deterministic admin CLI/dry-run/capabilities; no broad MCP until scopes and mutation approval are proven.
- Human/notebook: Typed service facade and notebook-safe redacted DTOs; no side-effectful dunders.
- Planned Python protocols: Immutable document/workflow references: __repr__ and value equality only.; Resource clients use context managers only for real lifecycle ownership.; Network, approval, submission, and mutation remain named methods.
- Core posture: Avoid FPF; use ui_and_artifacts only for redacted governed reports; do not put private personal data in PDP.
- Data posture: Private local data custody with dry-run-first mutation proposals, redacted audit logs, explicit human approval, least requested Google scopes, and source -> validated records -> governed outputs.
- Preventive mutation architecture: Gmail/Calendar side effects are represented as `MutationProposal` records, redacted, audited, and applied only through `MutationGuard` after explicit approval flags. This is a privacy-by-design control, not evidence of any prior leak.
- CLI dependency boundary: local inspection mode `python -m src.main --run cases` imports only local-state/redaction code and is tested to run without Anthropic, Google packages, OAuth credentials, or `ANTHROPIC_API_KEY`; Gmail/LLM dependencies are imported only by modes that need them.
- Causal-impact example boundary: `examples/impact_evaluation` is public-synthetic and non-runtime. It may use the optional `impact` dependency profile, must not consume Gmail/Calendar/local private state, and must not be advertised as production impact evidence.

### Extension and exception discipline

Probable extensions must cross named ports/capability registries rather than adding sibling modules indefinitely. Every exception is exact, risk-bearing, no-growth, and has a refactoring trigger. Generated/vendor/migration/resource paths are declared explicitly; they do not silently weaken runtime rules.
<!-- PORTFOLIO-CONSTITUTION:END -->

## Issue #10: synthetic impact contract

The public-synthetic example preserves raw fitted propensity support separately from bounded ordinary ATT weighting scores and reports clipping count/fraction. Weighted DiD uncertainty is conditional on supplied weights, without first-stage adjustment; coverage is unvalidated. See [example API and limits](../examples/impact_evaluation/README.md).

```bash
python -m examples.impact_evaluation.reminder_impact --capabilities
python -m examples.impact_evaluation.reminder_impact --format json
python -m pytest -q tests/integration/test_impact_evaluation.py tests/integration/test_impact_evaluation_controls.py tests/e2e/test_impact_cli.py
```

These CPU-only commands use generated public-synthetic user-period data (days; seed 7; 6400 rows per design; 12000-row panel cap). No provider access is involved. Python 3.12/Linux x86_64 is the hash-locked configured gate. `ARCHITECTURE.yaml` defines the normal wheel plus copied-example profile and transparent third-party reuse. PR #9 and issues #10/#11 retain executed evidence and remaining human/security and resulting-main acceptance.


## Issue #11: complete quality gates and compatibility

The existing Python 3.12 hash-locked workflow runs `python -m ruff check .` and
`python -m ruff format --check .` after dependency installation, followed by
`python -m pytest -q`. These are complete repository gates using the inherited
rule selection; no ignores, baselines, dependency changes, or relaxed architecture
limits are introduced. `tests/architecture/test_quality_workflow.py` uses installed
PyYAML to inspect actual workflow run steps and installation order. Python-invoked
non-executable governance scripts omit misleading shebangs.

Library rationale: retain installed Ruff, stdlib `json`/`datetime`, and PyYAML's
safe loader. Their public APIs already cover these boundaries; a custom parser,
clock framework, or new dependency would add no capability. Ruff's
[BLE001 guidance](https://docs.astral.sh/ruff/rules/blind-except/) supports catching
only expected errors. Classification, medical extraction, and draft generation
catch only `json.JSONDecodeError` around decoding synthetic/provider response text.
Valid JSON results and malformed-JSON fallback payloads remain compatible,
including the classifier's existing `method="llm"` fallback. This change adds no
schema validation or data migration. Decoder TypeError, non-JSON ValueError,
RuntimeError, and resource errors propagate with their original identity.
The policy CLI handles only contract read/decode/shape errors (`OSError`,
`UnicodeError`, `yaml.YAMLError`, `ContractShapeError`) during loading; validation
runs outside that catch so programmer/runtime defects retain their traceback.
Tests use real JSON decoding for expected outputs and narrowly injected decoder
or validation failures for unexpected errors, without live provider calls.

Ruff's [DTZ003 guidance](https://docs.astral.sh/ruff/rules/call-datetime-utcnow/)
and Python's [aware/naive datetime contract](https://docs.python.org/3.12/library/datetime.html#aware-and-naive-objects)
support an explicitly aware UTC clock. Finance event `created_at`, medical case
`created_at`/`updated_at`, and JSON logger `ts` call `datetime.now(UTC)` then remove
`tzinfo` only at their legacy serialization boundary. Exact naive ISO strings and
naive date arithmetic remain compatible. Weekly default dates and monthly CLI
default months derive directly from aware UTC, never local time.
`src/governance/audit.py` already used aware UTC and continues to emit `+00:00`;
Ruff's `UTC` alias modernization preserves that contract. Fixed synthetic clocks
separate UTC from local day/month boundaries and reject the legacy clock path.
No inference, propensity, weighting, coverage, or synthetic-data semantics change.

Local source gates do not establish hosted CI, human/security review, provider
acceptance, scientific acceptance, or verification on actual resulting main.
Those reviews and merge/main gates remain outstanding; no issue closure is claimed.


The locked research environment need not contain the separate security tooling.
Run `zizmor --offline --min-severity medium .` using an authorized compatible
installation of the declared tool; report its actual result for the exact revision.
Passing local pinact and policy self-tests are partial checks, not a replacement
security-audit result. Reused immutable dependencies and separately installed
project wheels must be identified independently in retained execution evidence.


## Issue #12: bundled defaults

The single canonical default source is `src/utils/assets/prompts/` (five templates)
and `src/utils/assets/rules/` (four YAML files). Explicit setuptools package-data
includes them in wheel and sdist. `src.utils.resources.default_resource` rejects
names outside the fixed registry and returns an importlib.resources Traversable;
consumers use UTF-8 `read_text`/`open`, including non-filesystem loaders. Existing
`PROMPT_PATH`, `RULES_PATH`, and `ROUTES_PATH` constants are resource handles now;
pathlib-only operations and writes through those constants are unsupported.
Private state paths and mutation approval requirements are unchanged.

Byte preservation includes existing limitations: `medical_routes.yaml` line 24
is invalid YAML and still raises PyYAML ParserError; Gmail/finance rule schemas
also differ from their current consumers. Packaging tests retain these outcomes,
not semantic repairs. Those runtime schema/routing defects are separately owned by
[issue #13](https://github.com/googa27/bureaucracy-copilot/issues/13), not accepted
functionality. All nine original hashes and synthetic resource-backed API
checks live in `tests/integration/test_default_resources.py`; package selection
fitness lives in `tests/architecture/test_resource_packaging.py`. Source passes
do not certify final installed artifacts, human/security approval, or main.

The build contract follows [setuptools package-data](https://setuptools.pypa.io/en/latest/userguide/datafiles.html)
and [Python resource access](https://docs.python.org/3.12/library/importlib.resources.html).
No new dependency or custom installer is needed. CI compares wheel/sdist bytes with
`scripts/check_distribution_resources.py`, then exercises normally installed
resource consumers from a temporary directory. This focused CI check complements
the separately required full installed/copied acceptance profile.
