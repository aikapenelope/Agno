---
name: whabi
description: Whabi - WhatsApp Business CRM for managing leads, clients, and messaging campaigns
metadata:
  version: "1.0.0"
  tags: ["crm", "whatsapp", "leads", "sales"]
---
# Whabi - WhatsApp Business CRM

Whabi is a WhatsApp Business CRM system for managing leads, clients, and messaging campaigns.

## Architecture
- **Database**: PostgreSQL (db: whabi) on Data Plane (10.0.1.20)
- **Cache**: Redis DB 0
- **Storage**: MinIO buckets: whabi-media, whabi-documents
- **Deployment**: Coolify on App Plane A (10.0.1.30)

## Key Concepts
- **Leads**: Potential clients who initiate contact via WhatsApp
- **Clients**: Converted leads with active service agreements
- **Campaigns**: Bulk messaging campaigns with templates
- **Media**: Images, documents, and voice messages stored in MinIO

## When to Use This Skill
- Analyzing Whabi leads or client data
- Planning WhatsApp messaging campaigns
- Researching WhatsApp Business API best practices
- Generating reports on lead conversion rates
- Creating CRM records in Twenty for Whabi contacts

## CRM Integration (Twenty)
- Create people records for new Whabi leads
- Track lead status and conversion pipeline
- Log interactions as notes on contact records
