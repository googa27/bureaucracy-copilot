# Label Taxonomy — Bureaucracy Copilot

## Overview

Gmail labels are organized in a hierarchical namespace. All custom labels use the prefix `BC/` (Bureaucracy Copilot) to keep them visually grouped and not pollute the user's existing label space.

---

## Top-Level Categories

| Label | Description |
|-------|-------------|
| `BC/Action` | Items requiring user action now |
| `BC/Pipeline` | Job search, career, recruiter threads |
| `BC/Records` | Important documents and receipts to keep |
| `BC/Waiting` | Sent items awaiting reply / pending claims |
| `BC/Feeds` | Newsletters, marketing, digests (low priority) |

---

## Sub-Label Taxonomy

### BC/Records/Medical
- `BC/Records/Medical/Invoice` — Medical invoices (boletas)
- `BC/Records/Medical/Reimbursement` — Claim forms and reimbursement docs
- `BC/Records/Medical/Appointment` — Appointment confirmations
- `BC/Records/Medical/Prescription` — Drug prescriptions
- `BC/Records/Medical/Lab` — Lab results and reports
- `BC/Records/Medical/Insurance` — Insurance policy documents

### BC/Records/Finance
- `BC/Records/Finance/Bank` — Bank statements and notifications
- `BC/Records/Finance/Transfer` — Transfer confirmations (Tenpo, BICE, etc.)
- `BC/Records/Finance/Investment` — Investment confirmations and statements
- `BC/Records/Finance/Receipt` — Purchase receipts
- `BC/Records/Finance/Subscription` — Subscription bills
- `BC/Records/Finance/Transport` — Transport charges (Uber, metro cards, etc.)
- `BC/Records/Finance/Tax` — Tax documents

### BC/Records/Admin
- `BC/Records/Admin/Government` — SII, Registro Civil, ChileAtiende
- `BC/Records/Admin/Legal` — Contracts, legal notices
- `BC/Records/Admin/Utilities` — Bills for electricity, internet, etc.
- `BC/Records/Admin/Housing` — Rent, condo, building admin

### BC/Records/Career
- `BC/Records/Career/Contract` — Employment contracts, offer letters
- `BC/Records/Career/Payslip` — Salary slips and liquidaciones
- `BC/Records/Career/Benefits` — Benefit confirmations and enrollment

### BC/Pipeline/Jobs
- `BC/Pipeline/Jobs/Recruiter` — Recruiter outreach
- `BC/Pipeline/Jobs/Application` — Applications sent
- `BC/Pipeline/Jobs/Interview` — Interview scheduling and prep
- `BC/Pipeline/Jobs/Offer` — Offers and negotiations
- `BC/Pipeline/Jobs/Rejection` — Rejection notices

### BC/Waiting
- `BC/Waiting/Claim` — Submitted insurance claims awaiting response
- `BC/Waiting/Reply` — Emails sent awaiting reply
- `BC/Waiting/Document` — Requested documents not yet received

### BC/Feeds
- `BC/Feeds/Newsletter` — Email newsletters
- `BC/Feeds/Marketing` — Promotional emails
- `BC/Feeds/Digest` — Aggregated feed emails
- `BC/Feeds/Social` — Social platform notifications

### BC/Action
- `BC/Action/Urgent` — Needs attention today
- `BC/Action/ThisWeek` — Needs attention this week
- `BC/Action/Review` — Needs review (documents, statements)

---

## Archiving Policy

| Label | Archive? | Notes |
|-------|----------|-------|
| BC/Action | No | Stays in inbox until actioned |
| BC/Pipeline | No | Stays in inbox while active |
| BC/Records | Yes | Archive after labeling |
| BC/Waiting | No | Stays surfaced for follow-up |
| BC/Feeds | Yes | Archive immediately |

---

## Gmail Filter Rules

Filters are defined in `src/utils/assets/rules/gmail_sender_rules.yaml` and map sender domains / patterns to labels.

Examples:
- `bicevidavida.cl` → `BC/Records/Medical/Insurance`
- `esencialapp.cl` → `BC/Records/Medical/Insurance`
- `clinicaalemana.cl` → `BC/Records/Medical/Appointment`
- `tenpo.cl` → `BC/Records/Finance/Transfer`
- `biceinversiones.cl` → `BC/Records/Finance/Investment`
- `linkedin.com` → `BC/Pipeline/Jobs/Recruiter`
- `sii.cl` → `BC/Records/Admin/Government`

---

## Label Colors (suggested)

| Label | Color |
|-------|-------|
| BC/Action | Red |
| BC/Pipeline | Blue |
| BC/Records | Green |
| BC/Waiting | Yellow |
| BC/Feeds | Gray |
