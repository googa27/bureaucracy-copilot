# Calendar Automation — Bureaucracy Copilot

## Overview

Google Calendar serves as the time-based operational layer for the system. The calendar module creates, updates, and tracks events tied to bureaucracy tasks.

---

## Event Types

### 1. Claim Follow-Up Reminder

Triggered when a medical case has been submitted or is waiting.

**Title format:** `[BC] Follow up: {provider} claim ({route})`

**Description includes:**
- Case ID and status
- Amount expected
- Days since submission
- Next action

**Timing:**
- Created 7 days after submission
- Rescheduled +7 days if dismissed without action
- Marked done when claim is reimbursed or rejected

**Calendar:** Personal / BC Reminders

---

### 2. Weekly Hygiene Review Block

Recurring block to review inbox state and reimbursement queue.

**Title:** `[BC] Weekly bureaucracy review`

**Recurrence:** Weekly, Monday 9:00 AM (or user-configured time)

**Duration:** 30 minutes

**Description:** Link to weekly summary, open actions listed

---

### 3. Monthly Finance Review

Recurring block to review the monthly finance digest.

**Title:** `[BC] Monthly finance review — {Month YYYY}`

**Recurrence:** Monthly, first Monday of month

**Duration:** 30 minutes

**Description:** Link to monthly digest, balance summary

---

### 4. Quarterly Admin Review

Seasonal review block for benefits, subscriptions, and Sport Francés handoff.

**Title:** `[BC] Quarterly admin review — Q{N} {YYYY}`

**Recurrence:** Quarterly

**Duration:** 1 hour

**Description:**
- Benefits to renew
- Subscriptions to audit
- Sport Francés update
- Insurance coverage check

---

### 5. Sport Francés Handoff Reminder

Special recurring reminder tied to the Sport Francés club reimbursement cycle.

**Title:** `[BC] Sport Francés — submit quarterly reimbursement`

**Recurrence:** Quarterly (aligned with SF fiscal cycle)

**Duration:** 30 minutes

**Description:**
- What to submit
- Where to submit
- Estimated amount
- Link to relevant emails

---

### 6. Stale Case Alert

One-time event created when a claim has been pending for too long.

**Title:** `[BC] ALERT: Stale claim — {provider} ({days} days)`

**Trigger:** Claim in `submitted` or `pending` status for > 21 days

**Duration:** 15 minutes

---

## Calendar Configuration

| Setting | Default |
|---------|---------|
| Calendar name | "Bureaucracy Copilot" (or personal calendar) |
| Reminder | 30 minutes before event |
| Color | Tomato (red) for urgent, Sage (green) for reviews |
| Visibility | Private |

---

## Calendar API Operations

```python
# Create a follow-up reminder
create_event(
    calendar_id="primary",
    summary="[BC] Follow up: Clínica Alemana claim (esencial)",
    description="Case ID: case_20251201_ABCD\nStatus: submitted\nAmount: CLP 45,000\nNext action: Check portal",
    start=datetime.now() + timedelta(days=7),
    duration_minutes=15,
    reminders=[30]
)

# Create recurring review
create_recurring_event(
    summary="[BC] Weekly bureaucracy review",
    rrule="FREQ=WEEKLY;BYDAY=MO",
    start=next_monday_9am(),
    duration_minutes=30
)
```

---

## Reminder Status Tracking

Reminder tasks are tracked in the `ReminderTask` store:
- `scheduled` → event exists in calendar
- `done` → user marked complete or claim resolved
- `dismissed` → skipped once, rescheduled
- `rescheduled` → moved to later date

---

## Integration with Cases

When a MedicalCase status changes:
- `ready → submitted`: Create follow-up reminder for +7 days
- `pending` for >21 days: Create stale alert
- `reimbursed` or `rejected`: Mark reminder as done

---

## Privacy

- Calendar events contain enough context to act, but not full sensitive details
- No PHI (diagnoses, conditions) in event titles or descriptions
- Use case IDs as references, not provider/diagnosis names in titles
