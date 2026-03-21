# AGENTS.md — NEXUS Production Architecture

Instructions for AI agents and humans working on this codebase.
Based on Agno's official patterns (`.cursorrules`, `AGENTS.md`, cookbook/01_demo),
community best practices, and lessons learned in production.

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
| **Team** | Multiple specialists, dynamic coordination | Customer support routing, research delegation |
| **Workflow** | Sequential steps, audit trail, repeatable | Deep research pipeline, content production, SEO audit |

**Rule: Start with a single agent. Only add Teams/Workflows when a single agent can't do it.**

---

## Model Assignment Rules

Groq tool calling is broken as of March 2026 (agno-agi/agno#4090).
No constrained decoding, no fix ETA from Groq.

| Task Type | Model | Why |
|-----------|-------|-----|
| **Tool calling** (search, CRM, files) | `TOOL_MODEL` (MiniMax M2.7) | Reliable tool calling, 200K context |
| **Streaming/fast UX** | `FAST_MODEL` (MiniMax M2.7) | Same quality, use highspeed when plan supports it |
| **Reasoning** (analysis, synthesis) | `REASONING_MODEL` (MiniMax M2.7) | Deep analysis without tools |
| **Routing** (team leader decisions) | `GROQ_ROUTING_MODEL` (gpt-oss-20b) | No tools needed, ultra fast, cheap |
| **Background** (followups, evals) | `GROQ_FAST_MODEL` (llama-3.1-8b) | No tools, text generation only |
| **Learning extraction** | `TOOL_MODEL` (MiniMax M2.7) | EntityMemory needs tool calling |
| **Compression** | `FAST_MODEL` (MiniMax M2.7) | Text summarization, no tools |

**NEVER use Groq for any agent that has `tools=[...]`.**

---

## Agent Construction Pattern

Follow the official Agno cookbook structure:

```python
# ---------------------------------------------------------------------------
# [Agent Name] — [One-line description]
# ---------------------------------------------------------------------------

agent_name = Agent(
    name="Agent Name",                    # Display name in AgentOS UI
    role="One sentence describing role",  # Used by team leaders for routing
    model=TOOL_MODEL,                     # See model assignment rules above

    # --- Tools (only what this agent needs) ---
    tools=[SpecificTool()],               # Minimal tool set, no redundancy
    tool_call_limit=3,                    # Prevent infinite tool loops
    retries=1,                            # One retry for transient failures

    # --- Knowledge & Skills ---
    skills=_domain_skills,                # Lazy-loaded domain instructions
    knowledge=knowledge_base,             # Only if agent needs RAG
    search_knowledge=True,                # Required to enable agentic RAG

    # --- Learning ---
    learning=_learning,                   # LearningMachine for memory
    # NOTE: LearningMachine model must support tool calling (not Groq)

    # --- Guardrails & Evals ---
    pre_hooks=_guardrails,                # PII detection, prompt injection
    post_hooks=[_quality_eval],           # Background quality scoring

    # --- Instructions (the most important part) ---
    instructions=[
        "You are [role]. You [do what].",
        "",
        "## What you handle",
        "- [Capability 1]",
        "- [Capability 2]",
        "",
        "## Process",
        "1. [Step 1]",
        "2. [Step 2]",
        "",
        "## Output format",
        "[Exact format the agent should produce]",
        "",
        "## Rules",
        "- [Hard constraint 1]",
        "- [Hard constraint 2]",
    ],

    # --- Context ---
    db=db,
    add_history_to_context=True,
    num_history_runs=3,                   # 5 for support agents, 3 for others
    add_datetime_to_context=True,
    markdown=True,

    # --- Performance ---
    compression_manager=_compression,     # Only for agents with heavy tool output
)
```

### Critical Rules (from Agno's .cursorrules)

- **NEVER create agents in loops** — reuse them for performance
- **PostgreSQL in production**, SQLite for dev only
- **Start with single agent**, scale up only when needed
- **Both sync and async** — all public methods need both variants

---

## Skills System

Skills are lazy-loaded domain knowledge files. They are the equivalent of
AGENTS.md but scoped to specific domains. Each skill folder has:

```
skills/
  domain-name/
    SKILL.md          # Main instructions (loaded when relevant)
    references/       # Supporting documents
      reference-1.md
      reference-2.md
```

### When to Use Skills vs Instructions

| Use | Skills | Instructions |
|-----|--------|-------------|
| Domain knowledge (EHR compliance, lead scoring) | Skills | |
| Agent behavior (output format, process steps) | | Instructions |
| Reusable across agents | Skills | |
| Specific to one agent | | Instructions |
| Long reference material (templates, checklists) | Skills | |

### Existing Skills

| Skill | Domain | Used By |
|-------|--------|---------|
| **Research Skills** | | |
| `deep-search/` | Query engineering, source quality, snippet extraction | All research scouts |
| `deep-synthesis/` | Report structure, confidence scoring, analytical writing | Research Synthesizer |
| `github-research/` | Repo analysis, PR tracking, OSS health assessment | All research scouts |
| `community-research/` | Reddit, HN, Twitter sentiment, opinion mining | All research scouts |
| `market-intelligence/` | Market data, competitor analysis, pricing intel | All research scouts |
| **Product Skills** | | |
| `whabi/` | WhatsApp CRM, leads, campaigns, message templates | Whabi Support, Onboarding |
| `docflow/` | EHR, compliance, documents, retention periods | Docflow Support, Onboarding |
| `aurora/` | Voice PWA, commands, Whisper, troubleshooting | Aurora Support, Onboarding |
| **Content Skills** | | |
| `content-research/` | Trend research, content briefs, source evaluation | Trend Scout |
| `content-strategy/` | Content pillars, hooks, formats, brand voice | Scriptwriter |
| `remotion-video/` | Video production, storyboards, animations | Scriptwriter |
| `campaign-analytics/` | Social media metrics, KPIs, reporting | Analytics Agent |
| `seo-geo/` | SEO + GEO optimization, listicle structure | Keyword Researcher, Article Writer |
| **Operations** | | |
| `agent-ops/` | Tool budgeting, error handling, escalation rules | Multiple agents |

---

## Workflow Construction Pattern

Follow Agno's official pipeline pattern (cookbook/gemini_3/20_workflow.py):

```python
workflow = Workflow(
    name="workflow-name",
    description="What this workflow does in one sentence",
    db=SqliteDb(session_table="workflow_session", db_file="nexus.db"),
    steps=[
        # Phase 1: Gather (parallel when possible)
        Parallel(
            Step(name="Source A", agent=agent_a, skip_on_failure=True),
            Step(name="Source B", agent=agent_b, skip_on_failure=True),
            name="Gather Phase",
        ),
        # Phase 2: Quality gate (stop early if data is thin)
        Step(name="Quality Gate", executor=quality_gate_function),
        # Phase 3: Synthesize (always the last step — user sees this)
        Step(name="Final Output", agent=synthesizer_agent),
    ],
)
```

### Workflow Rules

1. **The last step is what the user sees.** Never end on a scoring/eval step.
2. **Use `skip_on_failure=True`** on parallel steps so one failure doesn't kill the workflow.
3. **Quality gates** are simple functions, not agents. Check content length, not quality.
4. **No `output_schema`** on the final synthesizer if the model doesn't support native structured outputs (MiniMax doesn't). Use instructions to guide format instead.
5. **Parallel steps don't share context.** Each runs independently. The synthesizer combines them.

### Workflow vs Team Decision

| Scenario | Use |
|----------|-----|
| "Research X, then write about it" | Workflow (sequential) |
| "Answer this customer question" | Team (router picks specialist) |
| "Search 3 sources simultaneously" | Workflow with Parallel |
| "Debate pros and cons" | Team (coordinate mode) |
| "Generate content for 3 platforms" | Workflow with Parallel |

---

## Team Construction Pattern

```python
team = Team(
    name="Team Name",
    description="What this team does (used by AgentOS UI)",
    members=[agent_a, agent_b, agent_c],
    mode=TeamMode.route,              # route | broadcast | coordinate | task
    model=GROQ_ROUTING_MODEL,         # Routing model (no tools needed)
    pre_hooks=_guardrails,
    determine_input_for_members=False, # Pass user message as-is to member
    instructions=[
        "You are the [team name] router.",
        "Route each message to the BEST agent based on content.",
        "",
        "## Routing rules (pick ONE agent):",
        "- [keyword pattern]: route to [Agent A]",
        "- [keyword pattern]: route to [Agent B]",
        "- [unclear/general]: route to [Fallback Agent]",
        "",
        "Do NOT add commentary. Return the agent's response directly.",
    ],
    db=db,
    learning=_learning,
    show_members_responses=True,
    markdown=True,
)
```

### Team Mode Selection

| Mode | Behavior | Use When |
|------|----------|----------|
| `route` | Leader picks ONE member | Customer support, FAQ routing |
| `broadcast` | ALL members get the same input | Parallel research, multi-perspective |
| `coordinate` | Leader orchestrates back-and-forth | Debate, iterative refinement |
| `task` | Leader assigns specific sub-tasks | Complex decomposition |

---

## Search Provider Strategy

Scouts use different search backends based on available API keys.
The system auto-detects which keys are set and creates scouts accordingly.

| Provider | Best For | API Key | Cost |
|----------|----------|---------|------|
| **Tavily** | News, articles, AI-optimized snippets | `TAVILY_API_KEY` | 1000 free/mo |
| **Exa** | Semantic search, papers, niche content | `EXA_API_KEY` | 1000 free/mo |
| **Firecrawl** | Full page extraction, docs, READMEs | `FIRECRAWL_API_KEY` | 500 free/mo |
| **Spider** | Site crawling, GitHub repos | Always available | Free OSS |
| **WebSearch** | General fallback (DuckDuckGo) | Always available | Free |

**Minimum setup:** Spider + WebSearch (no API keys needed).
**Recommended:** Add Tavily for dramatically better search quality.
**Full setup:** All 5 providers for maximum coverage.

---

## Common Mistakes (from Agno's .cursorrules + our experience)

| Mistake | Why It's Bad | Fix |
|---------|-------------|-----|
| Creating agents in loops | Massive performance hit | Create once, reuse |
| Using Groq for tool calling | ~15% failure rate, hallucinated tools | Use MiniMax for tools |
| `output_schema` on MiniMax | Produces raw JSON, not readable text | Use instructions for format |
| SQLite in production | No concurrent access, no persistence | Use PostgreSQL |
| DuckDuckGo in parallel | Rate limited, blocks after ~5 requests | Use Tavily/Exa |
| Skills on Groq agents | Long context causes hallucinated tools | Skills only on MiniMax agents |
| Ending workflow on eval step | User sees SCORE, not the report | Always end on synthesizer |
| `tool_call_limit` too high | Agent loops endlessly on searches | Limit to 3 (2 searches + 1 margin) |
| Missing `skip_on_failure=True` | One scout failure kills entire Parallel | Always set on parallel steps |
| Forgetting `search_knowledge=True` | Knowledge base exists but agent can't search it | Required for agentic RAG |

---

## File Structure

```
nexus.py                    # Main application (all agents, teams, workflows, AgentOS)
requirements.txt            # Dependencies
nexus.db                    # SQLite storage (dev only)
lancedb/                    # Vector database (local)
knowledge/                  # Knowledge base files (PDF, MD, CSV, JSON)
  blog-drafts/              # Generated blog articles
skills/                     # Domain skills (lazy-loaded instructions)
  whabi/                    # WhatsApp CRM domain
  docflow/                  # EHR domain
  aurora/                   # Voice PWA domain
  content-research/         # Content research strategies
  content-strategy/         # Content creation guidelines
  remotion-video/           # Video production specs
  campaign-analytics/       # Analytics and KPIs
  deep-search/              # Search query engineering
  deep-synthesis/           # Report synthesis techniques
  seo-geo/                  # SEO + GEO optimization
  agent-ops/                # General agent operations
workspace/                  # Sandboxed directory for Code Review Agent
evals/                      # Evaluation scripts
AGENTS.md                   # This file
```

---

## Production Checklist

Before deploying to production:

- [ ] Switch from `SqliteDb` to `PostgresDb`
- [ ] Set `debug_mode=False` on all agents
- [ ] Set `show_tool_calls=False` on all agents
- [ ] Wrap all `agent.run()` calls in try-except
- [ ] Configure `TAVILY_API_KEY` for search quality
- [ ] Set up MiniMax paid plan (avoid rate limits)
- [ ] Test all workflows end-to-end with real queries
- [ ] Verify WhatsApp webhook endpoint is accessible
- [ ] Set up monitoring via AgentOS tracing
- [ ] Review PII guardrails are active on all customer-facing agents
