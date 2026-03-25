---
name: directus-crm
description: Complete guide for Directus CRM — MCP tools, REST API, collections schema, data patterns, and automation flows. Load this skill to work with any CRM data.
metadata:
  version: "1.0.0"
  tags: [crm, directus, mcp, api, contacts, companies, conversations, tickets, payments]
---

# Directus CRM — Complete Reference

Directus is the data layer for NEXUS. All business data lives here: contacts, companies, conversations, tickets, payments, tasks, and events.

## Connection

```
URL: http://localhost:8055
Auth: Bearer DIRECTUS_TOKEN
REST API: http://localhost:8055/items/{collection}
Admin UI: http://localhost:8055
```

## Your MCP Tools

You have these MCP tools from @directus/content-mcp:

| Tool | What it does | When to use |
|------|-------------|-------------|
| `read-items` | Query any collection with filters | Look up contacts, search conversations, check tickets |
| `create-item` | Create a record in any collection | Add contacts, log conversations, create tasks |
| `update-item` | Update an existing record | Change ticket status, update lead score, edit contact |
| `read-collections` | List all collections | Discover what data exists |
| `read-fields` | Get field definitions for a collection | Understand field types before creating records |
| `read-flows` | List automation flows | Check what automations exist |
| `trigger-flow` | Execute a flow programmatically | Run bulk operations, trigger notifications |

## Your Direct Tools (faster, no MCP overhead)

| Tool | Collection | When to use |
|------|-----------|-------------|
| `save_contact` | contacts | Create/update a person |
| `save_company` | companies | Create a company |
| `log_conversation` | conversations | Log a chat/WhatsApp interaction |
| `log_support_ticket` | tickets | Log a support case |
| `confirm_payment` | payments | Record an approved payment |
| `escalate_to_human` | tasks + events | Create urgent task for human |

**Rule: Use direct tools for WRITING. Use MCP tools for READING/QUERYING.**

## Collections Schema

### contacts
```json
{
  "first_name": "Pedro",
  "last_name": "Gomez",
  "email": "pedro@empresa.com",
  "phone": "0412323123",
  "company": "uuid-of-company",
  "product": "whabi",
  "lead_score": 7,
  "status": "lead",
  "source": "whatsapp",
  "job_title": "Gerente",
  "city": "Caracas",
  "notes": "Interesado en plan pro"
}
```
- `product`: whabi | docflow | aurora
- `status`: lead | client | churned
- `source`: whatsapp | web | email | manual
- `company`: UUID reference to companies collection

### companies
```json
{
  "name": "Nala Labs",
  "domain": "nalabs.com",
  "industry": "technology",
  "employees": 25,
  "plan": "starter",
  "address": "Caracas, Venezuela",
  "notes": ""
}
```
- `plan`: free | starter | pro | enterprise

### conversations
```json
{
  "contact": "uuid-of-contact",
  "channel": "whatsapp",
  "direction": "inbound",
  "raw_message": "Hola, quiero saber el precio del plan pro",
  "agent_response": "El plan pro cuesta $49/mes...",
  "intent": "pricing",
  "sentiment": "positive",
  "lead_score": 7,
  "agent_name": "whabi-support"
}
```
- `channel`: whatsapp | web | email
- `direction`: inbound | outbound
- `sentiment`: positive | neutral | negative

### tickets
```json
{
  "contact": "uuid-of-contact",
  "product": "docflow",
  "intent": "bug-report",
  "summary": "El PDF no se genera correctamente",
  "resolution": "Se actualizo el generador de PDF",
  "urgency": "high",
  "status": "resolved"
}
```
- `urgency`: low | medium | high
- `status`: open | resolved | escalated

### payments
```json
{
  "contact": "uuid-of-contact",
  "company": "uuid-of-company",
  "amount": 49.00,
  "method": "transferencia",
  "reference": "REF-2026-001",
  "status": "approved",
  "approved_by": "nexus-agent",
  "product": "whabi"
}
```
- `status`: pending | approved | rejected

### tasks
```json
{
  "contact": "uuid-of-contact",
  "title": "Seguimiento: Pedro Gomez (Whabi)",
  "body": "Enviar cotizacion del plan pro",
  "status": "todo",
  "due_date": "2026-03-30T10:00:00",
  "source": "auto"
}
```
- `status`: todo | in_progress | done
- `source`: auto | manual

### events (audit trail)
```json
{
  "type": "whatsapp",
  "payload": {"phone": "0412323123", "message": "raw text", "timestamp": "..."},
  "contact": "uuid-of-contact"
}
```
- `type`: whatsapp | email | payment | ticket | escalation | contact_note | company_note | login

## MCP Query Patterns

### Find a contact by phone
```
read-items collection=contacts filter={"phone": {"_eq": "0412323123"}}
```

### Find a contact by name
```
read-items collection=contacts filter={"first_name": {"_contains": "Pedro"}}
```

### List all open tickets
```
read-items collection=tickets filter={"status": {"_eq": "open"}} sort=-date_created
```

### Get conversations for a contact
```
read-items collection=conversations filter={"contact": {"_eq": "uuid"}} sort=-date_created limit=10
```

### List high-score leads
```
read-items collection=contacts filter={"lead_score": {"_gte": 7}} sort=-lead_score
```

### Count conversations today
```
read-items collection=conversations filter={"date_created": {"_gte": "$NOW(-1 day)"}} aggregate={"count": "id"}
```

### Find companies by industry
```
read-items collection=companies filter={"industry": {"_contains": "tech"}}
```

### Get pending payments
```
read-items collection=payments filter={"status": {"_eq": "pending"}}
```

## Workflow Patterns

### New contact from WhatsApp
1. `save_contact(first_name, last_name, phone, source="whatsapp")`
2. If company mentioned: `save_company(name)`
3. After conversation: `log_conversation(channel="whatsapp", intent, sentiment, lead_score)`
4. If support issue: `log_support_ticket(product, intent, summary, urgency)`

### Payment flow
1. Client says they paid → `confirm_payment(product, client_name, amount, method, reference)`
2. System creates payment record (status=approved) + follow-up task
3. Admin reviews in Directus UI

### Escalation flow
1. Agent can't resolve → `escalate_to_human(product, client_name, reason, urgency)`
2. System creates urgent task + event log
3. Human sees task in Directus UI

### Lead qualification
| Score | Action |
|-------|--------|
| 1-3 | save_contact only |
| 4-6 | save_contact + log_conversation |
| 7-8 | save_contact + log_conversation + task (agendar demo) |
| 9-10 | save_contact + log_conversation + task (enviar cotizacion) |

## Directus Filter Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `_eq` | Equals | `{"status": {"_eq": "open"}}` |
| `_neq` | Not equals | `{"status": {"_neq": "resolved"}}` |
| `_contains` | Contains text | `{"first_name": {"_contains": "Pedro"}}` |
| `_gte` | Greater or equal | `{"lead_score": {"_gte": 7}}` |
| `_lte` | Less or equal | `{"amount": {"_lte": 100}}` |
| `_in` | In list | `{"product": {"_in": ["whabi", "docflow"]}}` |
| `_null` | Is null | `{"company": {"_null": true}}` |
| `_nnull` | Not null | `{"email": {"_nnull": true}}` |

## Products

| Product | Description | Redis DB | MinIO Buckets |
|---------|-------------|----------|---------------|
| **Whabi** | WhatsApp Business CRM | DB 0 | whabi-media, whabi-documents |
| **Docflow** | Electronic Health Records | DB 1 | docflow-documents |
| **Aurora** | Voice-first business PWA | DB 2 | aurora-assets |

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Bad or expired token | Regenerate token in Directus UI → User → Token → Save |
| 403 Forbidden | User lacks permission | Check role permissions in Directus Settings |
| 400 field error | Wrong field name | Use read-fields to check exact field names |
| Connection refused | Directus not running | `cd ~/directus-aikalabs && docker compose up -d` |

## Important Rules

1. **NEVER guess field names.** Use `read-fields` if unsure.
2. **ALWAYS use direct tools for writing** (save_contact, log_conversation, etc.) — they're faster and pre-formatted.
3. **Use MCP read-items for querying** — it supports filters, sorting, and aggregation.
4. **Log everything to events** — any significant action should create an event for audit trail.
5. **Link records with UUIDs** — when creating a conversation, include the contact UUID in the `contact` field.
6. **Status values are lowercase** — `todo` not `TODO`, `open` not `Open`.
