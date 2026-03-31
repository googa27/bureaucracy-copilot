# Bureaucracy Copilot

> **AI operations layer for Gmail + Google Calendar**

A personal bureaucracy operating system that turns your inbox into a near-autonomous platform for managing medical reimbursements, financial evidence, and administrative follow-up.

---

## What it does

- **Recovers money** from missed medical reimbursements (Esencial, BICE VIDA, Clínica Alemana)
- **Organizes your inbox** with a structured label taxonomy (Action / Pipeline / Records / Waiting / Feeds)
- **Extracts financial evidence** from bank, transfer, and payment emails into structured records
- **Automates follow-up** via Google Calendar reminders for open claims
- **Generates weekly/monthly summaries** so you don't have to manually scan your inbox
- **Prepares claim packets** with missing-document detection

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/googa27/bureaucracy-copilot.git
cd bureaucracy-copilot

# Install dependencies (Python 3.11+)
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Add your Gmail OAuth credentials and Anthropic API key

# Run first classification pass
python -m src.ingestion.run

# Generate weekly summary
python -m src.summaries.weekly
```

---

## Repository Structure

```
bureaucracy-copilot/
├── README.md               ← This file
├── PRD.md                  ← Product Requirements Document
├── PLAN.md                 ← Implementation plan
├── docs/
│   ├── architecture.md     ← System architecture
│   ├── label-taxonomy.md   ← Gmail label hierarchy
│   ├── insurer-routing.md  ← Claim routing logic (Esencial/BICE/Alemana)
│   ├── data-model.md       ← Data schemas
│   ├── calendar-automation.md  ← Calendar event logic
│   ├── summaries.md        ← Summary generation specs
│   └── privacy-and-risk.md ← Privacy policy and risk register
├── schemas/                ← JSON Schema definitions
├── rules/                  ← YAML classification rules
├── prompts/                ← LLM prompt templates
├── src/                    ← Python source code
│   ├── ingestion/          ← Gmail reading
│   ├── classification/     ← Email classification
│   ├── medical/            ← Reimbursement case tracking
│   ├── finance/            ← Financial event extraction
│   ├── calendar/           ← Calendar reminder creation
│   ├── summaries/          ← Summary generation
│   ├── outputs/            ← Gmail labels, drafts, events
│   └── utils/              ← Shared utilities
├── notebooks/              ← Exploration notebooks
└── tests/                  ← Test suite
```

---

## Key Concepts

### Label Taxonomy
Emails are classified into five top-level categories with detailed sub-labels:
- `BC/Action` — needs attention now
- `BC/Pipeline` — job search and career
- `BC/Records/Medical` — invoices, appointments, insurance
- `BC/Records/Finance` — bank, transfers, investments
- `BC/Waiting` — submitted claims and pending replies

See [docs/label-taxonomy.md](docs/label-taxonomy.md) for the full taxonomy.

### Medical Cases
Each reimbursable medical expense becomes a structured `MedicalCase` object with:
- Expense type and amount
- Inferred insurer route (Esencial / BICE VIDA / combined / unknown)
- Document checklist (invoice, form, prescription, etc.)
- Status tracking and next action

See [docs/insurer-routing.md](docs/insurer-routing.md) for routing logic.

### Financial Events
Bank transfers, payments, and receipts are extracted into structured `FinancialEvent` records with full traceability back to the source email.

### Automation Cadences
| Cadence | Jobs |
|---------|------|
| Daily | Classify new emails, update case statuses |
| Weekly | Hygiene summary, reimbursement queue review |
| Monthly | Finance digest, subscription audit |
| Quarterly | Sport Francés handoff, benefit review |

---

## v1 Success Definition

v1 is complete when:
1. Finance and medical emails are structurally searchable
2. A reimbursement backlog tracker exists and is usable
3. Calendar follow-up logic is working
4. Weekly/monthly summaries reduce manual scanning
5. System is ready for Claude/Codex implementation without redesign

---

## Status

| Component | Status |
|-----------|--------|
| PRD + PLAN | ✅ Complete |
| Label taxonomy | ✅ Defined |
| Schemas | ✅ Defined |
| Sender rules | ✅ Defined |
| Prompt templates | ✅ Defined |
| Gmail classifier | 🚧 In progress |
| Medical case tracker | 🔲 Not started |
| Financial extractor | 🔲 Not started |
| Calendar module | 🔲 Not started |
| Summary generator | 🔲 Not started |

---

## License

Private — personal use only. Not licensed for redistribution.
