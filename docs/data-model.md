# Data Model — Bureaucracy Copilot

## Overview

The system uses four core object types. All objects maintain an evidence link to their source email(s).

---

## 1. EmailRecord

Represents a single email message after classification.

```json
{
  "message_id": "string",
  "thread_id": "string",
  "from": "string",
  "to": ["string"],
  "subject": "string",
  "timestamp": "datetime",
  "labels": ["string"],
  "snippet": "string",
  "has_attachment": true,
  "attachment_names": ["string"],
  "classification": "Action|Pipeline|Records|Waiting|Feeds",
  "sub_labels": ["string"],
  "confidence": 0.0,
  "processed_at": "datetime"
}
```

**Fields:**
- `classification` — top-level class from FR-1
- `sub_labels` — full label paths from taxonomy (e.g. `BC/Records/Medical/Invoice`)
- `confidence` — classification confidence [0.0, 1.0]

---

## 2. MedicalCase

Represents a single reimbursement case. One case may span multiple emails.

```json
{
  "case_id": "string",
  "service_date": "date",
  "provider": "string",
  "expense_type": "consultation|lab|medication|hospitalization|dental|mental_health|other",
  "amount": 0,
  "currency": "CLP",
  "route": "esencial|bicevida|alemana|combined|unknown",
  "route_confidence": 0.0,
  "documents": {
    "invoice": false,
    "reimbursement_form": false,
    "prescription": false,
    "payment_proof": false,
    "esencial_confirmation": false,
    "additional_support": false
  },
  "status": "new|missing_docs|ready|submitted|pending|reimbursed|rejected",
  "source_emails": ["message_id"],
  "notes": "string",
  "next_action": "string",
  "follow_up_date": "date|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Status transitions:**
- `new` → `missing_docs` — when doc check fails
- `missing_docs` → `ready` — when all docs present
- `ready` → `submitted` — when claim is filed
- `submitted` → `pending` — awaiting insurer decision
- `pending` → `reimbursed` — money received
- `pending` → `rejected` — claim denied
- Any → `new` — if case is reopened

---

## 3. FinancialEvent

Represents a single financial transaction extracted from email evidence.

```json
{
  "event_id": "string",
  "event_date": "datetime",
  "counterparty": "string",
  "amount": 0,
  "currency": "CLP",
  "direction": "in|out",
  "account_source": "tenpo|bice|bice_inversiones|other",
  "event_type": "bank_transfer|payment|investment|subscription|salary|receipt|other",
  "source_email_id": "string",
  "has_attachment": true,
  "attachment_names": ["string"],
  "notes": "string",
  "created_at": "datetime"
}
```

**Extraction targets:**
- Tenpo transfer notifications
- BICE bank statements
- BICE Inversiones confirmations
- Online payment receipts
- Subscription charges
- Salary deposits

---

## 4. ReminderTask

Represents a calendar-linked follow-up task.

```json
{
  "task_id": "string",
  "related_object_type": "claim|finance_review|job|admin|sport_frances|quarterly",
  "related_object_id": "string",
  "title": "string",
  "description": "string",
  "scheduled_at": "datetime",
  "google_event_id": "string|null",
  "status": "scheduled|done|dismissed|rescheduled",
  "notes": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Storage

### v1 (JSON files)

```
data/
├── email_records.jsonl       # append-only log of classified emails
├── medical_cases.json        # dict: case_id → MedicalCase
├── financial_events.jsonl    # append-only log of financial events
├── reminder_tasks.json       # dict: task_id → ReminderTask
└── processed_ids.json        # set of already-processed message_ids
```

### v1.5+ (SQLite)

Tables mirror the schemas above with proper indexing on dates and statuses.

---

## ID Generation

- `case_id`: `case_YYYYMMDD_XXXX` (date + 4-char random)
- `event_id`: `fin_YYYYMMDD_XXXX`
- `task_id`: `task_YYYYMMDD_XXXX`

---

## Schema Files

JSON schemas for validation are in `schemas/`:
- `medical_case.schema.json`
- `financial_event.schema.json`
- `reminder.schema.json`
- `sender_rule.schema.json`
