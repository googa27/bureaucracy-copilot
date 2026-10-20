# Build Claim Case Prompt

## Purpose

Extract and structure a medical reimbursement case from one or more related emails.

---

## System Prompt

```
You are a medical reimbursement case builder. Your job is to extract structured case data from email evidence. Be conservative: only populate fields you have evidence for. Use null for unknown fields. Infer the route based on available signals (sender domain, keywords, provider name). Flag which documents appear to be present and which are missing. Output valid JSON only.
```

---

## User Prompt Template

```
Build a medical reimbursement case from these emails.

EMAILS:
{{emails_json}}

Extract the following case data:

{
  "case_id": "GENERATE: case_YYYYMMDD_XXXX format",
  "service_date": "YYYY-MM-DD or null if unknown",
  "provider": "clinic/pharmacy/lab name or null",
  "expense_type": "consultation|lab|medication|hospitalization|dental|mental_health|imaging|other",
  "amount": number or null,
  "currency": "CLP",
  "route": "esencial|bicevida|alemana|combined|unknown",
  "route_confidence": 0.0 to 1.0,
  "documents": {
    "invoice": true/false,
    "reimbursement_form": true/false,
    "prescription": true/false,
    "payment_proof": true/false,
    "esencial_confirmation": true/false,
    "additional_support": true/false
  },
  "status": "new|missing_docs|ready",
  "notes": "brief summary of what was found",
  "next_action": "what the user should do next",
  "follow_up_date": "YYYY-MM-DD or null",
  "source_emails": ["message_id1", "message_id2"]
}

Rules for status:
- Set to "ready" only if all required documents for the route are present
- Set to "missing_docs" if any required document is absent
- Set to "new" if there's not enough information to determine completeness

Required documents by route:
- esencial: invoice, reimbursement_form
- bicevida: invoice, reimbursement_form  
- combined: invoice, reimbursement_form, esencial_confirmation
- medication (any route): prescription required
```

---

## Example Input

```json
[
  {
    "message_id": "msg_001",
    "from": "reservas@clinicaalemana.cl",
    "subject": "Confirmación de cita médica - Dr. Fernández",
    "date": "2026-02-10",
    "snippet": "Su cita con el Dr. Fernández el 14 de febrero ha sido confirmada. Valor consulta: $45.000."
  },
  {
    "message_id": "msg_002",
    "from": "billing@clinicaalemana.cl",
    "subject": "Boleta N°12345 - Clínica Alemana",
    "date": "2026-02-14",
    "snippet": "Adjunto boleta por consulta médica. Total: CLP 45.000. Fecha: 14/02/2026.",
    "has_attachment": true,
    "attachment_names": ["boleta_12345.pdf"]
  }
]
```

## Example Output

```json
{
  "case_id": "case_20260214_ABCD",
  "service_date": "2026-02-14",
  "provider": "Clínica Alemana",
  "expense_type": "consultation",
  "amount": 45000,
  "currency": "CLP",
  "route": "esencial",
  "route_confidence": 0.75,
  "documents": {
    "invoice": true,
    "reimbursement_form": false,
    "prescription": false,
    "payment_proof": false,
    "esencial_confirmation": false,
    "additional_support": false
  },
  "status": "missing_docs",
  "notes": "Appointment confirmation and invoice found. Invoice in attachment msg_002. Reimbursement form not found.",
  "next_action": "Download reimbursement form from Esencial portal and attach to this case",
  "follow_up_date": "2026-02-21",
  "source_emails": ["msg_001", "msg_002"]
}
```

---

## Notes

- If the amount appears in attachment but not in snippet, set amount to null with a note
- If multiple expenses are in the same email thread, create separate cases
- Alemana cases may use alemana route even if no explicit insurer signal, based on sender domain
- Always set a follow_up_date 7 days from today for new and missing_docs cases
