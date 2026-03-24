---
name: crm-patterns
description: Complete guide for Twenty CRM integration — REST API patterns, data structure, support workflow, and query patterns for Whabi/Docflow/Aurora.
metadata:
  version: "2.0.0"
  tags: [crm, twenty, contacts, pipeline, support, whatsapp]
---

# CRM Patterns (Twenty)

Reference for all agents that interact with Twenty CRM.
Twenty is accessed via direct REST API tools: save_contact, save_company,
log_conversation, log_support_ticket, confirm_payment, escalate_to_human.

## Twenty REST API

Base URL: http://localhost:3000/rest/
Auth: Bearer TWENTY_API_KEY

### Endpoints used by our tools

| Endpoint | Method | What it creates |
|----------|--------|-----------------|
| `/rest/people` | POST | Contact (person) |
| `/rest/companies` | POST | Company |
| `/rest/tasks` | POST | Task (follow-up) |
| `/rest/notes` | POST | Note (conversation log, ticket, payment) |

### Data Format

**Person (contact):**
```json
{
  "name": {"firstName": "Maria", "lastName": "Lopez"},
  "emails": [{"address": "maria@empresa.com"}],
  "phones": [{"number": "+573001234567"}],
  "jobTitle": "Gerente de Operaciones",
  "city": "Bogota"
}
```

**Company:**
```json
{
  "name": "Clinica Norte SAS",
  "domainName": "clinicanorte.com",
  "employees": 50
}
```

**Task:**
```json
{
  "title": "Seguimiento: Maria Lopez (Whabi)",
  "body": "Verificar acreditacion de pago",
  "status": "TODO"
}
```

**Note:**
```json
{
  "title": "Conversacion: Maria Lopez - Whabi (whatsapp)",
  "body": "Cliente: Maria Lopez\nProducto: Whabi\nIntent: pricing\n..."
}
```

## Support Agent Workflow

Every support conversation MUST follow this flow:

### 1. Identify the client (START of conversation)
```
Client says: "Hola, soy Maria Lopez de Clinica Norte"
→ save_contact(first_name="Maria", last_name="Lopez", company_name="Clinica Norte")
→ save_company(name="Clinica Norte", industry="healthcare")
```

### 2. Resolve the query
Handle the client's question using your product knowledge and skills.

### 3. If payment involved
```
Client says: "Ya hice la transferencia de $500"
→ confirm_payment(product="whabi", client_name="Maria Lopez", amount="500", method="transferencia")
→ PAUSES for admin approval in /approvals page
→ After approval: payment logged in Twenty as note + follow-up task
```

### 4. Log the interaction (ALWAYS)
```
→ log_support_ticket(product="whabi", intent="pricing", summary="...", resolution="...", lead_score=7)
```

### 5. Log the conversation (END of conversation)
```
→ log_conversation(
    client_name="Maria Lopez",
    product="whabi",
    channel="whatsapp",
    summary="Pregunto por precios del plan pro, interesada en demo",
    intent="pricing",
    sentiment="positive",
    lead_score=7,
    next_action="Agendar demo para la proxima semana"
  )
```

### 6. If escalation needed
```
→ escalate_to_human(product="whabi", reason="Disputa de pago", client_name="Maria Lopez")
→ Creates urgent task in Twenty for human team
```

## Data Organization

### People (contacts)
Every contact should have:
- **Name**: first + last name
- **Phone**: with country code (+57...)
- **Email**: if available
- **Company**: mentioned in notes
- **Job title**: if mentioned

### Companies
- **Name**: legal or commercial name
- **Domain**: website if mentioned
- **Industry**: healthcare, retail, services, etc.

### Tasks (follow-ups)
Created automatically by tools when:
- Payment confirmed → "Seguimiento pago: ..."
- High urgency ticket → "Follow-up: ..."
- Escalation → "ESCALACION: ..."
- Conversation with next_action → "Seguimiento: ..."

### Notes (everything else)
Every interaction creates a note:
- Payment confirmations
- Support tickets
- Conversation summaries
- Escalation audit trail
- Contact context (product interest, lead score)

## Lead Scoring

Apply when someone asks about buying:

| Score | Meaning | Action |
|-------|---------|--------|
| 1-3 | Just browsing | Log, no follow-up |
| 4-6 | Asked about features/pricing | Log, optional follow-up |
| 7-8 | Requested demo or pricing details | Log + create follow-up task |
| 9-10 | Ready to buy, asked for invoice | Log + urgent follow-up task |

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "TWENTY_API_KEY not configured" | Missing env var | Set TWENTY_API_KEY in ~/.zshrc |
| "Twenty 401" | Invalid API key | Regenerate key in Twenty settings |
| "Twenty connection failed" | Twenty not running | Start Twenty (docker-compose up) |
| "Twenty 400" | Invalid data format | Check field names match Twenty schema |

## What Shows in nexus-ui

Everything created by these tools appears in the `/crm` page:
- **Contactos tab**: all people from Twenty
- **Empresas tab**: all companies
- **Tareas tab**: all tasks (follow-ups, escalations)
- **Notas tab**: all notes (conversations, tickets, payments)
- **Agente CRM tab**: chat with Automation Agent for complex queries
