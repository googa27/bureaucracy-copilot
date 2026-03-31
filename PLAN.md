# PLAN.md — Bureaucracy Copilot Implementation Plan

## Phase 1: Foundation (v1)

### 1.1 Repository and documentation scaffold
- [x] Create repo `bureaucracy-copilot`
- [x] Add PRD.md
- [ ] Add PLAN.md
- [ ] Add all docs/ files
- [ ] Add schemas/
- [ ] Add rules/
- [ ] Add prompts/

### 1.2 Gmail label taxonomy
- Define top-level label structure
- Map sender domains to labels
- Create filter rules spec

### 1.3 Schema definitions
- Email record schema
- Medical case schema
- Financial event schema
- Reminder / calendar task schema

### 1.4 Classification rules
- Sender rules YAML
- Medical route inference rules
- Finance classification rules

### 1.5 Prompt templates
- Email classification prompt
- Weekly hygiene summary prompt
- Finance monthly digest prompt
- Claim case builder prompt
- Follow-up draft prompt

---

## Phase 2: Core Implementation (v1 → v1.5)

### 2.1 Gmail classifier
- Read Gmail API
- Apply sender rules
- Apply classification prompt
- Label and archive

### 2.2 Medical case tracker
- Extract reimbursement-relevant emails
- Generate case objects
- Detect missing documents
- Infer insurer route

### 2.3 Financial event extractor
- Parse bank / payment / investment emails
- Create structured event records
- Preserve source email links

### 2.4 Calendar reminder system
- Create follow-up events for open claims
- Create recurring review blocks
- Create quarterly handoffs

### 2.5 Summary generation
- Weekly hygiene summary
- Reimbursement queue summary
- Monthly finance digest

---

## Phase 3: Automation Layer (v2)

### 3.1 Attachment ingestion
- PDF/image parsing for invoices
- Form recognition for reimbursement docs
- Confidence scoring

### 3.2 Claim packet bundling
- Gather all docs for a case
- Identify missing docs
- Prepare submission-ready packets

### 3.3 Draft generation
- Follow-up email drafts
- Insurer chase drafts
- Handoff messages

### 3.4 Benefit optimization engine
- Track available benefits
- Flag unused entitlements
- Estimate recoverable amounts

---

## Phase 4: Near-Full Automation (v3)

### 4.1 Agentic workflow
- Multi-agent pipeline: classify → case → calendar → summarize
- Human approval queue for outbound actions
- Retry and escalation flows

### 4.2 Insurer portal adapters
- Esencial portal automation
- BICE VIDA portal automation
- Alemana portal automation

### 4.3 Dashboard
- Claims state view
- Finance summary view
- Waiting queue view
- Family/multi-user view

---

## Implementation Priorities

| Priority | Component | Effort | Value |
|----------|-----------|--------|-------|
| P0 | Label taxonomy + rules | Low | High |
| P0 | Schema definitions | Low | High |
| P0 | Prompt templates | Medium | High |
| P1 | Gmail classifier | High | High |
| P1 | Medical case tracker | High | Critical |
| P1 | Financial event extractor | High | High |
| P1 | Calendar reminder system | Medium | High |
| P2 | Attachment ingestion | Very High | Medium |
| P2 | Claim packet bundler | High | High |
| P3 | Dashboard | Very High | Medium |
| P3 | Portal adapters | Very High | High |

---

## Technology Choices

### Core language
Python 3.11+

### Gmail integration
- Google Gmail API (read, label, archive, draft)
- OAuth2 for authentication

### Calendar integration
- Google Calendar API (create/read/update events)

### Data storage (v1)
- JSON files for cases and events
- SQLite for persistence in v1.5+

### AI/LLM layer
- Claude API (Anthropic) for classification and summarization
- Prompt templates in `prompts/` directory

### Future
- Google Drive API for document storage
- WhatsApp Business API or Twilio for notifications
- OCR via Google Document AI or AWS Textract

---

## File Creation Order

1. docs/architecture.md
2. docs/label-taxonomy.md
3. docs/insurer-routing.md
4. docs/data-model.md
5. docs/calendar-automation.md
6. docs/summaries.md
7. docs/privacy-and-risk.md
8. schemas/medical_case.schema.json
9. schemas/financial_event.schema.json
10. schemas/reminder.schema.json
11. schemas/sender_rule.schema.json
12. rules/gmail_sender_rules.yaml
13. rules/medical_routes.yaml
14. rules/finance_classification.yaml
15. rules/summary_rules.yaml
16. prompts/classify_email.md
17. prompts/summarize_weekly_hygiene.md
18. prompts/summarize_finance_monthly.md
19. prompts/build_claim_case.md
20. prompts/draft_followup.md
21. src/ placeholder files
22. notebooks/ placeholder files
