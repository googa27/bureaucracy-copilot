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

### Two-user design

- AI: AGENTS + deterministic admin CLI/dry-run/capabilities; no broad MCP until scopes and mutation approval are proven.
- Human/notebook: Typed service facade and notebook-safe redacted DTOs; no side-effectful dunders.
- Planned Python protocols: Immutable document/workflow references: __repr__ and value equality only.; Resource clients use context managers only for real lifecycle ownership.; Network, approval, submission, and mutation remain named methods.
- Core posture: Avoid FPF; use ui_and_artifacts only for redacted governed reports; do not put private personal data in PDP.
- Data posture: Private local data custody with dry-run-first mutation proposals, redacted audit logs, explicit human approval, least requested Google scopes, and source -> validated records -> governed outputs.
- Preventive mutation architecture: Gmail/Calendar side effects are represented as `MutationProposal` records, redacted, audited, and applied only through `MutationGuard` after explicit approval flags. This is a privacy-by-design control, not evidence of any prior leak.
- CLI dependency boundary: local inspection mode `python -m src.main --run cases` imports only local-state/redaction code and is tested to run without Anthropic, Google packages, OAuth credentials, or `ANTHROPIC_API_KEY`; Gmail/LLM dependencies are imported only by modes that need them.

### Extension and exception discipline

Probable extensions must cross named ports/capability registries rather than adding sibling modules indefinitely. Every exception is exact, risk-bearing, no-growth, and has a refactoring trigger. Generated/vendor/migration/resource paths are declared explicitly; they do not silently weaken runtime rules.
<!-- PORTFOLIO-CONSTITUTION:END -->
