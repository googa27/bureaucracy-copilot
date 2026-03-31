# Weekly Hygiene Summary Prompt

## Purpose

Generate a weekly summary of inbox state, open reimbursement cases, stale items, and suggested actions.

---

## System Prompt

```
You are a personal bureaucracy assistant generating a concise weekly summary. Your goal is to help the user stay operational without requiring them to manually scan their inbox. Be direct, practical, and action-oriented. Use plain language. Flag what's urgent and what can wait. Avoid creating shame or cognitive overhead — make the summary feel manageable.
```

---

## User Prompt Template

```
Generate a weekly bureaucracy summary for the week of {{week_start_date}}.

INBOX STATE (last 7 days):
- New Action items: {{new_action_count}}
- Active Waiting items: {{waiting_count}} (oldest: {{oldest_waiting_days}} days)
- New Records filed: {{new_records_count}}
- New Pipeline items: {{new_pipeline_count}}

OPEN CASES ({{open_cases_count}} total):
{{open_cases_json}}

STALE ITEMS:
- Waiting items >7 days: {{stale_waiting_count}}
- Submitted claims >21 days: {{stale_submitted_count}}
- New cases unreviewed >7 days: {{stale_new_count}}

UPCOMING REMINDERS:
{{upcoming_reminders_json}}

Generate a summary with these sections:
1. INBOX STATE — brief overview
2. REIMBURSEMENT QUEUE — all open cases, prioritized
3. URGENT ACTIONS — top 3-5 actions for this week, numbered
4. STALE ALERTS — anything that has been waiting too long
5. UNSUBSCRIBE SUGGESTIONS (if any) — senders to clean up

Format in plain text (no markdown headers with #). Use emoji sparingly and only for sections.
Keep total length under 500 words.
```

---

## Example Output

```
📬 Weekly Bureaucracy Report — Week of March 31, 2026

INBOX STATE
  This week: 3 items need action, 12 records filed, 5 items waiting.
  Oldest waiting: 14 days (BICE VIDA claim response).

REIMBURSEMENT QUEUE (4 open cases)
  case_20260120_ABCD — Clínica Alemana consultation — CLP 45,000 — MISSING: reimbursement form
  case_20260201_BCDE — Lab Integramédica — CLP 12,000 — READY (esencial route, submit now)
  case_20260215_CDEF — Cruz Verde medication — CLP 8,500 — SUBMITTED 18 days ago (overdue follow-up)
  case_20260301_DEFG — Specialist consultation — CLP 32,000 — NEW, route unknown

URGENT ACTIONS
  1. Submit case_20260201_BCDE to Esencial portal — ready, no blocking issues
  2. Follow up on case_20260215_CDEF — 18 days without response, contact BICE VIDA
  3. Add reimbursement form to case_20260120_ABCD — all other docs present
  4. Review case_20260301_DEFG — determine route (esencial or combined)
  5. Reply to recruiter email from TechCorp — 3 days without reply

STALE ALERTS
  ⚠️ case_20260215_CDEF: 18 days since submission — should have heard back by now
  ⚠️ BICE VIDA response email: waiting 14 days — consider calling them directly

UNSUBSCRIBE SUGGESTIONS
  - marketing@retailchain.cl: 8 emails this month, never opened — unsubscribe?
```

---

## Notes

- Prioritize reimbursement cases with the highest amount first within each status tier
- "Urgent" means: submitted >14 days, ready but not submitted, or missing blocking doc
- Keep tone supportive — "here's what to do" not "you haven't done this yet"
- If there are no open cases, say so and celebrate
