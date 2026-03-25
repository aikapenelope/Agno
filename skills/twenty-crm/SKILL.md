---
name: twenty-crm
description: Complete guide for Twenty CRM REST API — exact field formats, data structures, and tool usage patterns verified against the live API.
metadata:
  version: "1.0.0"
  tags: [crm, twenty, api, rest, contacts, companies]
---

# Twenty CRM REST API Guide

Verified field formats from the live Twenty API (self-hosted, localhost:3000).
Use this when calling save_contact, save_company, or any Twenty CRM tool.

## Authentication

```
Base URL: http://localhost:3000/rest/
Header: Authorization: Bearer TWENTY_API_KEY
```

## Person (Contact) — POST /rest/people

### Correct format (verified):
```json
{
  "name": {
    "firstName": "Pedro",
    "lastName": "Gomez"
  },
  "emails": {
    "primaryEmail": "pedro@empresa.com",
    "additionalEmails": []
  },
  "phones": {
    "primaryPhoneNumber": "0412323123",
    "primaryPhoneCountryCode": "",
    "primaryPhoneCallingCode": "+58",
    "additionalPhones": []
  },
  "jobTitle": "Gerente",
  "city": "Caracas",
  "companyId": "uuid-de-la-empresa"
}
```

### WRONG formats (will fail with 400):
```
❌ { "firstName": "Pedro" }              → field doesn't exist at top level
❌ { "emails": [{"address": "..."}] }    → emails is NOT an array
❌ { "phones": [{"number": "..."}] }     → phones is NOT an array
```

### Key rules:
- `name` is ALWAYS an object with `firstName` and `lastName`
- `emails` is an object with `primaryEmail`, NOT an array
- `phones` is an object with `primaryPhoneNumber`, NOT an array
- `companyId` links to an existing company (use the UUID)

## Company — POST /rest/companies

### Correct format:
```json
{
  "name": "Nala Labs",
  "domainName": {
    "primaryLinkLabel": "",
    "primaryLinkUrl": "https://nalabs.com",
    "secondaryLinks": []
  },
  "employees": 25,
  "address": {
    "addressStreet1": "Av Principal",
    "addressCity": "Caracas",
    "addressCountry": "Venezuela"
  }
}
```

### Simple format (minimum required):
```json
{
  "name": "Nala Labs"
}
```

### Key rules:
- `name` is a simple string (NOT nested like people)
- `domainName` is an object with `primaryLinkUrl`, NOT a string
- `address` is an object with addressStreet1, addressCity, etc.
- `employees` is a number

## Task — POST /rest/tasks

```json
{
  "title": "Seguimiento: Pedro Gomez (Whabi)",
  "body": "Verificar pago y agendar demo",
  "status": "TODO"
}
```

Status values: `TODO`, `IN_PROGRESS`, `DONE`

## Note — POST /rest/notes

```json
{
  "title": "Conversacion: Pedro Gomez - Whabi",
  "body": "Cliente: Pedro Gomez\nProducto: Whabi\nIntent: pricing\nResumen: Pregunto por planes pro"
}
```

## GET Responses

### GET /rest/people
```json
{
  "data": {
    "people": [
      {
        "id": "uuid",
        "name": { "firstName": "Ivan", "lastName": "Zhao" },
        "emails": { "primaryEmail": "zhao@notion.com", "additionalEmails": [] },
        "phones": { "primaryPhoneNumber": "882261739", "primaryPhoneCallingCode": "+1" },
        "jobTitle": "",
        "city": "San Francisco",
        "companyId": "uuid-or-null",
        "createdAt": "2026-03-16T21:03:32.247Z"
      }
    ]
  },
  "totalCount": 6,
  "pageInfo": { "hasNextPage": false }
}
```

### GET /rest/companies
```json
{
  "data": {
    "companies": [
      {
        "id": "uuid",
        "name": "Notion",
        "domainName": { "primaryLinkUrl": "https://notion.com" },
        "employees": 400,
        "address": { "addressCity": "San Francisco", "addressCountry": "United States" },
        "createdAt": "2026-03-16T21:03:32.247Z"
      }
    ]
  },
  "totalCount": 8
}
```

## Tool Usage Patterns

### Creating a contact with company:
1. First create or find the company: `save_company(name="Nala Labs")`
2. Then create the person: `save_contact(first_name="Pedro", last_name="Gomez", phone="0412323123", company_name="Nala Labs")`

### Logging a support interaction:
1. Save contact info: `save_contact(first_name="Maria", last_name="Lopez", phone="+573001234567")`
2. If company mentioned: `save_company(name="Clinica Norte", industry="healthcare")`
3. After resolving: `log_support_ticket(product="docflow", intent="pricing", summary="...", resolution="...")`
4. End of conversation: `log_conversation(client_name="Maria Lopez", product="docflow", sentiment="positive", lead_score=7)`

### Lead scoring:
| Score | Meaning | Tool action |
|-------|---------|-------------|
| 1-3 | Browsing | save_contact only |
| 4-6 | Asked features/pricing | save_contact + log_support_ticket |
| 7-8 | Requested demo | save_contact + log_support_ticket + log_conversation(next_action="agendar demo") |
| 9-10 | Ready to buy | save_contact + log_support_ticket + log_conversation(next_action="enviar cotizacion") |

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 UNAUTHENTICATED | Bad API key or newline in key | Check key in ~/.zshrc, no trailing newline |
| 400 "doesn't have firstName field" | Using flat fields instead of nested | Use `name: { firstName, lastName }` |
| 400 on emails | Sending array instead of object | Use `emails: { primaryEmail: "..." }` |
| Connection refused | Twenty not running | Start Twenty (docker-compose up) |
