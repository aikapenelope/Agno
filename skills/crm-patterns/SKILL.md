---
name: crm-patterns
description: Patterns for using Twenty CRM effectively — pipeline structure, tagging conventions, query patterns, and data organization for Whabi/Docflow/Aurora contacts.
metadata:
  version: "1.0.0"
  tags: [crm, twenty, contacts, pipeline, tags, queries]
---

# CRM Patterns (Twenty)

Reference for Dash and Automation Agent when working with Twenty CRM data.
Twenty is accessed via MCP tools: search_records, list_people, list_companies,
create_person, create_company, create_task, create_note.

## Data Organization

### People (contacts)
Every contact should have:
- **Name**: full name
- **Phone**: with country code (+57...)
- **Email**: if available
- **Company**: linked to company record
- **Tags**: product (whabi/docflow/aurora), status (lead/client/churned)
- **Notes**: interaction history, preferences

### Companies (clients)
Every company should have:
- **Name**: legal or commercial name
- **Industry**: healthcare, retail, services, etc.
- **Product**: which AikaLabs product they use
- **Plan**: free/starter/pro/enterprise
- **MRR**: monthly recurring revenue

### Tasks (follow-ups)
- **Title**: action-oriented ("Follow up with Dr. Garcia about Docflow demo")
- **Due date**: specific date, not "soon"
- **Assigned to**: who is responsible
- **Status**: todo/in_progress/done
- **Related to**: linked to person or company

## Tagging Convention

Tags are the universal connector. Use consistently:

| Tag | Meaning |
|-----|---------|
| `whabi` | Related to Whabi product |
| `docflow` | Related to Docflow product |
| `aurora` | Related to Aurora product |
| `lead` | Potential client, not yet paying |
| `client` | Active paying client |
| `churned` | Former client |
| `hot-lead` | Lead score 7+ |
| `enterprise` | Large company, custom pricing |
| `support-escalation` | Had a support issue escalated to human |

## Common Query Patterns

### "How many leads this week?"
```
search_records(query="lead") → filter by created_at > 7 days ago
```

### "Which clients use Docflow?"
```
search_records(query="docflow client")
```

### "Show me hot leads"
```
search_records(query="hot-lead")
```

### "What tasks are overdue?"
```
list_tasks(status="todo") → filter by due_date < today
```

## Analytics Patterns (for Dash)

When computing metrics, always:
1. Query the raw data from Twenty
2. Use Calculator or Python to compute
3. Compare to previous period
4. Explain what the number means

Common metrics:
- **Lead velocity**: new leads this week vs last week
- **Conversion rate**: leads → clients / total leads
- **Response time**: average time to first response (from notes timestamps)
- **Churn rate**: churned clients / total clients this month
- **MRR growth**: this month MRR vs last month
