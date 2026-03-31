# Privacy and Risk — Bureaucracy Copilot

## Privacy Principles

### Minimal Data Exposure
- The system reads email content only to classify and extract structured data
- No email content is stored beyond snippets needed for case context
- No full email bodies are persisted in the data store
- Attachment content is referenced by name only (not stored locally in v1)

### Sensitive Data Handling
- Medical diagnoses, conditions, and lab values are never stored in structured fields
- Financial account numbers and card numbers are never extracted or stored
- RUT (Chilean national ID) numbers are never logged
- OAuth tokens are stored in OS credential store, not in repo or config files

### Audit Trail
- All structured objects reference source email IDs
- Source emails remain in Gmail (never deleted by the system)
- System-generated labels and archives are reversible

---

## Risk Register

### Risk 1: Wrong claim routing
**Likelihood:** Medium  
**Impact:** High  
**Mitigation:**
- Confidence scoring on route inference
- Human review step before submission
- Conservative default: mark as `unknown` if signals are weak

### Risk 2: Over-archiving important emails
**Likelihood:** Low  
**Impact:** High  
**Mitigation:**
- Conservative label-then-archive policy
- Labels preserve searchability
- Archiving is reversible
- Action items never auto-archived

### Risk 3: False financial event extraction
**Likelihood:** Medium  
**Impact:** Medium  
**Mitigation:**
- Source email preserved for audit
- Amounts flagged for human review if extraction confidence is low
- No financial decisions made automatically

### Risk 4: Privacy leakage to LLM
**Likelihood:** Low  
**Impact:** High  
**Mitigation:**
- Prompts use snippets and metadata, not full email bodies
- PII scrubbing before LLM calls (v1.5+)
- Anthropic API data handling reviewed
- No third-party LLMs used

### Risk 5: Credential exposure
**Likelihood:** Low  
**Impact:** Very High  
**Mitigation:**
- Credentials stored in environment variables
- OAuth tokens use OS keychain
- Never committed to repo (gitignore enforced)
- Tokens use minimal required scopes

### Risk 6: Sending wrong follow-up email
**Likelihood:** Low  
**Impact:** Medium  
**Mitigation:**
- Draft-first policy: all outbound emails are drafts
- Human review required before sending
- No auto-send in v1

### Risk 7: Attachment variability
**Likelihood:** High  
**Impact:** Low–Medium  
**Mitigation:**
- Phased ingestion: attachment parsing is v1.5+
- Missing-doc state explicitly tracked
- System degrades gracefully when attachment can't be parsed

---

## Data Minimization

| Data Type | Collected | Stored | Duration |
|-----------|-----------|--------|----------|
| Email metadata (from, subject, date) | Yes | Yes | Indefinitely |
| Email snippet | Yes | Yes | Indefinitely |
| Full email body | Yes (for classification) | No | Not persisted |
| Attachment content | No (v1) | No | — |
| Medical provider name | Yes | Yes | Indefinitely |
| Medical diagnosis | No | No | — |
| Financial amount | Yes | Yes | Indefinitely |
| Financial account number | No | No | — |
| RUT / national ID | No | No | — |

---

## Access Control

- Data files (`data/`) are gitignored
- OAuth credentials never committed
- API keys stored in environment variables
- Data directory permissions: 700 (owner only)

---

## Reversibility

All system actions are reversible:
- **Labels:** Can be removed via Gmail
- **Archives:** Can be unarchived via Gmail
- **Calendar events:** Can be deleted via Calendar
- **Structured data:** JSON files can be edited or reset

The system never permanently deletes emails. The only delete operation is unsubscribe (which is user-approved).

---

## Compliance Notes

- GDPR-adjacent: all data is the user's own data processed for personal use
- No data shared with third parties except:
  - Claude API (Anthropic) for classification prompts — mitigated by data minimization
  - Gmail API / Calendar API (Google) — user's own provider
- System is for single-user personal use in v1; multi-user requires additional privacy design
