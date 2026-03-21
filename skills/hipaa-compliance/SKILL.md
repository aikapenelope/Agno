---
name: hipaa-compliance
description: Health data compliance for Latin America — data protection laws, patient rights, document retention, audit requirements, and EHR regulations by country.
metadata:
  version: "1.0.0"
  tags: [compliance, health, hipaa, data-protection, ehr, latam]
---

# Health Data Compliance (Latin America)

Reference for Docflow support agents handling compliance questions.
Note: "HIPAA" is US-specific. Latam has its own regulations per country.

## Universal Rules (apply everywhere)

1. **Patient data is the patient's property** — they can request it anytime
2. **Explicit consent required** before collecting health data
3. **Encryption required** at rest and in transit
4. **Access logging** — every access to patient records must be logged
5. **Breach notification** — patients must be notified of data breaches
6. **Minimum necessary** — only access data needed for the task

## Document Retention by Type

| Document | Minimum Retention | Notes |
|----------|------------------|-------|
| Clinical notes | 10 years | From last visit date |
| Lab results | 7 years | From date of result |
| Imaging (X-ray, MRI) | 10 years | From date of study |
| Prescriptions | 5 years | From date issued |
| Billing records | 7 years | From date of service |
| Consent forms | Permanent | Never destroy |
| Audit logs | 5 years | From date of log entry |

## What to NEVER Do

- Never share patient data in chat messages (even with the patient)
- Never store patient identifiers in conversation logs
- Never confirm or deny a patient's existence to third parties
- Never send medical records via unencrypted email
- Never discuss specific patient cases without de-identification

## When to Escalate

ALWAYS escalate to a human when:
- Client asks about specific legal liability
- Client reports a data breach
- Client asks about cross-border data transfer
- Client wants to delete patient records (legal implications)
- Regulatory authority contacts the client

## Audit Checklist (for client self-assessment)

- [ ] All user accounts have unique credentials (no shared logins)
- [ ] Access logs are enabled and reviewed monthly
- [ ] Data is encrypted at rest (database) and in transit (HTTPS)
- [ ] Backup procedures are documented and tested quarterly
- [ ] Staff has completed data protection training this year
- [ ] Privacy notice is posted and patients sign consent forms
- [ ] Incident response plan exists and is tested annually
