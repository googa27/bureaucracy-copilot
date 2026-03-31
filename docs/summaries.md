# Summaries — Bureaucracy Copilot

## Overview

The system generates three types of automated summaries to keep the user operational without manual inbox scanning.

---

## 1. Weekly Hygiene Summary

**Cadence:** Weekly (Monday morning)

**Delivery:** Email to user, or Markdown file

**Template:** `prompts/summarize_weekly_hygiene.md`

### Sections

#### 1.1 Inbox State
- Messages newly received in each category (Action, Records, Waiting, Feeds)
- Count of items still in Action queue
- Count of Waiting items and how long they've been waiting

#### 1.2 Reimbursement Queue
- Open cases by status (new, missing_docs, ready, submitted, pending)
- Cases with next action due this week
- Cases past their follow-up date

#### 1.3 Stale Items
- Waiting items >7 days without response
- Cases in `submitted` status >21 days
- Cases in `pending` status >30 days

#### 1.4 Suggested Actions
- Top 3–5 items the user should address this week
- Prioritized by: urgency > value > staleness

#### 1.5 Unsubscribe Suggestions
- Senders delivering high volume with no user action
- Estimated inbox noise reduction

### Example Output

```
📬 Weekly Bureaucracy Report — Week of March 31, 2026

INBOX STATE
  Action: 3 items need attention
  Waiting: 5 items (oldest: 14 days)
  Records: 12 new items filed this week

REIMBURSEMENT QUEUE
  Open cases: 4
    - case_20260120_ABCD: Clínica Alemana consultation — MISSING: reimbursement form
    - case_20260201_BCDE: Lab results — READY to submit (esencial route)
    - case_20260215_CDEF: Medication — SUBMITTED 18 days ago (follow up now)
    - case_20260301_DEFG: Specialist — NEW, needs review

URGENT ACTIONS
  1. Submit case_20260201_BCDE to Esencial (ready, no action taken)
  2. Follow up on case_20260215_CDEF (18 days since submission)
  3. Review case_20260301_DEFG (new, unclassified)

UNSUBSCRIBE SUGGESTIONS
  - marketing@retailchain.cl: 12 emails, 0 opens this month → Unsubscribe?
```

---

## 2. Reimbursement Queue Summary

**Cadence:** Embedded in weekly summary, or on-demand

**Purpose:** Single-screen view of all reimbursement cases

### Format

| Case ID | Date | Provider | Amount | Route | Status | Next Action | Due |
|---------|------|----------|--------|-------|--------|-------------|-----|
| case_20260120_ABCD | Jan 20 | Clínica Alemana | $45,000 | esencial | missing_docs | Add form | ASAP |
| case_20260201_BCDE | Feb 01 | Lab Integramédica | $12,000 | esencial | ready | Submit | Now |
| case_20260215_CDEF | Feb 15 | Farmacias Cruz Verde | $8,500 | bicevida | submitted | Follow up | Mar 8 |

---

## 3. Monthly Finance Digest

**Cadence:** Monthly (first Monday of month)

**Template:** `prompts/summarize_finance_monthly.md`

### Sections

#### 3.1 Summary Stats
- Total out: sum of all outgoing financial events
- Total in: sum of all incoming events
- Net: in - out

#### 3.2 By Category
- Medical spend (pre-reimbursement)
- Transport spend
- Subscriptions
- Investments / savings
- Other

#### 3.3 Reimbursements Received
- Amounts received from Esencial and BICE VIDA this month
- Net medical spend (after reimbursements)

#### 3.4 Subscription Audit
- Active recurring charges detected
- Estimated monthly total
- Flag unused or duplicate subscriptions

#### 3.5 Benefits Review
- Benefits available but not used this period
- Estimated value of unused benefits

### Example Output

```
💰 Finance Digest — February 2026

SUMMARY
  Total out: CLP 1,240,000
  Total in:  CLP 1,850,000 (includes salary)
  Net:       CLP +610,000

MEDICAL SPEND
  Gross: CLP 65,000
  Reimbursements received: CLP 28,000
  Net medical: CLP 37,000

SUBSCRIPTIONS (detected)
  - Spotify: CLP 4,990/mo
  - Netflix: CLP 8,990/mo
  - GitHub Pro: CLP 12,000/mo
  Total: CLP 25,980/mo

BENEFITS NOT USED
  - Annual dental checkup (BICE VIDA): available, not used this quarter
  - Gym reimbursement (employer): CLP 30,000/quarter available
```

---

## Delivery Methods

| Method | v1 | v2+ |
|--------|----|-----|
| Console/stdout | ✅ | ✅ |
| Email (Gmail draft) | ✅ | ✅ |
| Notion / Google Doc | — | ✅ |
| WhatsApp | — | ✅ |
| Dashboard | — | v3 |

---

## Prompt Templates

See `prompts/` directory for the LLM prompt templates used to generate summaries.
