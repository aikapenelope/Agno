# AGENTS.md — NEXUS Production Architecture

Instructions for AI agents and humans working on this codebase.

---

## System Overview

NEXUS is a multi-agent system for AikaLabs with 46 agents, 7 teams, 7 workflows, and 24 skills.
It serves 3 products: Whabi (WhatsApp CRM), Docflow (EHR), Aurora (voice PWA).

**Stack:** Agno framework + AgentOS + MiniMax M2.7 (primary) + OpenAI via OpenRouter (reasoning/learning)
**CRM:** Twenty CRM (localhost:3000) — direct REST API, no MCP/n8n intermediary
**Frontend:** Next.js + CopilotKit v2 + React Flow (16 pages)
**Database:** SQLite (dev), LanceDB (vectors), Twenty (CRM)

---

## Model Strategy (Hybrid)

| Model | Use | Cost |
|-------|-----|------|
| **MiniMax M2.7** (subscription) | 40 agents + 4 team routers + compression | $0/token |
| **GPT-5-mini** (OpenRouter) | 2 agents with reasoning (Knowledge, Code Review) | $0.25/$2.00 per 1M |
| **GPT-4o-mini** (OpenRouter) | LearningMachine (user_memory extraction) | $0.15/$0.60 per 1M |
| **GPT-5-nano** (OpenRouter) | Followup suggestions | $0.05/$0.40 per 1M |

### MiniMax Incompatibilities

| Feature | Status | Alternative |
|---------|--------|-------------|
| `response_format: json_object` | Error 2013 | Use tool calling (AGENTIC mode) |
| `output_schema` | Produces raw JSON | Use instructions for format |
| `reasoning=True` | Needs structured output | Use GPT-5-mini for reasoning agents |

---

## Team Architecture

```
NEXUS Master (father team, route mode)
├── 12 individual agents (simple requests)
├── Cerebro (route: research + knowledge + automation)
├── Content Factory (route: trend scout + scriptwriter + analytics)
├── Product Development (coordinate: PM + UX + tech writer)
├── Creative Studio (route: image gen + video gen + media describer)
└── Marketing Latam (coordinate: copywriter ES + SEO + social media)

WhatsApp Support (independent, route mode)
├── Whabi Support
├── Docflow Support
├── Aurora Support
└── General Support
```

### Team Rules (learned from production)

| Setting | Value | Why |
|---------|-------|-----|
| `respond_directly=True` | All teams | Stop after routing, return member response |
| `tool_call_limit=1` | All teams | Force exactly ONE tool call (delegate_task_to_member) |
| No `learning` on teams | All teams | Extra tools confuse routing |
| No `pre_hooks` on teams | All teams | Guardrails block before routing |
| `show_members_responses=False` | All teams | With respond_directly, this is redundant |

---

## Learning Configuration

Two configs, matching Agno official patterns:

**_learning (minimal)** — 13 agents (research, content, scouts)
- Only `learned_knowledge` in AGENTIC mode (2 tools: search_learnings, save_learning)

**_learning_full** — 8 agents (Pal, Dash, support agents, onboarding, invoice)
- user_profile + user_memory + entity_memory + learned_knowledge + decision_log
- All AGENTIC mode (agent decides when to update, 0-2 calls per conversation)

**NEVER use ALWAYS mode** — causes 100+ LLM calls per request (784K tokens).

---

## CRM Integration (Twenty)

Direct REST API calls to Twenty CRM (localhost:3000). No MCP, no n8n.

### Support Tools (6 total)

| Tool | What it does | Twenty action |
|------|-------------|---------------|
| `save_contact` | Save client info | Creates person + note |
| `save_company` | Save company info | Creates company + note |
| `log_conversation` | Log conversation summary | Creates note + follow-up task |
| `log_support_ticket` | Log support interaction | Creates note + task (if urgent) |
| `confirm_payment` | Confirm payment (@approval) | Creates note + task (after approval) |
| `escalate_to_human` | Escalate to human | Creates urgent task + note |

### Support Agent Flow

```
1. Client writes (WhatsApp/chat)
2. Agent identifies client → save_contact
3. If company mentioned → save_company
4. Agent resolves query
5. If payment → confirm_payment (admin approves in /approvals)
6. log_support_ticket (intent, resolution, lead score)
7. log_conversation (summary, sentiment, next action)
8. Everything visible in /crm page of nexus-ui
```

---

## Frontend (nexus-ui)

16 pages, all connected to AgentOS REST API + Twenty CRM:

| Page | Data source |
|------|-------------|
| `/` Dashboard | GET /agents, /teams, /sessions, /approvals/count |
| `/topology` | GET /agents, /teams, /workflows (React Flow) |
| `/chat` | POST /teams/nexus/runs (followups, approvals, file upload) |
| `/agents` | GET /agents + POST /agents/{id}/runs |
| `/teams` | GET /teams + POST /teams/{id}/runs |
| `/workflows` | GET /workflows + POST /workflows/{id}/runs |
| `/approvals` | GET /approvals + POST /approvals/{id}/resolve |
| `/traces` | GET /traces |
| `/history` | GET /sessions + /sessions/{id}/runs |
| `/knowledge` | GET /knowledge/content + search + upload |
| `/memory` | GET /memory + DELETE |
| `/analytics` | GET /metrics + /traces |
| `/whatsapp` | Mock (needs webhook) |
| `/crm` | Twenty REST API (people, companies, tasks, notes) |
| `/schedules` | GET/POST/DELETE /schedules |
| `/settings` | Static reference |

---

## Environment Variables

### Required
```
MINIMAX_API_KEY          # Primary model (subscription)
OPENROUTER_API_KEY       # Reasoning, learning, followups
VOYAGE_API_KEY           # Embeddings for knowledge base
```

### CRM
```
TWENTY_API_KEY           # Twenty CRM REST API
TWENTY_BASE_URL          # Default: http://localhost:3000
NEXT_PUBLIC_TWENTY_API_KEY   # Frontend CRM access
NEXT_PUBLIC_TWENTY_URL       # Frontend CRM URL
```

### Optional
```
TAVILY_API_KEY           # Better search quality (recommended)
GOOGLE_API_KEY           # NanoBanana image generation
WHATSAPP_ACCESS_TOKEN    # WhatsApp Business API
WHATSAPP_PHONE_ID        # WhatsApp phone number ID
GITHUB_TOKEN             # Code Review Agent
```

---

## File Structure

```
nexus.py                    # Main application (3500+ lines)
AGENTS.md                   # This file
requirements.txt            # Python dependencies
nexus.db                    # SQLite storage (dev)
lancedb/                    # Vector database
knowledge/                  # Knowledge base files
skills/                     # 24 domain skills
workspace/                  # Code Review Agent sandbox
pal-data/                   # Pal personal storage
nexus-ui/                   # Next.js frontend (16 pages)
  src/app/                  # App Router pages
  src/components/           # Shared components
  src/lib/api.ts            # AgentOS API client
  src/lib/twenty.ts         # Twenty CRM client
```

---

## Production Checklist

- [ ] Switch from SqliteDb to PostgresDb
- [ ] Configure TAVILY_API_KEY for search quality
- [ ] Deploy AgentOS on Hetzner (not Mac)
- [ ] Configure WhatsApp webhook with HTTPS
- [ ] Deploy nexus-ui to Vercel or Hetzner
- [ ] Set up JWT + RBAC for multi-user
- [ ] Test all workflows end-to-end
- [ ] Monitor via AgentOS tracing
