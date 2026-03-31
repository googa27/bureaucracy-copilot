# PRD.md — Bureaucracy Copilot

**Working subtitle:** AI operations layer for Gmail + Calendar + claims + financial evidence

---

## 1. Product Vision

Build a system that turns Gmail and Google Calendar into a near-autonomous personal operations platform that:

- recovers money from missed reimbursements
- preserves financial evidence for analysis
- reduces bureaucracy and procrastination
- keeps important inbox items visible
- automates reminders, summaries, and follow-up
- becomes a reusable template for other people, including family

> **Long-term target:** "Manual bureaucracy becomes exception handling, not the default mode."

---

## 2. Problem Statement

### Inbox pain
- Inbox is too noisy to trust
- Important admin/financial/medical items are buried
- Unread status is meaningless
- Newsletters and promotions compete with real tasks

### Medical bureaucracy pain
- Reimbursements were not submitted for many medical expenses
- Documents exist in email but are not organized as cases
- Reimbursement routes are fragmented across isapre and insurers
- Follow-up is easy to procrastinate

### Financial data pain
- Valuable evidence exists across bank/investment/payment emails
- Later analysis is possible in theory but hard in practice
- Transport/subscription/medical/admin costs are not structured

### Calendar pain
- Calendar is underused
- Reminders and deadlines are not connected to bureaucracy state

### Human pain
- User strongly dislikes bureaucracy
- User procrastinates on admin work even when the value is obvious
- Cognitive overhead is the enemy

---

## 3. Users

### Primary user
Cristobal:
- Highly technical
- Values automation and leverage
- Wants reliable systems
- Wants finance and admin data preserved
- Dislikes repetitive admin friction

### Secondary user
Future family/user archetype:
- Struggles with bureaucracy
- Needs claims, invoices, reminders, and paperwork simplified

---

## 4. Product Goals

| Goal | Description |
|------|-------------|
| Goal 1 — Recover money | Identify and operationalize missed reimbursement opportunities |
| Goal 2 — Trustworthy inbox surfaces | Make inbox/action state sparse, interpretable, and useful again |
| Goal 3 — Preserve structured evidence | Build long-lived structured datasets from financial and medical email evidence |
| Goal 4 — Reduce manual follow-up burden | Move deadlines, reminders, and claim-chasing into Calendar and automated summaries |
| Goal 5 — Prepare for near-full automation | Design v1 so Codex or Claude can later implement highly automated pipelines cleanly |

---

## 5. Non-Goals

- Replacing official insurer or bank systems
- Autonomous execution of risky external actions without review
- Perfect extraction from all attachments on day one
- Deep legal or policy adjudication
- Replacing a full accounting system in v1
- Replacing a human on ambiguous claims or safety-sensitive actions

---

## 6. Key Product Principles

1. **Preserve evidence** — Never destroy useful financial/medical history unless explicitly approved
2. **Route before summarize** — Organization comes before analytics
3. **Cases over emails** — Important workflows should be modeled as cases or events, not loose messages
4. **Human review for irreversible actions** — Draft, stage, and prepare first
5. **Surface exceptions** — Compress noise and expose what is blocked, stale, expensive, or valuable
6. **Automation should reduce shame, not create it** — The system should make bureaucracy feel lighter

---

## 7. Scope

### v1 (current)
- Gmail classification
- Label/routing framework
- Medical reimbursement case tracker
- Financial event extraction schema
- Calendar reminder logic
- Weekly and monthly summaries
- Unsubscribe / archive suggestions
- Job-pipeline signal tracking
- Benefits worth using

### v1.5
- Attachment ingestion pipeline
- Normalized claim packet folders
- Confidence scoring
- Missing-doc detection
- Dashboard views

### v2
- Semi-automatic claim packet generation
- Insurer-specific routing logic
- WhatsApp/email draft generation
- Richer financial analytics
- Benefit optimization engine
- Family template / multi-user mode

### v3
- Maximum feasible end-to-end automation with verified portals/APIs
- Cross-source reconciliation
- Agentic workflows with human approvals
- Mobile-friendly dashboard / notifications

---

## 8. Major Workflows

### 8.1 Inbox Routing Workflow
**Input:** New emails and existing inbox backlog

**Output:** Labeled, archived, and surfaced mail streams:
- Action
- Pipeline
- Records
- Feeds
- Waiting

**Acceptance:** Finance and medical records are no longer mixed with promo noise; inbox volume dramatically reduced

### 8.2 Medical Reimbursement Workflow
**Input:** Invoices, appointment emails, claim instructions, reimbursement forms, prescriptions, insurer messages

**Output:** Claim case objects, case statuses, missing doc flags, next action, follow-up reminders

**Acceptance:** User can see all likely reimbursable items in one structured queue; blocked reasons explicit; waiting claims surfaced automatically

### 8.3 Financial Evidence Workflow
**Input:** Bank emails, transfer confirmations, receipts, statements, investment confirmations, club dues, transport receipts

**Output:** Structured financial events, evidence links to original email, preserved historical archive, digest-ready dataset

**Acceptance:** User can later analyze spending without re-reading the inbox manually

### 8.4 Calendar Orchestration Workflow
**Input:** Cases needing follow-up, statements needing review, appointments, admin deadlines

**Output:** Reminder events, recurring review blocks, follow-up triggers

**Acceptance:** Calendar becomes the time-based operational layer for bureaucracy

### 8.5 Maintenance Summary Workflow
**Input:** Mailbox state, claims state, waiting items, financial event changes

**Output:** Weekly hygiene summary, reimbursement queue summary, monthly finance digest, unsubscribe suggestions, stale-item alerting

**Acceptance:** User can stay operational without manually scanning the inbox

---

## 9. Data Model

See `schemas/` directory for full JSON schemas.

**Key objects:**
- `EmailRecord` — classified email with metadata and confidence
- `MedicalCase` — reimbursement case with status, documents, route
- `FinancialEvent` — structured financial transaction from email evidence
- `ReminderTask` — calendar-linked task with related object type

---

## 10. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-1 | Gmail classification into Action / Pipeline / Records / Waiting / Feeds |
| FR-2 | Hierarchical label taxonomy for medical / finance / career / admin / waiting / feeds |
| FR-3 | Medical case generation from reimbursement-relevant emails |
| FR-4 | Missing-doc detection and status flagging |
| FR-5 | Route inference (Esencial / BICE VIDA / Alemana / combined / unknown) |
| FR-6 | Financial event extraction from bank/payment/investment/receipt emails |
| FR-7 | Evidence preservation — every structured object links to source email(s) |
| FR-8 | Summary generation: weekly hygiene, reimbursement summary, monthly finance digest |
| FR-9 | Calendar reminder creation for claim follow-up, periodic review, finance reviews |
| FR-10 | Draft generation for follow-ups, insurer chase emails, handoff messages |
| FR-11 | Safety gating before mass archive/delete, insurer submission, or third-party communication |

---

## 11. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | Reliability — misclassification degrades safely; uncertain items remain visible |
| NFR-2 | Auditability — any structured object traceable to raw email evidence |
| NFR-3 | Incremental deployability — provides value before full automation exists |
| NFR-4 | Privacy — sensitive health/finance data treated as confidential, minimally exposed |
| NFR-5 | Reversibility — archiving/labeling flows reversible; deletion exceptional |
| NFR-6 | Extensibility — supports future insurer adapters, dashboard UI, multi-user, connectors |

---

## 12. Integrations

### Required
- Gmail (read, label, archive, draft)
- Google Calendar (create/update events and reminders)

### Strongly recommended
- Spreadsheet tracker (structured data output)
- GitHub repository (this repo — rule/prompt management)
- Google Drive (claim packet storage)

### Future
- Contacts
- WhatsApp-compatible output layer
- OCR/document parsing layer
- Insurer portal adapters where possible

---

## 13. Automation Cadences

| Cadence | Activities |
|---------|-----------|
| Daily | Detect new high-value finance/admin/medical mail; surface urgent items |
| Weekly | Hygiene summary; reimbursement queue; stale waiting items; job follow-ups |
| Monthly | Finance digest; statement review; subscription audit; benefits review |
| Quarterly | Sport Francés reminder/handoff; deeper archive/cleanup; insurance/benefit review |

---

## 14. Risks

| Risk | Why it matters | Mitigation |
|------|---------------|------------|
| Wrong routing of claim | Could waste time or cause failed submission | Confidence + human review |
| Over-archiving | Useful mail disappears from surface | Preserve with labels; conservative first |
| False financial parsing | Bad analytics later | Retain evidence link; confidence score |
| Attachment variability | Docs may be hard to interpret | Phased ingestion; missing-doc states |
| Insurer policy ambiguity | Route may depend on actual policy details | Use user's docs as source of truth |
| Over-automation of messages | Could send wrong follow-up | Draft-first policy |
| Privacy leakage | Health/financial info is sensitive | Narrow exports, minimal exposure |

---

## 15. Metrics

### Outcome metrics
- Number of recovered reimbursement cases
- Estimated money recovered (CLP)
- Inbox unread reduction in high-value categories
- Number of finance emails correctly preserved and structured
- Number of stale claims surfaced before being forgotten
- Number of low-value promo threads moved out of inbox
- Number of recurring admin reminders actually completed

### Quality metrics
- Classification precision for finance/medical messages
- Extraction precision for amount/date/counterparty
- Missing-doc detection accuracy
- Reminder usefulness rate
- Unsubscribe recommendation acceptance rate

---

## 16. Initial Backlog

### P0
- [x] Write plan and PRD
- [x] Define label taxonomy
- [x] Define schemas
- [x] Create repo scaffolding
- [ ] Define sender rules
- [ ] Build reimbursement tracker spec
- [ ] Build financial event spec

### P1
- [ ] Implement Gmail classifier
- [ ] Implement structured trackers
- [ ] Implement calendar reminder rules
- [ ] Implement summaries
- [ ] Implement Sport Francés handoff helper

### P2
- [ ] Attachment parser
- [ ] Packet bundling
- [ ] Confidence scoring
- [ ] Benefit value scoring
- [ ] Unsubscribe advisor

### P3
- [ ] Dashboard
- [ ] Insurer-specific adapters
- [ ] Family template
- [ ] Cross-source reconciliation
- [ ] Agent approvals workflow

---

## 17. Repository Structure

```
bureaucracy-copilot/
├── README.md
├── PRD.md
├── PLAN.md
├── docs/
│   ├── architecture.md
│   ├── label-taxonomy.md
│   ├── insurer-routing.md
│   ├── data-model.md
│   ├── calendar-automation.md
│   ├── summaries.md
│   └── privacy-and-risk.md
├── schemas/
│   ├── medical_case.schema.json
│   ├── financial_event.schema.json
│   ├── reminder.schema.json
│   └── sender_rule.schema.json
├── rules/
│   ├── gmail_sender_rules.yaml
│   ├── medical_routes.yaml
│   ├── finance_classification.yaml
│   └── summary_rules.yaml
├── prompts/
│   ├── classify_email.md
│   ├── summarize_weekly_hygiene.md
│   ├── summarize_finance_monthly.md
│   ├── build_claim_case.md
│   └── draft_followup.md
├── src/
│   ├── ingestion/
│   ├── classification/
│   ├── medical/
│   ├── finance/
│   ├── calendar/
│   ├── summaries/
│   ├── outputs/
│   └── utils/
├── notebooks/
│   ├── reimbursement_exploration.ipynb
│   └── finance_exploration.ipynb
└── tests/
```

---

## 18. v1 Success Definition

v1 is successful if it achieves all of the following:

1. Finance and medical emails become structurally searchable
2. A reimbursement backlog tracker exists and is usable
3. Calendar follow-up logic exists
4. Weekly/monthly summaries reduce manual scanning
5. The system is ready for Codex / Claude implementation without redesign

---

## 19. Final Product Statement

This is not just an inbox organizer.
It is a **personal bureaucracy operating system** built on top of Gmail and Calendar.

If implemented well, it should:
- Save money
- Save time
- Reduce shame/friction around admin work
- Preserve long-term financial evidence
- Generalize into a broader family bureaucracy assistant
