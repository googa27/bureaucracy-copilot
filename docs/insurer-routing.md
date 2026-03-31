# Insurer Routing — Bureaucracy Copilot

## Overview

Medical reimbursements in Chile flow through multiple routes depending on the type of expense, the provider, and the insurance plan. This document defines the routing logic for the Bureaucracy Copilot system.

---

## Insurer Entities

### Esencial (Isapre)
- **Type:** Isapre (mandatory health insurance)
- **Coverage:** Hospitalization, specialists, labs, some medications
- **Portal:** esencialapp.cl / app
- **Reimbursement form:** Formulario de Reembolso Esencial
- **Deadline:** Generally 30 days from service date
- **Key identifiers:** sender domains `esencial.cl`, `esencialapp.cl`

### BICE VIDA (Complementary Insurance)
- **Type:** Complementary health insurance (seguro complementario)
- **Coverage:** Co-pays, deductibles, outpatient expenses not fully covered by isapre
- **Portal:** portal.bicevida.cl
- **Reimbursement form:** Formulario de Reembolso BICE VIDA
- **Deadline:** Generally 90 days from service date
- **Key identifiers:** sender domains `bicevida.cl`, `bicevidavida.cl`

### Clínica Alemana (Internal insurance / convenio)
- **Type:** Clinic-internal coverage or convenio
- **Coverage:** Expenses within Clínica Alemana facilities
- **Portal:** clinicaalemana.cl
- **Reimbursement:** Often handled at the clinic directly
- **Key identifiers:** sender domains `clinicaalemana.cl`

---

## Routing Logic

### Route: Esencial only
Apply when:
- Service is a hospitalization or surgery
- Provider is in the isapre network
- No complementary insurance applies
- Amount is below deductible threshold

### Route: BICE VIDA only  
Apply when:
- Service is outpatient and fully non-reimbursable by isapre
- Or isapre has already reimbursed its portion and BICE VIDA covers the remainder

### Route: Combined (Esencial → BICE VIDA)
Apply when:
- Service is covered by both isapre and complementary insurance
- Standard flow: submit to Esencial first, get reimbursement letter, then submit to BICE VIDA
- Required docs: invoice + Esencial reimbursement confirmation + BICE VIDA form

### Route: Alemana
Apply when:
- Service is at Clínica Alemana
- Covered under a clinic convenio
- Route is handled by clinic billing directly

### Route: Unknown
Apply when:
- Insufficient information to determine route
- Case needs manual review

---

## Document Requirements by Route

| Route | Invoice | Isapre Form | Esencial Proof | BICE Form | Prescription | Other |
|-------|---------|-------------|----------------|-----------|--------------|-------|
| Esencial | Required | Required | — | — | If medication | — |
| BICE VIDA | Required | — | — | Required | If medication | — |
| Combined | Required | Required | Required | Required | If medication | — |
| Alemana | Depends | — | — | — | — | Clinic-specific |

---

## Classification Signals

The system infers the likely route based on:

1. **Sender domain** — clinic or insurer domain in the email
2. **Subject keywords** — "reembolso", "reimbursement", "bono", "bonificación"
3. **Amount** — large amounts more likely to need combined route
4. **Provider name** — known network providers vs. non-network
5. **Expense type** — medication vs. procedure vs. lab vs. consultation

---

## Confidence Levels

| Signal | Confidence boost |
|--------|-----------------|
| Known insurer domain in sender | +High |
| Reimbursement keyword in subject | +Medium |
| Known provider name | +Medium |
| Amount matches typical range | +Low |
| No matching signals | Unknown |

---

## Edge Cases

- **Dental** — usually not covered by isapre, may be covered by BICE VIDA or separate dental insurance
- **Mental health** — psychologist sessions partially covered; check plan limits
- **Medications** — covered if prescribed; prescription required for both routes
- **Emergency abroad** — different process, may require travel insurance claim
- **Pre-existing conditions** — may be excluded; check plan details

---

## Rule File

Routes are configured in `rules/medical_routes.yaml`.
