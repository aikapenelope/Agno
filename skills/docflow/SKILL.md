---
name: docflow
description: Docflow - Electronic Health Records (EHR) system for medical document management
metadata:
  version: "1.0.0"
  tags: ["ehr", "healthcare", "documents", "medical"]
---
# Docflow - Electronic Health Records System

Docflow is an EHR system for managing medical documents, patient records, and clinical workflows.

## Architecture
- **Database**: PostgreSQL (db: docflow) on Data Plane (10.0.1.20)
- **Cache**: Redis DB 1
- **Storage**: MinIO bucket: docflow-documents
- **Deployment**: Coolify on App Plane A (10.0.1.30)

## Key Concepts
- **Patient Records**: Demographics, medical history, allergies
- **Documents**: Lab results, prescriptions, clinical notes, imaging reports
- **Workflows**: Document intake, review, approval, archival
- **Compliance**: HIPAA-aware data handling (PII guardrails active)

## When to Use This Skill
- Analyzing Docflow document workflows
- Researching EHR compliance requirements
- Planning document management improvements
- Generating reports on document processing metrics

## Important Notes
- Patient data is sensitive. Always apply PII guardrails.
- Never store or transmit unencrypted patient identifiers.
- Document retention policies vary by jurisdiction.
