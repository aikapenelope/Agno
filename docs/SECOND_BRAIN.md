# NEXUS Second Brain — Complete Architecture Guide

How NEXUS stores, retrieves, and learns from data. Based on Agno's official cookbook patterns and production best practices.

## The 5 Memory Systems

NEXUS has 5 interconnected memory systems. Together they form a "second brain" that gets smarter over time.

```
┌─────────────────────────────────────────────────────────┐
│                    NEXUS SECOND BRAIN                     │
│                                                          │
│  1. USER PROFILE        "Who am I talking to?"           │
│     Name, preferences, role, communication style         │
│     Stored: SQLite (nexus.db)                            │
│     Updates: Automatic after each conversation           │
│                                                          │
│  2. USER MEMORY          "What have they told me?"       │
│     Observations, facts, context from conversations      │
│     Stored: SQLite (nexus.db)                            │
│     Updates: Automatic (AGENTIC mode — agent decides)    │
│                                                          │
│  3. ENTITY MEMORY        "What do I know about X?"       │
│     Clients, companies, products, projects               │
│     Facts (timeless) + Events (time-bound)               │
│     Stored: SQLite (nexus.db)                            │
│     Updates: Automatic (AGENTIC mode)                    │
│                                                          │
│  4. LEARNED KNOWLEDGE    "What patterns have I found?"   │
│     Solutions, best practices, corrections               │
│     Stored: LanceDB vectors (lancedb/nexus_learnings)    │
│     Updates: Agent calls save_learning / search_learnings│
│     Searchable: Semantic search across all learnings     │
│                                                          │
│  5. KNOWLEDGE BASE       "What documents do I have?"     │
│     PDFs, MD, TXT, CSV, JSON from knowledge/ folder      │
│     Stored: LanceDB vectors (lancedb/nexus_knowledge)    │
│     Updates: On startup (auto-index new files)           │
│     Searchable: Semantic search via Knowledge Agent      │
│                                                          │
│  + DECISION LOG          "Why did I decide that?"        │
│     Audit trail of agent decisions and reasoning         │
│     Stored: SQLite (nexus.db)                            │
│     Updates: Automatic after each decision               │
│                                                          │
│  + SESSION HISTORY       "What happened in this chat?"   │
│     Last N messages per session                          │
│     Stored: SQLite (nexus.db)                            │
│     Config: num_history_runs=3 to 10 per agent           │
└─────────────────────────────────────────────────────────┘
```

## How Each System Works

### 1. User Profile (automatic)

From Agno cookbook `08_learning/02_user_profile`:

The agent automatically extracts profile information from conversations. You don't need to ask it to remember — it just does.

**What it captures:**
- Name and preferred name
- Role/job title
- Communication preferences (concise, detailed, language)
- Custom fields based on conversation

**Example:**
```
User: "Soy Angel, CEO de AikaLabs. Prefiero respuestas cortas en español."

→ Profile saved:
   name: Angel
   role: CEO
   company: AikaLabs
   language: Spanish
   style: concise
```

**Persists across sessions.** Next time you chat, the agent already knows who you are.

### 2. User Memory (automatic)

From Agno cookbook `08_learning/01_basics`:

Unstructured observations about the user. Things the agent notices and remembers.

**What it captures:**
- Facts you mention ("Tengo una reunion con Pedro el viernes")
- Preferences ("No me gusta que me manden emails largos")
- Context ("Estamos migrando de Twenty a Directus")

**Example:**
```
User: "Recuerdame que el viernes tengo reunion con Pedro de Nala Labs"

→ Memory saved:
   "User has a meeting with Pedro from Nala Labs on Friday"
```

### 3. Entity Memory (automatic)

From Agno cookbook `08_learning/04_entity_memory`:

Tracks external entities: people, companies, products, projects. Distinguishes between:
- **Facts** (timeless): "Nala Labs is a tech company in Caracas"
- **Events** (time-bound): "Nala Labs signed contract on March 25"

**Example:**
```
User: "Pedro Gomez de Nala Labs quiere el plan pro de Whabi. 
       Tiene 25 empleados y estan en Caracas."

→ Entities saved:
   Entity: Pedro Gomez
     Facts: works at Nala Labs, interested in Whabi pro plan
   Entity: Nala Labs
     Facts: 25 employees, based in Caracas, tech company
     Events: expressed interest in Whabi pro plan (March 2026)
```

**Shared across agents.** If you tell the Research Agent about Nala Labs, the Support Agent also knows.

### 4. Learned Knowledge (agent-controlled)

From Agno cookbook `08_learning/05_learned_knowledge`:

Reusable patterns and solutions. The agent decides what's worth remembering using `save_learning` and retrieves with `search_learnings`.

**What gets saved:**
- Solutions to common problems
- Best practices discovered
- Corrections from the user
- Patterns that work

**Example:**
```
Agent resolves a Chrome login issue by clearing cache.
→ save_learning:
   title: "Chrome login fix"
   learning: "When users can't login on Chrome, clearing browser cache resolves it"
   tags: ["support", "chrome", "login"]

Next time a similar issue comes up:
→ search_learnings("chrome login problem")
→ Finds the previous solution instantly
```

**Stored as vectors.** Semantic search finds relevant learnings even with different wording.

### 5. Knowledge Base (document-based)

From Agno cookbook `07_knowledge/03_production`:

Documents dropped into the `knowledge/` folder. Indexed on startup with Voyage AI embeddings.

**Supported formats:** PDF, TXT, MD, CSV, JSON

**How to add knowledge:**
```bash
# Just drop files into the knowledge folder
cp product-guide.pdf ~/Agno/knowledge/
cp pricing-sheet.md ~/Agno/knowledge/
# Restart nexus.py — files are indexed automatically
```

**How agents access it:**
- Knowledge Agent has `search_knowledge=True` (automatic search)
- Other agents ask the Knowledge Agent via team routing

### Decision Log (automatic audit trail)

From Agno cookbook `08_learning/09_decision_logs`:

Records why the agent made certain decisions. Useful for:
- Auditing agent behavior
- Debugging unexpected outcomes
- Learning from past decisions

**Example:**
```
Agent decides to escalate a ticket to human support.
→ Decision logged:
   action: "escalate_to_human"
   reason: "Customer urgency=high, 3 failed resolution attempts"
   context: "Whabi payment issue, customer frustrated"
```

## Storage Architecture

```
~/Agno/
├── nexus.db              ← SQLite: sessions, profiles, memories, entities, decisions
├── lancedb/
│   ├── nexus_knowledge   ← Vectors: document embeddings (knowledge/ folder)
│   └── nexus_learnings   ← Vectors: learned patterns and solutions
├── knowledge/            ← Source documents (PDF, MD, TXT, CSV, JSON)
│   ├── product-guide.pdf
│   ├── pricing.md
│   └── ...
└── nexus.py              ← Agent definitions
```

**SQLite (nexus.db)** stores structured data:
- `agno_sessions` — chat history per user/agent
- `agno_user_profiles` — user profile data
- `agno_user_memories` — user observations
- `agno_entity_memories` — entity facts and events
- `agno_decision_logs` — agent decision audit trail

**LanceDB (lancedb/)** stores vectors:
- `nexus_knowledge` — document embeddings for RAG
- `nexus_learnings` — learned pattern embeddings

## NEXUS Configuration

All 27 agents use `_learning_full`:

```python
_learning_full = LearningMachine(
    model=TOOL_MODEL,  # MiniMax M2.7 (subscription, $0/token)
    knowledge=learnings_knowledge,
    user_profile=UserProfileConfig(mode=LearningMode.AGENTIC),
    user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
    entity_memory=EntityMemoryConfig(mode=LearningMode.AGENTIC),
    learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    decision_log=DecisionLogConfig(mode=LearningMode.AGENTIC),
)
```

**AGENTIC mode** means the agent gets tools and decides when to use them. You'll see tool calls like `update_user_profile`, `create_entity`, `save_learning` in the agent's responses.

## Production Patterns (from Agno cookbook)

### Personal Assistant Pattern
From `cookbook/08_learning/07_patterns/personal_assistant.py`:
- User Profile (ALWAYS) — auto-extract preferences
- Session Context with planning — track goals and progress
- Entity Memory — remember people, projects, events

### Support Agent Pattern
From `cookbook/08_learning/07_patterns/support_agent.py`:
- User Profile (ALWAYS) — customer history
- Session Context with planning — ticket tracking
- Entity Memory — products, past tickets (shared across org)
- Learned Knowledge (AGENTIC) — solutions that worked

### Research Assistant Pattern
From `cookbook/08_learning/07_patterns/research_assistant.py`:
- User Profile — researcher preferences
- User Memory — research interests, past queries
- Tools — web search for live research

## External Data (Directus)

Business data that must survive framework changes lives in Directus:

| Data | Agno (internal) | Directus (external) |
|------|-----------------|-------------------|
| "Who is Pedro Gomez?" | Entity Memory (auto) | contacts collection (permanent) |
| "Pedro asked about pricing" | User Memory (auto) | conversations collection (permanent) |
| "Chrome cache fix works" | Learned Knowledge (searchable) | — |
| "User prefers Spanish" | User Profile (auto) | — |
| "Payment of $49 approved" | Decision Log (audit) | payments collection (permanent) |

**Rule:** Agno learns automatically. Directus stores permanently. Both work together.

## How to Make NEXUS Smarter

1. **Drop documents in `knowledge/`** — product guides, SOPs, pricing sheets, FAQs
2. **Talk to it regularly** — the more you interact, the more it learns about you
3. **Correct it when wrong** — corrections become learned knowledge
4. **Use specific names** — "Pedro Gomez from Nala Labs" creates entity memory
5. **Ask it to remember** — "Recuerda que el plan pro cuesta $49/mes"
6. **Review learnings** — ask "What have you learned about X?"

## References

- [Agno Learning Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/08_learning)
- [Agno Knowledge Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/07_knowledge)
- [Agno Memory Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/11_memory)
- [Personal Assistant Pattern](https://github.com/agno-agi/agno/blob/main/cookbook/08_learning/07_patterns/personal_assistant.py)
- [Support Agent Pattern](https://github.com/agno-agi/agno/blob/main/cookbook/08_learning/07_patterns/support_agent.py)
