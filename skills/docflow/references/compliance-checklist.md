# Docflow Compliance Checklist

## Document Intake
- [ ] Patient identity verified
- [ ] Document type classified (lab, prescription, imaging, clinical note)
- [ ] Date of service recorded
- [ ] Provider name and license number captured

## Data Handling
- [ ] PII encrypted at rest and in transit
- [ ] Access logged with user ID and timestamp
- [ ] No patient data in logs or error messages
- [ ] Retention period set per document type

## Retention Periods
| Document Type | Retention | Notes |
|---|---|---|
| Clinical notes | 10 years | From last visit |
| Lab results | 7 years | From date of result |
| Imaging | 10 years | From date of study |
| Prescriptions | 5 years | From date issued |
| Billing records | 7 years | From date of service |

## Audit Requirements
- Monthly access log review
- Quarterly compliance self-assessment
- Annual external audit
