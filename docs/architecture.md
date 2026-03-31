# Architecture — Bureaucracy Copilot

## Overview

The system is a layered AI operations pipeline built on top of Gmail and Google Calendar. It processes emails, extracts structured data, and drives automated reminders and summaries.

```
┌─────────────────────────────────────────────────────┐
│                   USER INTERFACES                    │
│   Gmail (labeled/filtered) │ Calendar │ Summaries   │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│               PIPELINE LAYER                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Ingestion│→│Classific.│→│ Routing  │            │
│  └──────────┘ └──────────┘ └────┬─────┘            │
│                                  │                  │
│  ┌──────────────────────────────▼──────────────┐   │
│  │              DOMAIN MODULES                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │ Medical  │ │ Finance  │ │  Calendar  │  │   │
│  │  │  Cases   │ │  Events  │ │  Reminders │  │   │
│  │  └──────────┘ └──────────┘ └────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │              OUTPUT LAYER                    │   │
│  │  Summaries │ Drafts │ Labels │ Events        │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. Ingestion Layer (`src/ingestion/`)

- Reads Gmail via API (OAuth2)
- Fetches new messages and existing inbox backlog
- Extracts headers, body, and attachment metadata
- Deduplicates against seen message IDs
- Produces raw `EmailRecord` objects

### 2. Classification Layer (`src/classification/`)

- Applies sender rules (YAML-defined)
- Calls LLM classifier (Claude API) with `prompts/classify_email.md`
- Assigns primary class: Action / Pipeline / Records / Waiting / Feeds
- Assigns sub-labels from taxonomy
- Applies Gmail labels and archives as appropriate

### 3. Medical Module (`src/medical/`)

- Detects reimbursement-relevant emails
- Generates or updates MedicalCase objects
- Performs route inference (Esencial / BICE VIDA / Alemana / combined / unknown)
- Checks document completeness
- Flags missing docs and sets next action
- Writes cases to structured store

### 4. Finance Module (`src/finance/`)

- Detects financial emails (bank, transfer, payment, investment, receipt)
- Extracts structured FinancialEvent objects
- Preserves link to source email
- Writes events to structured store

### 5. Calendar Module (`src/calendar/`)

- Reads open cases needing follow-up
- Creates or updates Google Calendar reminders
- Creates recurring review blocks (weekly, monthly, quarterly)
- Tracks reminder status

### 6. Summaries Module (`src/summaries/`)

- Generates weekly hygiene summary email
- Generates reimbursement queue summary
- Generates monthly finance digest
- Uses `prompts/summarize_weekly_hygiene.md` and `prompts/summarize_finance_monthly.md`

### 7. Outputs Layer (`src/outputs/`)

- Gmail label application
- Gmail draft creation
- Calendar event creation
- Summary delivery (email or console)

### 8. Utils (`src/utils/`)

- Gmail API client wrapper
- Calendar API client wrapper
- LLM API client wrapper
- Schema validators
- Logging and error handling

## Data Flow

```
Gmail → Ingestion → Classification → Labels applied
                                  ↓
                           Medical module → MedicalCase store → Calendar reminders
                           Finance module → FinancialEvent store
                           Summary module → Digest emails
```

## Storage (v1)

- JSON files in `data/` directory (gitignored for privacy)
- `data/cases.json` — all medical cases
- `data/events.json` — all financial events
- `data/reminders.json` — all calendar tasks
- `data/processed_ids.json` — seen message IDs

## External APIs

| API | Usage | Auth |
|-----|-------|------|
| Gmail API | Read/write email, labels, drafts | OAuth2 |
| Google Calendar API | Create/read/update events | OAuth2 |
| Claude API (Anthropic) | Classification, summarization, drafts | API key |

## Security and Privacy

- Credentials stored in environment variables (never in code)
- OAuth2 tokens stored in `~/.config/bureaucracy-copilot/`
- No sensitive data logged or exported to public surfaces
- All writes to Gmail/Calendar are opt-in and reviewed

## Cadence

| Job | Trigger |
|-----|---------|
| `ingest_and_classify` | Daily or on-demand |
| `process_medical` | Daily |
| `process_finance` | Daily |
| `sync_calendar` | Daily |
| `generate_weekly_summary` | Weekly (Monday) |
| `generate_finance_digest` | Monthly (1st) |
