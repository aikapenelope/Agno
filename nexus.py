"""
NEXUS Cerebro - Multi-Agent Analysis System
============================================

A multi-agent analysis system powered by Agno, Groq, and MiniMax.
Cerebro orchestrates specialized agents to decompose complex tasks,
research the web, query a knowledge base, and execute automations.

Based on official Agno cookbook patterns:
- cookbook/05_agent_os/demo.py (AgentOS setup)
- cookbook/90_models/groq/agent_team.py (Groq + Team)
- cookbook/03_teams/05_knowledge/01_team_with_knowledge.py (Knowledge)

Prerequisites:
    pip install -r requirements.txt

    Set environment variables (or add to ~/.zshrc for persistence):
        export GROQ_API_KEY="your-groq-api-key"
        export VOYAGE_API_KEY="your-voyage-api-key"
        export MINIMAX_API_KEY="your-minimax-api-key"
        export N8N_API_KEY="your-n8n-api-key"
        export TWENTY_API_KEY="your-twenty-api-key"
        export TWENTY_BASE_URL="http://localhost:3000"

    MCP servers (requires Docker running with n8n and Twenty):
        - n8n workflow builder: creates and manages n8n workflows
        - Twenty CRM: manages contacts, companies, tasks, notes

    Knowledge base:
        Drop PDF, TXT, MD, CSV, or JSON files into the knowledge/ folder.
        They are indexed automatically on startup.

Usage:
    python nexus.py
    Then connect AgentOS UI at https://os.agno.com -> Add new OS -> Local
"""

import os
from pathlib import Path

from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail
from agno.learn.machine import LearningMachine
from agno.learn import (
    LearnedKnowledgeConfig,
    LearningMode,
    UserProfileConfig,
    UserMemoryConfig,
    EntityMemoryConfig,
)
from agno.knowledge.embedder.voyageai import VoyageAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.groq import Groq
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.registry import Registry
from agno.skills import LocalSkills, Skills
from agno.team import Team, TeamMode
from agno.tools.mcp import MCPTools
from agno.tools.arxiv import ArxivTools
from agno.tools.browserbase import BrowserbaseTools
from agno.tools.calculator import CalculatorTools
from agno.tools.csv_toolkit import CsvTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.email import EmailTools
from agno.tools.exa import ExaTools
from agno.tools.file import FileTools
from agno.tools.firecrawl import FirecrawlTools
from agno.tools.github import GithubTools
from agno.tools.hackernews import HackerNewsTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.lumalab import LumaLabTools
from agno.tools.nano_banana import NanoBananaTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.reddit import RedditTools
from agno.tools.slack import SlackTools
from agno.tools.spider import SpiderTools
from agno.tools.tavily import TavilyTools
from agno.tools.todoist import TodoistTools
from agno.tools.user_control_flow import UserControlFlowTools
from agno.tools.webbrowser import WebBrowserTools
from agno.tools.websearch import WebSearchTools
from agno.tools.whatsapp import WhatsAppTools
from agno.tools.wikipedia import WikipediaTools
from agno.tools.workflow import WorkflowTools
from agno.tools.x import XTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.youtube import YouTubeTools
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

# ---------------------------------------------------------------------------
# Structured Output Models (Pydantic)
# ---------------------------------------------------------------------------
# These models enforce structured responses when agents need to produce
# machine-readable output (e.g., for CRM integration or workflow steps).


class ResearchReport(BaseModel):
    """Structured research output for consistent reporting."""

    executive_summary: str = Field(description="2-3 sentence overview of findings")
    key_findings: list[str] = Field(description="List of key findings with sources")
    recommendations: list[str] = Field(description="Actionable next steps")
    sources: list[str] = Field(description="URLs and references used")
    confidence: str = Field(description="high, medium, or low confidence level")


class LeadReport(BaseModel):
    """Structured lead/client analysis for CRM integration."""

    company_name: str = Field(description="Company or person name")
    industry: str = Field(description="Industry or sector")
    score: int = Field(ge=1, le=10, description="Lead quality score 1-10")
    pain_points: list[str] = Field(description="Identified pain points or needs")
    next_steps: list[str] = Field(description="Recommended follow-up actions")
    notes: str = Field(description="Additional context or observations")


class TaskSummary(BaseModel):
    """Structured task output for automation tracking."""

    action: str = Field(description="What was done")
    status: str = Field(description="success, partial, or failed")
    details: str = Field(description="Details of the action taken")
    follow_up: list[str] = Field(default_factory=list, description="Follow-up items")


class ContentBrief(BaseModel):
    """Research brief for a content piece."""

    topic: str = Field(description="Topic title")
    pillar: str = Field(
        description="Content pillar (AI Trends, Tools, Business, Future, BTS)"
    )
    timeliness: str = Field(description="Why this topic matters right now")
    key_facts: list[str] = Field(
        description="Key facts with specific numbers and sources"
    )
    sources: list[str] = Field(description="Source URLs")
    angle: str = Field(description="Our unique perspective or take")
    hook_variants: list[str] = Field(
        description="2-3 hook options for the first 3 seconds"
    )
    visual_ideas: list[str] = Field(description="What to show on screen")
    relevance_score: int = Field(ge=1, le=10, description="Relevance to audience 1-10")


class VideoScene(BaseModel):
    """A single scene in a video storyboard."""

    text: str = Field(description="Narration text for this scene (Spanish)")
    visual: str = Field(description="Detailed image/visual description for generation")
    duration_seconds: int = Field(ge=2, le=15, description="Scene duration in seconds")
    transition: str = Field(
        default="fade", description="Transition type: fade, slide, cut, zoom"
    )


class VideoStoryboard(BaseModel):
    """Complete video storyboard ready for Remotion rendering."""

    title: str = Field(description="Video title")
    hook: str = Field(description="Selected hook (first 3 seconds)")
    language: str = Field(default="es", description="Content language")
    total_duration_seconds: int = Field(description="Total video duration")
    scenes: list[VideoScene] = Field(description="Ordered list of scenes")
    hashtags: list[str] = Field(description="Platform hashtags")
    cta: str = Field(description="Call to action at the end")
    platform: str = Field(
        default="instagram_reels",
        description="Target platform: instagram_reels, tiktok",
    )
    style: dict = Field(
        default_factory=lambda: {
            "font": "Inter",
            "primary_color": "#1a1a2e",
            "accent_color": "#e94560",
        },
        description="Visual style configuration",
    )


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

db = SqliteDb(db_file="nexus.db")

# ---------------------------------------------------------------------------
# Knowledge Base (LanceDB local + Voyage AI embeddings)
# ---------------------------------------------------------------------------
# LanceDB stores vectors locally (like SQLite). Voyage AI generates embeddings
# via API so your Mac CPU stays free. Drop files into knowledge/ and restart.

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
KNOWLEDGE_DIR.mkdir(exist_ok=True)

embedder = VoyageAIEmbedder(
    id="voyage-3-lite",
    dimensions=512,
)

vector_db = LanceDb(
    uri=str(Path(__file__).parent / "lancedb"),
    table_name="nexus_knowledge",
    search_type=SearchType.hybrid,
    embedder=embedder,
)

knowledge_base = Knowledge(
    name="NEXUS Knowledge",
    description="Internal documents, research, and reference material",
    vector_db=vector_db,
    contents_db=db,
)

# Learnings vector DB (separate table for what the agents learn over time).
learnings_db = LanceDb(
    uri=str(Path(__file__).parent / "lancedb"),
    table_name="nexus_learnings",
    search_type=SearchType.hybrid,
    embedder=embedder,
)

learnings_knowledge = Knowledge(
    name="NEXUS Learnings",
    description="Accumulated agent learnings, patterns, and corrections",
    vector_db=learnings_db,
    contents_db=db,
)

# Index all supported files in the knowledge/ folder on startup.
for file_path in sorted(KNOWLEDGE_DIR.iterdir()):
    if file_path.suffix.lower() in {".pdf", ".txt", ".md", ".csv", ".json"}:
        knowledge_base.insert(path=file_path, skip_if_exists=True)

# ---------------------------------------------------------------------------
# Model Configuration
# ---------------------------------------------------------------------------
# Primary: MiniMax M2.7 (released 2026-03-18). 200K context, tool calling,
# reasoning, 97% skill adherence. $0.30/$1.20 per 1M tokens (input/output).
# Fallback: Groq for ultra-fast/cheap tasks where MiniMax is overkill.

# --- MiniMax Models (primary) ---
# M2.7: flagship model. Tool calling, reasoning, 200K context, ~60 tps.
# SWE-Pro 56.22%, best open-source on GDPval-AA (ELO 1495).
# role_map: MiniMax API does not support the "developer" role that OpenAI uses
# for system prompts. We override the default map to keep standard roles.
_minimax_role_map = {
    "system": "system",
    "user": "user",
    "assistant": "assistant",
    "tool": "tool",
    "model": "assistant",
}

_minimax_kwargs = {
    "api_key": os.getenv("MINIMAX_API_KEY"),
    "base_url": "https://api.minimax.io/v1",
    "role_map": _minimax_role_map,
    # MiniMax does not support OpenAI's native structured outputs or json_schema
    # response_format. Disable to avoid "invalid chat setting (2013)" errors
    # from the learning/memory subsystem.
    "supports_native_structured_outputs": False,
    "supports_json_schema_outputs": False,
}

TOOL_MODEL = OpenAIChat(id="MiniMax-M2.7", **_minimax_kwargs)

# M2.7 Highspeed: identical results, ~100 tps. Best for streaming/fast UX.
# $0.60/$2.40 per 1M tokens (2x standard, but 2x faster).
FAST_MODEL = OpenAIChat(id="MiniMax-M2.7-highspeed", **_minimax_kwargs)

# Reasoning model: M2.7 standard for deep analysis (same model, used where
# reasoning=True and no tools are needed). Cheaper than highspeed.
REASONING_MODEL = OpenAIChat(id="MiniMax-M2.7", **_minimax_kwargs)

# --- Groq Models (fallback / ultra-cheap tasks) ---
GROQ_TOOL_MODEL = Groq(id="llama-3.3-70b-versatile")
GROQ_FAST_MODEL = Groq(id="llama-3.1-8b-instant")
GROQ_REASONING_MODEL = Groq(id="openai/gpt-oss-120b")
# GPT-OSS-20B: 1000 tps, tool calling, $0.075/M input. Ideal for routing/search.
GROQ_ROUTING_MODEL = Groq(id="openai/gpt-oss-20b")

# --- Learning Machine ---
# Full learning system: profile, memory, entities, and accumulated knowledge.
# Uses GROQ_FAST_MODEL (llama-3.1-8b, 560 tps) for extraction -- cheap and fast.
# All data stored in SQLite (nexus.db) + LanceDB (lancedb/) locally on Mac.
_learning = LearningMachine(
    model=GROQ_FAST_MODEL,
    knowledge=learnings_knowledge,
    user_profile=UserProfileConfig(mode=LearningMode.ALWAYS),
    user_memory=UserMemoryConfig(mode=LearningMode.ALWAYS),
    entity_memory=EntityMemoryConfig(mode=LearningMode.ALWAYS),
    learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
)

# ---------------------------------------------------------------------------
# Guardrails (applied to all agents and teams)
# ---------------------------------------------------------------------------
# PII detection blocks SSNs, credit cards, emails, phone numbers in input.
# Prompt injection blocks jailbreak attempts and instruction overrides.

_guardrails = [
    PIIDetectionGuardrail(),
    PromptInjectionGuardrail(),
]

# ---------------------------------------------------------------------------
# Skills (domain knowledge loaded on demand)
# ---------------------------------------------------------------------------
# Skills are lazy-loaded: agents see summaries, then load full instructions
# only when relevant. This saves tokens and keeps context lean.

SKILLS_DIR = Path(__file__).parent / "skills"
_skills = (
    Skills(loaders=[LocalSkills(str(SKILLS_DIR))]) if SKILLS_DIR.exists() else None
)

# ---------------------------------------------------------------------------
# Research Agent
# ---------------------------------------------------------------------------

research_agent = Agent(
    name="Research Agent",
    role="Search the web for current information and data",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=5)],
    retries=2,  # Retry on Groq tool-call validation errors
    pre_hooks=_guardrails,
    skills=_skills,
    instructions=[
        "You are a research specialist.",
        "Use the web_search tool to find current, accurate information.",
        "Always include sources with URLs and dates.",
        "Present data in structured formats when possible.",
        "Be thorough but concise.",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Knowledge Agent
# ---------------------------------------------------------------------------

knowledge_agent = Agent(
    name="Knowledge Agent",
    role="Query internal knowledge base and provide context",
    model=REASONING_MODEL,
    knowledge=knowledge_base,
    search_knowledge=True,
    pre_hooks=_guardrails,
    skills=_skills,
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=5,
    instructions=[
        "You are a knowledge specialist.",
        "Search the knowledge base for relevant information before answering.",
        "Provide context from internal knowledge and past analyses.",
        "Cross-reference information across different domains.",
        "Cite specific facts and relationships.",
        "When no relevant knowledge is found, work from conversation context.",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    update_memory_on_run=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# MCP Servers (conditionally loaded based on env vars)
# ---------------------------------------------------------------------------

_automation_tools: list = []

# n8n workflow builder: create, list, execute, manage n8n workflows.
# Limited to core workflow + execution tools to avoid context overflow.
if os.getenv("N8N_API_KEY"):
    _automation_tools.append(
        MCPTools(
            command="npx -y @makafeli/n8n-workflow-builder",
            env={
                "N8N_HOST": "http://localhost:5678",
                "N8N_API_KEY": os.getenv("N8N_API_KEY", ""),
            },
            include_tools=[
                "list_workflows",
                "get_workflow",
                "create_workflow",
                "update_workflow",
                "activate_workflow",
                "deactivate_workflow",
                "execute_workflow",
                "list_executions",
                "get_execution",
            ],
            timeout_seconds=30,
        )
    )

# Twenty CRM: manage contacts, companies, tasks, notes.
# Limited to core CRUD + search to avoid context overflow.
if os.getenv("TWENTY_API_KEY"):
    _automation_tools.append(
        MCPTools(
            command=f"node {Path.home()}/twenty-crm-mcp-server/index.js",
            env={
                "TWENTY_API_KEY": os.getenv("TWENTY_API_KEY", ""),
                "TWENTY_BASE_URL": os.getenv(
                    "TWENTY_BASE_URL", "http://localhost:3000"
                ),
            },
            include_tools=[
                "create_person",
                "list_people",
                "create_company",
                "list_companies",
                "create_task",
                "list_tasks",
                "create_note",
                "search_records",
            ],
            timeout_seconds=30,
        )
    )

# Obsidian vault: read, search, and manage notes from your Obsidian vault.
# Set OBSIDIAN_VAULT_PATH in ~/.zshrc (e.g., ~/Documents/MyVault)
# No API key needed -- runs locally via npx.
_obsidian_vault = os.getenv("OBSIDIAN_VAULT_PATH")
if _obsidian_vault:
    _automation_tools.append(
        MCPTools(
            command=f"npx -y @bitbonsai/mcpvault {_obsidian_vault}",
            include_tools=[
                "read_note",
                "write_note",
                "search_notes",
                "list_directory",
                "get_frontmatter",
                "manage_tags",
            ],
            timeout_seconds=30,
        )
    )

# ---------------------------------------------------------------------------
# Automation Agent
# ---------------------------------------------------------------------------

automation_agent = Agent(
    name="Automation Agent",
    role="Execute workflows, manage CRM, and run automations",
    model=TOOL_MODEL,  # Needs reliable tool calling for MCP
    tools=_automation_tools or None,  # type: ignore[arg-type]
    pre_hooks=_guardrails,
    skills=_skills,
    instructions=[
        "You are an automation specialist with access to n8n, Twenty CRM, and Obsidian.",
        "IMPORTANT: Always USE your tools to execute actions. NEVER just explain how to do something.",
        "When asked to do something, DO IT using your tools. Do not describe steps.",
        "",
        "## n8n (workflow automation)",
        "- List, create, execute, activate, and deactivate n8n workflows.",
        "- When asked to automate something, check if a workflow already exists first.",
        "",
        "## Twenty CRM",
        "- Manage contacts (people), companies, tasks, and notes.",
        "- Search across CRM records when asked about clients or leads.",
        "- Create new records when requested.",
        "",
        "## Obsidian (knowledge vault)",
        "- Read, search, and write notes in the Obsidian vault.",
        "- Use search_notes to find relevant information across all notes.",
        "- Create new notes when asked to save or document something.",
        "",
        "## Rules",
        "- ALWAYS call tools first, then report results.",
        "- Confirm before executing destructive or irreversible actions.",
        "- If a tool call fails, report the error. Do not explain manual steps.",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Cerebro Team
# ---------------------------------------------------------------------------

cerebro = Team(
    name="Cerebro",
    description="Multi-agent analysis system that decomposes complex tasks",
    members=[research_agent, knowledge_agent, automation_agent],
    mode=TeamMode.route,
    model=GROQ_ROUTING_MODEL,
    knowledge=knowledge_base,
    pre_hooks=_guardrails,
    determine_input_for_members=False,
    instructions=[
        "You are Cerebro, a router for the research team.",
        "",
        "## Routing rules (pick ONE member):",
        "- Web research, news, market data, competitors: route to Research Agent.",
        "- Internal documents, knowledge base, historical data: route to Knowledge Agent.",
        "- n8n workflows, CRM, Obsidian notes: route to Automation Agent.",
        "",
        "If the request needs multiple sources, route to Research Agent first.",
        "Do NOT add commentary. Return the member's response directly.",
    ],
    db=db,
    enable_session_summaries=False,
    add_history_to_context=False,
    show_members_responses=True,
    add_datetime_to_context=False,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Content Team (video production pipeline for Instagram Reels + TikTok)
# ---------------------------------------------------------------------------
# Specialized skills per agent role. Each agent only loads the skills it needs
# to keep context lean and responses focused.

_trend_scout_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "content-research")),
            LocalSkills(str(SKILLS_DIR / "content-strategy")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

_scriptwriter_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "content-strategy")),
            LocalSkills(str(SKILLS_DIR / "remotion-video")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

_analytics_skills = (
    Skills(loaders=[LocalSkills(str(SKILLS_DIR / "campaign-analytics"))])
    if SKILLS_DIR.exists()
    else None
)

_deep_search_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "deep-search")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

_deep_synthesis_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "deep-synthesis")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

# --- Trend Scout: finds and evaluates trending topics ---
trend_scout = Agent(
    name="Trend Scout",
    role="Research AI/tech trends and produce content briefs",
    model=GROQ_ROUTING_MODEL,
    tools=[
        DuckDuckGoTools(),
        WebSearchTools(fixed_max_results=3),
    ],
    retries=0,
    pre_hooks=_guardrails,
    skills=_trend_scout_skills,
    instructions=[
        "You are a trend researcher for a Spanish-language AI content brand.",
        "Your job is to find the most relevant AI/tech trends RIGHT NOW.",
        "",
        "## Process (STRICT: max 3 tool calls total)",
        "1. Do ONE broad search: 'AI news today' or similar (1 tool call)",
        "2. Do ONE focused search on the best topic found (1 tool call)",
        "3. Optionally check HackerNews for community signal (1 tool call)",
        "4. STOP searching. Produce the content brief from what you have.",
        "",
        "## IMPORTANT: Efficiency rules",
        "- You have a MAXIMUM of 3 tool calls. Plan them wisely.",
        "- Do NOT use read_article or fetch full pages. Work with search snippets.",
        "- Do NOT repeat searches with slightly different queries.",
        "- If the first search gives good results, skip the second search.",
        "- Prefer DuckDuckGo for web search (faster, no rate limits).",
        "",
        "## Output rules",
        "- Only topics from the last 48 hours (unless evergreen explainer)",
        "- Must have at least 2 credible sources (URLs from search results count)",
        "- Relevance score must be 7+ to proceed",
        "- Hooks must be in Spanish, punchy, under 10 words",
        "- Include specific numbers and data points from search snippets",
        "- Produce the ContentBrief structured output directly after searching",
    ],
    db=db,
    learning=_learning,
    add_datetime_to_context=True,
    markdown=True,
)

# --- Scriptwriter: turns briefs into video scripts + storyboards ---
scriptwriter = Agent(
    name="Scriptwriter",
    role="Write video scripts and storyboards for short-form content",
    model=FAST_MODEL,
    tools=[FileTools(base_dir=Path.home() / "nexus-videos")],
    pre_hooks=_guardrails,
    skills=_scriptwriter_skills,
    instructions=[
        "You are a professional scriptwriter for short-form video (Reels/TikTok).",
        "You write in Spanish (Latin America neutral).",
        "",
        "## Process (do this in ONE response)",
        "1. Read the content brief",
        "2. Generate EXACTLY 3 storyboard variants with different creative angles:",
        "   - Variant A: Emotional/storytelling angle",
        "   - Variant B: Data-driven/factual angle",
        "   - Variant C: Bold/provocative angle",
        "3. Save ALL 3 as separate JSON files using save_file:",
        "   - public/content/<slug>-a.json",
        "   - public/content/<slug>-b.json",
        "   - public/content/<slug>-c.json",
        "4. Reply with a brief summary of each variant (2 lines each)",
        "",
        "## Script Rules (apply to ALL 3 variants)",
        "- 5-6 scenes maximum per variant",
        "- First scene: hook (different hook per variant)",
        "- Sentences: max 15 words each",
        "- Tone: professional but accessible",
        "- Last scene: CTA (follow, comment, share)",
        "- Never start with greetings ('Hola', 'Bienvenidos')",
        "",
        "## Visual descriptions: be concise but specific",
        "- Max 20 words per visual description",
        "- Include: subject, setting, style",
        "- Do NOT write paragraphs for visuals",
        "",
        "## AUTO-SAVE (mandatory, no confirmation needed)",
        "Base directory is ~/nexus-videos, use relative paths only.",
        "",
        "## JSON SCHEMA (same for all 3 variants)",
        '{"title":"...","hook":"...","language":"es","total_duration_seconds":30,',
        '"scenes":[{"text":"...","visual":"...","duration_seconds":5,"transition":"fade"}],',
        '"hashtags":["#..."],"cta":"...","platform":"instagram_reels",',
        '"style":{"font":"Inter","primary_color":"#1a1a2e","accent_color":"#e94560"}}',
    ],
    db=db,
    learning=_learning,
    add_datetime_to_context=True,
    markdown=True,
)

# --- Creative Director: evaluates storyboard variants visually ---
creative_director = Agent(
    name="Creative Director",
    role="Evaluate video storyboards and describe how they will look visually",
    model=FAST_MODEL,
    tools=[FileTools(base_dir=Path.home() / "nexus-videos", enable_save_file=False)],
    pre_hooks=_guardrails,
    instructions=[
        "You are a creative director who evaluates video storyboards.",
        "You receive 3 storyboard variants (JSON files) and describe each visually.",
        "",
        "## Process",
        "1. Read the 3 JSON files provided",
        "2. For EACH variant, write a visual preview in Spanish:",
        "   - Overall mood and feel (1 sentence)",
        "   - Scene-by-scene visual flow (1 line per scene)",
        "   - Strongest moment (which scene will have most impact)",
        "   - Weakness (what could feel flat or repetitive)",
        "3. Give your recommendation: which variant is strongest and why",
        "",
        "## Format your response as:",
        "### Variante A: [title]",
        "**Mood**: ...",
        "**Flujo visual**: scene 1 → scene 2 → ...",
        "**Momento fuerte**: ...",
        "**Debilidad**: ...",
        "",
        "### Variante B: [title]",
        "(same format)",
        "",
        "### Variante C: [title]",
        "(same format)",
        "",
        "### Recomendacion: Variante [X]",
        "**Por que**: ...",
        "",
        "Keep it concise. The user will choose which variant to produce.",
    ],
    db=db,
    learning=_learning,
    add_datetime_to_context=True,
    markdown=True,
)
# --- Analytics Agent: tracks performance and generates reports ---
analytics_agent = Agent(
    name="Analytics Agent",
    role="Analyze content performance and generate optimization reports",
    model=TOOL_MODEL,
    tools=[
        WebSearchTools(fixed_max_results=5),
        CalculatorTools(),
        FileTools(),
    ],
    pre_hooks=_guardrails,
    skills=_analytics_skills,
    instructions=[
        "You are a social media analytics specialist.",
        "You analyze content performance for Instagram Reels and TikTok.",
        "",
        "## Capabilities",
        "- Generate weekly performance reports",
        "- Identify top-performing content patterns (hooks, topics, formats)",
        "- Recommend optimizations based on data",
        "- Track KPIs by growth stage",
        "- Compare pillar performance",
        "",
        "## Report Format",
        "Always produce structured reports with:",
        "- Executive summary (1 paragraph)",
        "- Numbers at a glance (table)",
        "- Top 3 and bottom 3 posts with analysis",
        "- Pillar and hook pattern analysis",
        "- 3 specific, data-driven recommendations for next week",
        "",
        "## Rules",
        "- Base recommendations on data, not assumptions",
        "- Engagement rate > raw view count for quality assessment",
        "- Save rate indicates value, share rate indicates resonance",
        "- Always compare week-over-week for trends",
    ],
    db=db,
    learning=_learning,
    add_datetime_to_context=True,
    markdown=True,
)

# --- Content Team: routes to the right member (no loop) ---
# For content creation, use the content_production_workflow instead (deterministic).
# This team exists for analytics requests and ad-hoc routing.
content_team = Team(
    name="Content Factory",
    description="Video content production team for Instagram Reels and TikTok",
    mode=TeamMode.route,
    members=[trend_scout, scriptwriter, analytics_agent],
    model=GROQ_ROUTING_MODEL,
    pre_hooks=_guardrails,
    determine_input_for_members=False,
    instructions=[
        "You are the Content Factory router.",
        "",
        "## Routing rules (pick ONE member, do NOT loop):",
        "- If the user asks to CREATE a video/content: route to Trend Scout.",
        "- If the user asks about ANALYTICS/metrics/performance: route to Analytics Agent.",
        "- If the user asks to WRITE a script from an existing brief: route to Scriptwriter.",
        "",
        "## For full video production (research + script):",
        "Tell the user: 'Use the content-production workflow for the full pipeline.'",
    ],
    db=db,
    enable_session_summaries=False,
    add_history_to_context=False,
    show_members_responses=True,
    add_datetime_to_context=False,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Content Production Workflow (deterministic pipeline with QA gates)
# ---------------------------------------------------------------------------

content_production_workflow = Workflow(
    name="content-production",
    description=(
        "Full content pipeline: trend research -> 3 script variants -> "
        "creative evaluation. Output is 3 VideoStoryboard JSONs + visual preview."
    ),
    db=SqliteDb(
        session_table="content_workflow_session",
        db_file="nexus.db",
    ),
    steps=[
        Step(name="Trend Research", agent=trend_scout),
        Step(name="Script Variants", agent=scriptwriter),
        Step(name="Creative Review", agent=creative_director),
    ],
)

# ---------------------------------------------------------------------------
# Workflows (deterministic pipelines)
# ---------------------------------------------------------------------------
# Unlike the Cerebro Team (which dynamically decides who to delegate to),
# workflows run agents in a fixed sequence. Use for repeatable processes.

# Synthesis agent: takes research + knowledge output and produces a structured report.
_synthesis_agent = Agent(
    name="Synthesis Agent",
    model=REASONING_MODEL,
    output_schema=ResearchReport,
    use_json_mode=True,  # Groq fallback for structured output
    instructions=[
        "You receive research findings and internal knowledge context.",
        "Synthesize everything into a structured research report.",
        "Be concise, analytical, and cite sources.",
    ],
)

client_research_workflow = Workflow(
    name="client-research",
    description="Research a client or topic: web search -> knowledge base -> structured report",
    db=SqliteDb(
        session_table="workflow_session",
        db_file="nexus.db",
    ),
    steps=[
        Step(name="Web Research", agent=research_agent),
        Step(name="Knowledge Lookup", agent=knowledge_agent),
        Step(name="Synthesis", agent=_synthesis_agent),
    ],
)

# ---------------------------------------------------------------------------
# Deep Research System
# ---------------------------------------------------------------------------
# Production-grade deep research: Planner → 3 parallel searchers (broadcast)
# → Reflector → Synthesizer. Inspired by Anthropic's multi-agent research,
# Exa/LangGraph patterns, and ACE context engineering principles.

# --- Planner: decomposes a research query into targeted sub-queries ---
_research_planner = Agent(
    name="Research Planner",
    role="Decompose research queries into targeted sub-queries",
    model=GROQ_ROUTING_MODEL,
    instructions=[
        "You are a research planner. Given a research topic, produce EXACTLY 3 sub-queries.",
        "",
        "## Rules",
        "- Each sub-query targets a DIFFERENT angle of the topic:",
        "  1. Current state / recent news / what's happening now",
        "  2. Data / numbers / market size / statistics",
        "  3. Key players / competitors / case studies / examples",
        "- Each sub-query must be a specific search query (not a vague topic)",
        "- Include site: filters when useful (e.g., site:techcrunch.com)",
        "- Write queries in the language most likely to find results (English for global, Spanish for Latam)",
        "",
        "## Output format (follow exactly)",
        "QUERY_1: [specific search query for current state]",
        "QUERY_2: [specific search query for data/numbers]",
        "QUERY_3: [specific search query for players/examples]",
        "SUFFICIENCY: [what would a complete answer include? 2-3 bullet points]",
    ],
    db=db,
    markdown=True,
)

# --- Three parallel searchers (used in broadcast mode) ---
_broad_scout = Agent(
    name="Broad Scout",
    role="General web search for current information",
    model=GROQ_ROUTING_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    retries=0,
    skills=_deep_search_skills,
    instructions=[
        "You are a web researcher. Search for the topic provided.",
        "",
        "## Rules",
        "- Do MAX 2 searches. One broad, one focused.",
        "- Work with search snippets. Do NOT fetch full pages.",
        "- Extract: key facts, numbers, dates, names, URLs.",
        "",
        "## Output format",
        "Return a structured summary:",
        "FINDINGS:",
        "- [finding 1 with source URL]",
        "- [finding 2 with source URL]",
        "- [finding 3 with source URL]",
        "GAPS: [what you couldn't find]",
    ],
    db=db,
    markdown=True,
)

_data_scout = Agent(
    name="Data Scout",
    role="Search for statistics, market data, and numbers",
    model=GROQ_ROUTING_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    retries=0,
    skills=_deep_search_skills,
    instructions=[
        "You are a data researcher. Search for statistics and numbers on the topic.",
        "",
        "## Rules",
        "- Do MAX 2 searches. Focus on data, reports, market size, growth rates.",
        "- Prioritize: government reports, industry analyses, research firms.",
        "- Include site: filters like site:statista.com, site:mckinsey.com",
        "",
        "## Output format",
        "Return a structured summary:",
        "DATA_POINTS:",
        "- [stat 1 with number and source URL]",
        "- [stat 2 with number and source URL]",
        "- [stat 3 with number and source URL]",
        "GAPS: [what data you couldn't find]",
    ],
    db=db,
    markdown=True,
)

_source_scout = Agent(
    name="Source Scout",
    role="Find primary sources, case studies, and key players",
    model=GROQ_ROUTING_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    retries=0,
    skills=_deep_search_skills,
    instructions=[
        "You are a source researcher. Find primary sources and case studies.",
        "",
        "## Rules",
        "- Do MAX 2 searches. Focus on company blogs, official announcements, case studies.",
        "- Look for: who are the key players, what are they doing, real examples.",
        "- Prioritize primary sources over news articles about them.",
        "",
        "## Output format",
        "Return a structured summary:",
        "SOURCES:",
        "- [source 1: company/person, what they did, URL]",
        "- [source 2: company/person, what they did, URL]",
        "- [source 3: company/person, what they did, URL]",
        "GAPS: [what sources you couldn't find]",
    ],
    db=db,
    markdown=True,
)

# --- Research team: runs 3 scouts in parallel via broadcast ---
_research_team = Team(
    name="Research Squad",
    description="Three parallel researchers covering different angles",
    mode=TeamMode.broadcast,
    members=[_broad_scout, _data_scout, _source_scout],
    model=GROQ_ROUTING_MODEL,
    instructions=[
        "Send the research query to ALL members simultaneously.",
        "Return all their findings combined without modification.",
    ],
    show_members_responses=True,
    markdown=True,
)

# --- Reflector: evaluates if research is sufficient ---
_research_reflector = Agent(
    name="Research Reflector",
    role="Evaluate research completeness and identify critical gaps",
    model=GROQ_REASONING_MODEL,
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=4,
    instructions=[
        "You evaluate research findings for completeness.",
        "",
        "## Process",
        "1. Read all findings from the research team",
        "2. Check against the sufficiency criteria from the planner",
        "3. Identify CRITICAL gaps (not nice-to-haves)",
        "",
        "## Output",
        "ASSESSMENT: [SUFFICIENT or INSUFFICIENT]",
        "COVERAGE: [what percentage of the topic is covered, roughly]",
        "CRITICAL_GAPS: [list only gaps that would make the report misleading if missing]",
        "ADDITIONAL_QUERIES: [if INSUFFICIENT, 1-2 specific queries to fill gaps. If SUFFICIENT, write NONE]",
        "",
        "## Rules",
        "- Be strict: 70%+ coverage with no misleading gaps = SUFFICIENT",
        "- Do NOT request more research just for completeness. Good enough is good enough.",
        "- If the topic is niche and hard to find data on, lower your bar.",
    ],
    db=db,
    markdown=True,
)

# --- Synthesizer: produces the final research report ---
_research_synthesizer = Agent(
    name="Research Synthesizer",
    role="Produce comprehensive research reports from collected findings",
    model=TOOL_MODEL,
    tools=[FileTools(base_dir=Path(__file__).parent / "knowledge")],
    skills=_deep_synthesis_skills,
    output_schema=ResearchReport,
    use_json_mode=True,
    instructions=[
        "You synthesize research findings into a comprehensive report.",
        "",
        "## Process",
        "1. Read ALL findings from the research team and reflector assessment",
        "2. Organize by theme, not by source",
        "3. Produce a ResearchReport with:",
        "   - executive_summary: 2-3 sentences, the key takeaway",
        "   - key_findings: specific facts with numbers and source URLs",
        "   - recommendations: actionable next steps based on findings",
        "   - sources: all URLs cited",
        "   - confidence: high/medium/low based on source quality and coverage",
        "",
        "4. Save the report as a markdown file using save_file:",
        "   Filename: research-<topic-slug>-<date>.md",
        "   This makes it searchable in the knowledge base for future queries.",
        "",
        "## Rules",
        "- Every finding must have a source URL. No unsourced claims.",
        "- If data conflicts between sources, note the conflict.",
        "- Write in Spanish if the topic is Latam-specific, English otherwise.",
        "- Be analytical, not descriptive. Say what it MEANS, not just what it IS.",
    ],
    db=db,
    learning=_learning,
    markdown=True,
)

# --- Deep Research Workflow ---
deep_research_workflow = Workflow(
    name="deep-research",
    description=(
        "Production-grade deep research: planner decomposes the query, "
        "3 searchers investigate in parallel, reflector evaluates completeness, "
        "synthesizer produces a structured report saved to knowledge base."
    ),
    db=SqliteDb(
        session_table="deep_research_session",
        db_file="nexus.db",
    ),
    steps=[
        Step(name="Plan", agent=_research_planner),
        Step(name="Research", team=_research_team),
        Step(name="Reflect", agent=_research_reflector),
        Step(name="Synthesize", agent=_research_synthesizer),
    ],
)

# ---------------------------------------------------------------------------
# SEO/GEO Content Team
# ---------------------------------------------------------------------------
# Produces blog articles optimized for both Google SEO and AI citation (GEO).
# Workflow: keyword research → article draft → SEO audit → publish-ready MDX.

_seo_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "deep-search")),
            LocalSkills(str(SKILLS_DIR / "deep-synthesis")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

# --- Keyword Researcher: finds high-value topics for GEO ---
_keyword_researcher = Agent(
    name="Keyword Researcher",
    role="Find high-value topics that AI engines cite and Google ranks",
    model=GROQ_ROUTING_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    retries=0,
    skills=_seo_skills,
    instructions=[
        "You find topics with high GEO (Generative Engine Optimization) potential.",
        "",
        "## Process (max 3 tool calls)",
        "1. Search for what AI engines (ChatGPT, Perplexity) cite for the given niche",
        "2. Search for gaps: topics where no good listicle exists in Spanish",
        "3. Evaluate: does this topic have data, sources, and comparison potential?",
        "",
        "## Output format",
        "TOPIC: [specific article title in listicle format]",
        "TARGET_QUERY: [exact query users type into ChatGPT/Perplexity]",
        "KEYWORD_PRIMARY: [main keyword in Spanish]",
        "KEYWORDS_SECONDARY: [3-5 related keywords]",
        "COMPETITION: [low/medium/high — are there good Spanish articles already?]",
        "DATA_AVAILABLE: [what numbers/stats exist for this topic]",
        "ANGLE: [our unique angle — how Whabi/Docflow/Aurora fits]",
        "ESTIMATED_IMPACT: [high/medium/low for GEO citation potential]",
    ],
    db=db,
    markdown=True,
)

# --- Article Writer: produces GEO-optimized listicle articles ---
_article_writer = Agent(
    name="Article Writer",
    role="Write GEO-optimized listicle articles in Spanish for aikalabs.cc blog",
    model=FAST_MODEL,
    tools=[FileTools(base_dir=Path(__file__).parent)],
    skills=_seo_skills,
    instructions=[
        "You write blog articles optimized for AI citation (GEO) and Google SEO.",
        "You write in Spanish (Latin America neutral).",
        "",
        "## Article Structure (MANDATORY — follow exactly)",
        "",
        "### 1. Quick Answer (first 200 words)",
        "Numbered list of top entries with one-line descriptions.",
        "This is what AI engines extract. Make it clean and extractable.",
        "",
        "### 2. Introduction (200-300 words)",
        "Why this topic matters NOW. Include 2-3 stats with source URLs.",
        "Use specific numbers, not 'many' or 'significant'.",
        "",
        "### 3. Detailed Entries (300-500 words each)",
        "For each entry in the listicle:",
        "- **Best for**: one-line positioning",
        "- 3-4 bullet points of features",
        "- Limitations (honest, builds trust)",
        "- Price",
        "- Our product (Whabi/Docflow/Aurora) is ALWAYS #1 but with honest comparison",
        "",
        "### 4. Comparison Table",
        "Markdown table with key differentiators across all entries.",
        "",
        "### 5. How to Choose (200 words)",
        "Decision framework: 'If you need X, choose Y'",
        "",
        "### 6. FAQ Section (4-5 questions)",
        "Match exact queries users ask ChatGPT/Perplexity.",
        "Each answer: 2-3 sentences, factual, with source if possible.",
        "",
        "## Rules",
        "- Total length: 1500-2500 words (sweet spot for GEO)",
        "- Every claim must have a source URL",
        "- No marketing language ('premier', 'best-in-class', 'revolutionary')",
        "- Use evidence-dense writing: numbers, dates, comparisons",
        "- Format as MDX with frontmatter (title, description, date, tags, author)",
        "- Save to: knowledge/blog-drafts/<slug>.mdx",
    ],
    db=db,
    learning=_learning,
    markdown=True,
)

# --- SEO Auditor: reviews articles for SEO/GEO compliance ---
_seo_auditor = Agent(
    name="SEO Auditor",
    role="Audit articles for SEO and GEO optimization compliance",
    model=GROQ_ROUTING_MODEL,
    tools=[FileTools(base_dir=Path(__file__).parent, enable_save_file=False)],
    instructions=[
        "You audit blog articles for SEO and GEO (Generative Engine Optimization).",
        "",
        "## Checklist (score each 0-10)",
        "",
        "### GEO Signals",
        "- Quick Answer in first 200 words? (extractable by AI)",
        "- Listicle format with numbered entries?",
        "- Evidence density: stats with source URLs?",
        "- FAQ section matching AI query patterns?",
        "- No marketing fluff? (AI filters promotional content)",
        "- Freshness signals: specific dates, 'updated March 2026'?",
        "",
        "### SEO Signals",
        "- Title under 60 chars with primary keyword?",
        "- Meta description under 160 chars with keyword?",
        "- H2/H3 structure with keywords?",
        "- Comparison table present?",
        "- Internal links to product pages (/whabi, /docflow, /aurora)?",
        "- At least 1500 words?",
        "",
        "## Output format",
        "SCORE: [X/100]",
        "GEO_SCORE: [X/60]",
        "SEO_SCORE: [X/40]",
        "ISSUES:",
        "- [issue 1 with specific fix]",
        "- [issue 2 with specific fix]",
        "VERDICT: [PUBLISH / REVISE / REWRITE]",
    ],
    db=db,
    markdown=True,
)

# --- SEO/GEO Content Workflow ---
seo_content_workflow = Workflow(
    name="seo-content",
    description=(
        "SEO/GEO content pipeline: keyword research → article draft → "
        "SEO audit. Produces publish-ready MDX articles for aikalabs.cc blog."
    ),
    db=SqliteDb(
        session_table="seo_content_session",
        db_file="nexus.db",
    ),
    steps=[
        Step(name="Keyword Research", agent=_keyword_researcher),
        Step(name="Article Draft", agent=_article_writer),
        Step(name="SEO Audit", agent=_seo_auditor),
    ],
)

# ---------------------------------------------------------------------------
# Registry (exposes components to AgentOS Studio UI)
# ---------------------------------------------------------------------------

# Build tool list: always include free tools, conditionally add paid ones.
_registry_tools: list = [
    # --- Free (no API key needed) ---
    ArxivTools(),
    CalculatorTools(),
    CsvTools(),
    DuckDuckGoTools(),
    FileTools(),
    HackerNewsTools(),
    KnowledgeTools(knowledge=knowledge_base),
    Newspaper4kTools(),
    PythonTools(),
    ReasoningTools(),
    SpiderTools(),
    UserControlFlowTools(),
    WebBrowserTools(),
    WebSearchTools(fixed_max_results=5),
    WikipediaTools(),
    WorkflowTools(workflow=client_research_workflow),
    YFinanceTools(),
    YouTubeTools(),
]

# --- Require API keys: only register if the key is set ---
if os.getenv("REDDIT_CLIENT_ID"):
    _registry_tools.append(RedditTools())
if os.getenv("EMAIL_SENDER") and os.getenv("EMAIL_PASSKEY"):
    _registry_tools.append(EmailTools())
if os.getenv("EXA_API_KEY"):
    _registry_tools.append(ExaTools())
if os.getenv("GITHUB_TOKEN"):
    _registry_tools.append(GithubTools())
if os.getenv("SLACK_BOT_TOKEN"):
    _registry_tools.append(SlackTools())
if os.getenv("TAVILY_API_KEY"):
    _registry_tools.append(TavilyTools())
if os.getenv("TODOIST_API_KEY"):
    _registry_tools.append(TodoistTools())
if os.getenv("WHATSAPP_ACCESS_TOKEN"):
    _registry_tools.append(WhatsAppTools())
if os.getenv("X_BEARER_TOKEN"):
    _registry_tools.append(XTools())
if os.getenv("FIRECRAWL_API_KEY"):
    _registry_tools.append(FirecrawlTools())
if os.getenv("BROWSERBASE_API_KEY") and os.getenv("BROWSERBASE_PROJECT_ID"):
    _registry_tools.append(BrowserbaseTools())
if os.getenv("GOOGLE_API_KEY"):
    _registry_tools.append(NanoBananaTools())
if os.getenv("LUMAAI_API_KEY"):
    _registry_tools.append(LumaLabTools())

registry = Registry(
    name="NEXUS Registry",
    tools=_registry_tools,
    models=[
        TOOL_MODEL,
        FAST_MODEL,
        REASONING_MODEL,
        GROQ_TOOL_MODEL,
        GROQ_FAST_MODEL,
        GROQ_REASONING_MODEL,
    ],
    dbs=[db],
    vector_dbs=[vector_db],
)

# ---------------------------------------------------------------------------
# AgentOS
# ---------------------------------------------------------------------------

agent_os = AgentOS(
    id="nexus",
    description="NEXUS Cerebro - Multi-agent analysis system",
    agents=[
        research_agent,
        knowledge_agent,
        automation_agent,
        trend_scout,
        scriptwriter,
        creative_director,
        analytics_agent,
    ],
    teams=[cerebro, content_team],
    workflows=[client_research_workflow, content_production_workflow, deep_research_workflow, seo_content_workflow],
    knowledge=[knowledge_base],
    registry=registry,
    db=db,
    tracing=True,
    scheduler=True,
    scheduler_poll_interval=30,  # Check for due schedules every 30 seconds
)
app = agent_os.get_app()

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # reload=False required when using MCP tools (lifespan conflicts)
    agent_os.serve(app="nexus:app", port=7777, reload=False)
