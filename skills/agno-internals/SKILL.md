---
name: agno-internals
description: How NEXUS stores and retrieves data internally. Knowledge base, learning system, sessions, skills, and tools. Load this to understand what data you have access to and how to use it.
metadata:
  version: "1.0.0"
  tags: [agno, knowledge, learning, memory, sessions, skills, internal]
---

# NEXUS Internal Systems — Complete Reference

You are an agent running on Agno. Here is everything you have access to and how it works.

## 1. Knowledge Base (read-only, documents)

**What:** PDF, TXT, MD, CSV, JSON files dropped into the `knowledge/` folder.
**Where:** LanceDB vectors (local) + Voyage AI embeddings.
**How:** Indexed automatically on startup. Searchable via semantic search.

### Who has it:
- **Knowledge Agent** — has `knowledge=knowledge_base` + `search_knowledge=True` (automatic search on every query)
- **Other agents** — can access via the Knowledge Agent (ask the team to route)

### How to use:
The Knowledge Agent automatically searches the knowledge base before answering. If you need knowledge and you're not the Knowledge Agent, ask: "What does our knowledge base say about X?"

### What's in it:
- Internal documents (SOPs, guides, policies)
- Research papers and reports
- Product documentation (Whabi, Docflow, Aurora)
- Any file the admin drops into `knowledge/`

## 2. Learning System (read/write, agent memory)

**What:** Patterns, solutions, user profiles, and entity memory that agents accumulate over time.
**Where:** SQLite (`nexus.db`) + LanceDB (`lancedb/nexus_learnings` table).
**How:** Agents learn automatically via `LearningMachine` after each interaction.

### Two learning levels:

**`_learning` (minimal)** — 13 agents use this:
- Only `learned_knowledge`: patterns, solutions, corrections
- Good for: research, content, analytics agents
- Example: "When user asks about pricing, always mention the free trial"

**`_learning_full` (complete)** — 8 agents use this:
- `user_profile`: who the user is, preferences, language
- `user_memory`: what the user told us (facts, context)
- `entity_memory`: tracked entities (clients, products, companies)
- `learned_knowledge`: patterns and solutions
- `decision_log`: why the agent made certain decisions
- Good for: support agents, Pal, Onboarding

### Built-in tools (automatic, you already have these):
- `search_learnings` — search for relevant insights in the knowledge base. ALWAYS call this before answering questions about best practices or recommendations.
- `save_learning` — save a reusable insight. ALWAYS call `search_learnings` first to check for duplicates.

### When to save a learning:
- You discovered a new pattern or solution
- A user corrected you
- You found a better way to handle a common request
- You learned something about a client or product

### When NOT to save:
- Generic information (save to Obsidian instead)
- One-time facts (save to Directus CRM instead)
- Conversation summaries (save to Directus conversations collection)

## 3. Sessions (automatic, chat history)

**What:** Conversation history for each user session.
**Where:** SQLite (`nexus.db`, table `agno_sessions`).
**How:** Automatic. Each agent stores the last N messages.

### Configuration per agent:
- `add_history_to_context=True` — includes past messages in context
- `num_history_runs=3` — how many past exchanges to include
- `update_memory_on_run=True` — updates learning after each run

### Important:
- Sessions are per-user, per-agent
- History resets when the session expires or user starts a new chat
- This is NOT permanent storage — use Directus for permanent data

## 4. Skills (read-only, instructions)

**What:** Markdown files with specialized knowledge for specific domains.
**Where:** `skills/` folder, each skill in its own subfolder with `SKILL.md`.
**How:** Loaded via `LocalSkills`. Agents can call `get_skill_instructions` to load a skill.

### Available skills (25):
| Skill | What it covers |
|-------|---------------|
| `directus-crm` | CRM collections, REST API, field formats |
| `obsidian-vault` | Obsidian MCP tools, note patterns |
| `agno-internals` | This document — internal systems |
| `whabi` | Whabi product knowledge |
| `docflow` | Docflow product knowledge |
| `aurora` | Aurora product knowledge |
| `whatsapp-business-api` | WhatsApp webhooks, templates |
| `content-strategy` | Reels/TikTok, viral hooks |
| `seo-geo` | SEO + AI search optimization |
| `competitive-analysis` | SaaS market analysis |
| `market-intelligence` | Research and trends |
| `hipaa-compliance` | Health data regulation (Latam) |
| `copywriting-es` | Spanish copywriting |
| `video-hooks` | Video content hooks |
| `deep-search` | Advanced research patterns |
| `deep-synthesis` | Analysis and synthesis |
| `prompt-patterns` | Prompt engineering |
| `academic-research` | Academic paper analysis |
| `agent-ops` | Agent operations |
| `campaign-analytics` | Campaign performance |
| `community-research` | Community analysis |
| `content-research` | Content research |
| `github-research` | GitHub analysis |
| `latam-research` | Latin America market |
| `pwa-troubleshooting` | PWA debugging |

### How to use skills:
```
get_skill_instructions(skill_name="directus-crm")
get_skill_reference(skill_name="whabi", reference="api-docs")
```

## 5. Tools Summary — What Goes Where

| Data type | Where to store | How |
|-----------|---------------|-----|
| Client contact info | **Directus** (contacts) | `save_contact()` |
| Company info | **Directus** (companies) | `save_company()` |
| Conversation log | **Directus** (conversations) | `log_conversation()` |
| Support ticket | **Directus** (tickets) | `log_support_ticket()` |
| Payment record | **Directus** (payments) | `confirm_payment()` |
| Raw event log | **Directus** (events) | `_directus_create("events", ...)` |
| Reusable pattern/insight | **Agno Learning** | `save_learning()` |
| Meeting notes, decisions | **Obsidian** | `write_note()` |
| Internal docs, SOPs | **Knowledge folder** | Drop file in `knowledge/` |
| Chat history | **Agno Sessions** | Automatic |
| User preferences | **Agno Learning Full** | Automatic |

## 6. Data Flow

```
User message arrives
    │
    ├── Agno checks session history (automatic)
    ├── Agent loads relevant skills (automatic)
    ├── Agent searches learnings (if search_learnings called)
    ├── Knowledge Agent searches knowledge base (if routed)
    │
    ▼
Agent processes and responds
    │
    ├── Learning system updates (automatic)
    ├── Session history updated (automatic)
    ├── CRM data saved to Directus (if tool called)
    └── Notes saved to Obsidian (if tool called)
```

## 7. Important Rules

1. **Business data → Directus.** Contacts, conversations, tickets, payments. This is permanent and survives framework changes.
2. **Agent patterns → Agno Learning.** "How to handle X" type knowledge. This is framework-specific.
3. **Team knowledge → Obsidian.** Meeting notes, decisions, SOPs. Human-readable and searchable.
4. **Reference docs → Knowledge folder.** PDFs, guides, specs. Indexed for semantic search.
5. **Never duplicate.** Don't save the same info in multiple places. Pick the right one.
6. **Search before saving.** Always check if the info already exists before creating a new record.
