# AGENTS.md — NEXUS Production Architecture

Instructions for AI agents and humans working on this codebase.
Based on Agno's official patterns, lessons learned with MiniMax M2.7,
and production debugging across 20+ iterations.

---

## Decision Framework: When to Use What

```
Is the task a single, clear objective?
  YES → Single Agent (90% of cases)
  NO  → Does it need predictable, repeatable steps?
          YES → Workflow (deterministic pipeline)
          NO  → Team (LLM decides who does what)
```

| Pattern | Use When | Example |
|---------|----------|---------|
| **Agent** | One clear task, solvable with tools + instructions | Web search, CRM lookup, code review |
| **Team** | Multiple specialists, dynamic coordination | Customer support routing, NEXUS master |
| **Workflow** | Sequential steps, audit trail, repeatable | Deep research, content production |

---

## Model Assignment Rules

| Task Type | Model | Why |
|-----------|-------|-----|
| **Tool calling** (search, CRM, files) | `TOOL_MODEL` (MiniMax M2.7) | Reliable tool calling, 200K context |
| **Team routing** (NEXUS, WhatsApp Support) | `TOOL_MODEL` (MiniMax M2.7) | Precise routing, no tool confusion |
| **Reasoning** (analysis, synthesis) | `REASONING_MODEL` (MiniMax M2.7) | Deep analysis |
| **Groq routing** (Cerebro, Content Factory) | `GROQ_ROUTING_MODEL` (gpt-oss-20b) | Fast, cheap, no tools needed |
| **Background** (evals only) | `GROQ_FAST_MODEL` (llama-3.1-8b) | No tools, text generation only |
| **Learning extraction** | `TOOL_MODEL` (MiniMax M2.7) | EntityMemory needs tool calling |
| **Compression** | `FAST_MODEL` (MiniMax M2.7) | Text summarization |

### MiniMax Incompatibilities (March 2026)

These features require `response_format: json_object` which MiniMax rejects with error 2013:

| Feature | Status | Alternative |
|---------|--------|-------------|
| `user_memory` (LearningMachine) | Disabled | `user_profile` + `entity_memory` work via tool calling |
| `enable_agentic_memory` (MemoryManager) | Disabled | LearningMachine handles memory |
| `update_memory_on_run` (MemoryManager) | Disabled | LearningMachine handles memory |
| `output_schema` on agents | Don't use | Use instructions to guide format |
| `followups` with Groq | Disabled | Groq requires 'json' in prompt |

Re-enable when switching to OpenAI or Anthropic.

---

## Agent Construction Pattern

```python
agent_name = Agent(
    name="Agent Name",
    role="One sentence describing role",
    model=TOOL_MODEL,

    # --- Tools ---
    tools=[SpecificTool()],
    tool_call_limit=5,                    # Prevent infinite loops (3 for scouts, 5 for others)
    retries=1,

    # --- Knowledge & Skills ---
    skills=_domain_skills,                # Lazy-loaded via get_skill_instructions tool
    knowledge=knowledge_base,             # Only if agent needs RAG
    search_knowledge=True,                # Required to enable agentic RAG

    # --- Learning (works with MiniMax) ---
    learning=_learning,                   # user_profile + entity_memory + learned_knowledge
    # NOTE: user_memory disabled (json_object incompatible with MiniMax)

    # --- Guardrails ---
    pre_hooks=_guardrails,                # PII masking + prompt injection detection
    post_hooks=[_quality_eval],           # Background quality scoring (heuristic, no LLM call)

    # --- Instructions ---
    instructions=[...],

    # --- Context ---
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)
```

---

## Team Construction Pattern (CRITICAL — learned from production)

```python
team = Team(
    name="Team Name",
    id="team-id",                         # Required for API access (/teams/team-id/runs)
    members=[agent_a, agent_b, agent_c],
    mode=TeamMode.route,
    respond_directly=True,                # CRITICAL: stop after routing, return member response
    tool_call_limit=1,                    # CRITICAL: only ONE tool call (delegate_task_to_member)
    model=TOOL_MODEL,                     # MiniMax for precise routing
    # NO pre_hooks — guardrails on individual agents, not team leader
    # NO learning — adds extra tools that confuse routing
    determine_input_for_members=False,
    show_members_responses=False,         # respond_directly handles this
    instructions=[
        "You are the [team name] router.",
        "You select which team member should handle each request.",
        "",
        "## Select ONE member:",
        "- [pattern] → [Agent Name]",
        "- [pattern] → [Agent Name]",
        "- Default → [Fallback Agent]",
    ],
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
)
```

### Why these settings matter

| Setting | Why |
|---------|-----|
| `respond_directly=True` | Sets `stop_after_tool_call=True` on delegate function. Leader routes and stops. |
| `tool_call_limit=1` | Forces exactly ONE tool call. Without this, MiniMax calls skills/learning tools instead of routing. |
| No `learning` | Learning adds `search_learnings` + `save_learning` tools. Leader calls these instead of `delegate_task_to_member`. |
| No `pre_hooks` | PII guardrail blocks messages BEFORE routing. Causes cascade errors. |
| `show_members_responses=False` | With `respond_directly`, showing member responses is redundant and shows thinking steps. |

---

## Skills System

Skills are lazy-loaded via tool calls. The agent sees a summary and uses
`get_skill_instructions(skill_name)` to load full instructions when needed.

### All 24 Skills

| Category | Skill | Domain |
|----------|-------|--------|
| **Research** | `deep-search/` | Query engineering, source quality |
| | `deep-synthesis/` | Report structure, confidence scoring |
| | `github-research/` | Repo analysis, PR tracking, OSS health |
| | `community-research/` | Reddit, HN, Twitter sentiment |
| | `market-intelligence/` | Market data, competitor pricing |
| | `academic-research/` | arXiv, Scholar, PubMed |
| **Products** | `whabi/` | WhatsApp CRM, leads, campaigns |
| | `whatsapp-business-api/` | Meta API, webhooks, troubleshooting |
| | `docflow/` | EHR, documents, workflows |
| | `hipaa-compliance/` | Health data laws, audit checklist |
| | `aurora/` | Voice commands, Whisper settings |
| | `pwa-troubleshooting/` | Installation, mic, cache by browser |
| **Content** | `content-research/` | Trend research, content briefs |
| | `content-strategy/` | Pillars, hooks, brand voice |
| | `copywriting-es/` | PAS/AIDA/BAB, Latam tone |
| | `video-hooks/` | Hook patterns by category |
| | `remotion-video/` | Video production, animations |
| | `campaign-analytics/` | Metrics, KPIs, reporting |
| | `seo-geo/` | SEO + GEO optimization |
| **Business** | `competitive-analysis/` | SWOT, feature matrix |
| | `latam-research/` | Latam data sources, regulatory map |
| | `crm-patterns/` | Twenty CRM queries, tagging |
| **Operations** | `agent-ops/` | Tool budgeting, error handling |
| | `prompt-patterns/` | Chain-of-thought, few-shot |

---

## Current System Inventory

### Agents (40 total, 18 registered in AgentOS)

**Registered (visible in dashboard):**
Research Agent, Knowledge Agent, Automation Agent, Trend Scout,
Scriptwriter, Creative Director, Analytics Agent, Code Review Agent,
Whabi Support, Docflow Support, Aurora Support, General Support,
Dash, Pal, Onboarding Agent, Email Agent, Scheduler Agent, Invoice Agent

**Internal (used in workflows):**
5 search scouts (Tavily, Exa, Firecrawl, Spider, WebSearch),
Research Planner, Research Synthesizer, Synthesis Agent,
Keyword Researcher, Article Writer, SEO Auditor,
3 social media writers, Social Media Auditor,
3 competitor scouts, Competitor Synthesizer,
Image Generator, Video Generator, Media Describer

### Teams (4)

| Team | Mode | Router Model | Members |
|------|------|-------------|---------|
| NEXUS Master | route | TOOL_MODEL (MiniMax) | 12 specialists |
| Cerebro | route | GROQ_ROUTING_MODEL | Research, Knowledge, Automation |
| Content Factory | route | GROQ_ROUTING_MODEL | Trend Scout, Scriptwriter, Analytics |
| WhatsApp Support | route | GROQ_ROUTING_MODEL | Whabi, Docflow, Aurora, General |

### Workflows (7)

| Workflow | Pattern |
|----------|---------|
| deep-research | Plan → Parallel(N scouts) → Quality Gate → Report |
| content-production | Trend → Compact → Script → Creative Review |
| client-research | Parallel(web + knowledge) → Synthesis |
| seo-content | Keyword → Article → Audit Loop |
| social-media-autopilot | Trend → Parallel(IG/TW/LI) → Audit |
| competitor-intelligence | Parallel(3 scouts) → Synthesis |
| media-generation | Router(image vs video) → Generation |

---

## Common Mistakes (from production experience)

| Mistake | What happens | Fix |
|---------|-------------|-----|
| `learning` on team leaders | Leader calls `search_learnings` instead of routing | No learning on teams |
| `pre_hooks` on team leaders | PII guardrail blocks before routing | Guardrails on agents only |
| No `respond_directly` on teams | Leader makes multiple tool calls, calls wrong tools | Always set `respond_directly=True` |
| No `tool_call_limit` on teams | Leader loops on tool calls | Set `tool_call_limit=1` |
| `show_members_responses=True` with `respond_directly` | Shows thinking steps to user | Set to `False` |
| `output_schema` on MiniMax agents | Produces raw JSON, not readable text | Use instructions for format |
| `user_memory` with MiniMax | Error 2013 (json_object incompatible) | Use entity_memory instead |
| `enable_agentic_memory` with MiniMax | Same error 2013 | Disabled |
| DuckDuckGo in parallel | Rate limited after ~5 requests | Use Tavily/Exa |
| `tool_call_limit` too high on agents | Agent loops on searches, wastes tokens | 3 for scouts, 5 for others |
| No `id=` on teams | API returns 404 (team not found by ID) | Always set `id="team-name"` |

---

## Frontend (nexus-ui)

Next.js app connecting directly to AgentOS REST API.

```
Browser (localhost:3000) → POST /teams/nexus/runs (FormData) → AgentOS (localhost:7777)
```

- Streaming SSE with event filtering (only shows RunContent, hides tool calls/reasoning)
- Configurable backend URL via `NEXT_PUBLIC_API_URL`
- Deploy to Vercel with `npx vercel`

---

## File Structure

```
nexus.py                    # Main application (3100+ lines)
requirements.txt            # Python dependencies
nexus.db                    # SQLite storage (dev only)
lancedb/                    # Vector database (local)
knowledge/                  # Knowledge base files
skills/                     # 24 domain skills
workspace/                  # Sandboxed directory for Code Review Agent
pal-data/                   # Pal personal storage (JSON files)
nexus-ui/                   # Next.js frontend
  src/app/page.tsx          # Chat interface with SSE streaming
  src/app/layout.tsx        # CopilotKit/AG-UI layout
evals/                      # Evaluation scripts
AGENTS.md                   # This file
```

---

## Production Checklist

- [ ] Switch from `SqliteDb` to `PostgresDb`
- [ ] Configure `TAVILY_API_KEY` for search quality
- [ ] Set up MiniMax paid plan (avoid rate limits)
- [ ] Deploy AgentOS on Hetzner (not Mac)
- [ ] Configure JWT + RBAC for multi-user
- [ ] Set up WhatsApp webhook with HTTPS
- [ ] Deploy nexus-ui to Vercel
- [ ] Test all workflows end-to-end
- [ ] Set up monitoring via AgentOS tracing
