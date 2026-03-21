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
from agno.approval.decorator import approval
from agno.compression.manager import CompressionManager
from agno.os.interfaces.whatsapp.whatsapp import Whatsapp
from agno.tools.decorator import tool
from agno.db.sqlite import SqliteDb
from agno.eval.base import BaseEval
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
from agno.tools.coding import CodingTools
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
from agno.workflow.steps import Steps
from agno.workflow.parallel import Parallel
from agno.workflow.loop import Loop
from agno.workflow.condition import Condition
from agno.workflow.router import Router
from agno.workflow.types import StepInput, StepOutput
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


class SupportTicket(BaseModel):
    """Structured support interaction for CRM logging and analytics."""

    product: str = Field(description="Product: whabi, docflow, or aurora")
    intent: str = Field(
        description="Customer intent: faq, pricing, payment, complaint, "
        "technical_issue, appointment, document_status, subscription, other"
    )
    urgency: str = Field(description="low, medium, high, or critical")
    summary: str = Field(description="One-line summary of the customer request")
    resolution: str = Field(description="What was done or recommended")
    escalated: bool = Field(default=False, description="Whether escalated to human")
    lead_score: int = Field(
        default=0, ge=0, le=10,
        description="Lead quality score 0-10 (0 = not a lead, 10 = ready to close)",
    )


class PaymentConfirmation(BaseModel):
    """Structured payment request requiring human approval."""

    product: str = Field(description="Product: whabi, docflow, or aurora")
    client_name: str = Field(description="Client name as provided")
    amount: str = Field(description="Payment amount with currency (e.g., '$150 USD')")
    method: str = Field(
        description="Payment method: transfer, card, paypal, crypto, other"
    )
    reference: str = Field(default="", description="Payment reference or invoice number")
    notes: str = Field(default="", description="Additional context about the payment")


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

# --- Context Compression ---
# Compresses long tool results to save tokens in agents with heavy tool usage.
# Uses GROQ_FAST_MODEL (llama-3.1-8b, 560 tps) for cheap/fast compression.
_compression = CompressionManager(
    model=GROQ_FAST_MODEL,
    compress_tool_results=True,
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
# Background Quality Eval (post-hook on agent responses)
# ---------------------------------------------------------------------------
# After each response, evaluates quality in the background without blocking.
# Logs results for iterative prompt improvement. Uses GROQ_FAST_MODEL (cheap).

class ResponseQualityEval(BaseEval):
    """Evaluate agent response quality as a post-hook.

    Checks: relevance, completeness, hallucination risk, actionability.
    Logs a structured score to the agent's learning system.
    """

    def pre_check(self, run_input):  # type: ignore[override]
        """No pre-check needed."""

    async def async_pre_check(self, run_input):  # type: ignore[override]
        """No async pre-check needed."""

    def post_check(self, run_output):  # type: ignore[override]
        """Score the response quality and log to learnings."""
        content = run_output.get_content_as_string() if run_output.content else ""
        if not content or len(content) < 50:
            return  # Skip trivially short responses

        agent_name = getattr(run_output, "agent_name", "unknown")
        input_text = getattr(run_output, "input", "")

        # Simple heuristic scoring (no extra LLM call to keep it fast/free)
        score = 10
        issues: list[str] = []

        # Check for empty or very short responses
        if len(content) < 100:
            score -= 2
            issues.append("response_too_short")

        # Check for hallucination signals (claims without sources)
        has_urls = "http" in content or "www." in content
        has_claims = any(w in content.lower() for w in ["according to", "studies show", "research indicates", "data shows"])
        if has_claims and not has_urls:
            score -= 3
            issues.append("claims_without_sources")

        # Check for hedging (low confidence signals)
        hedge_words = ["i think", "maybe", "perhaps", "i'm not sure", "it might"]
        hedge_count = sum(1 for w in hedge_words if w in content.lower())
        if hedge_count >= 2:
            score -= 1
            issues.append("excessive_hedging")

        # Check for actionability (does it give next steps?)
        action_signals = ["you should", "next step", "recommend", "try", "consider"]
        has_actions = any(w in content.lower() for w in action_signals)
        if not has_actions and len(content) > 500:
            score -= 1
            issues.append("no_actionable_advice")

        score = max(1, min(10, score))

        # Log to learnings knowledge base (non-blocking, best-effort)
        try:
            eval_record = (
                f"EVAL: agent={agent_name} score={score}/10 "
                f"issues={','.join(issues) or 'none'} "
                f"input_preview={str(input_text)[:100]}"
            )
            learnings_knowledge.insert(content=eval_record, skip_if_exists=True)
        except Exception:
            pass  # Never block the response for eval logging

    async def async_post_check(self, run_output):  # type: ignore[override]
        """Async version delegates to sync."""
        self.post_check(run_output)


_quality_eval = ResponseQualityEval()

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
    post_hooks=[_quality_eval],
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
    followups=True,
    num_followups=3,
    followup_model=GROQ_FAST_MODEL,
    compression_manager=_compression,
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
    post_hooks=[_quality_eval],
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
    followups=True,
    num_followups=3,
    followup_model=GROQ_FAST_MODEL,
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
    post_hooks=[_quality_eval],
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
    followups=True,
    num_followups=3,
    followup_model=GROQ_FAST_MODEL,
    compression_manager=_compression,
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
    learning=_learning,
    enable_session_summaries=False,
    add_history_to_context=False,
    show_members_responses=True,
    add_datetime_to_context=False,
    markdown=True,
    followups=True,
    num_followups=3,
    followup_model=GROQ_FAST_MODEL,
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

# --- Approval-wrapped file tools for sensitive write operations ---
# The @approval decorator requires human confirmation before the agent saves
# files. This prevents accidental overwrites and creates an audit trail.
_video_file_tools = FileTools(base_dir=Path.home() / "nexus-videos")
_article_file_tools = FileTools(base_dir=Path(__file__).parent)


@approval  # type: ignore[arg-type]  # agno's @approval handles Function objects at runtime
@tool(requires_confirmation=True)
def save_video_file(contents: str, file_name: str, overwrite: bool = True) -> str:
    """Save a video storyboard JSON file. Requires approval before writing."""
    return _video_file_tools.save_file(contents, file_name, overwrite)


@approval(type="audit")
@tool(requires_confirmation=True)
def save_article_file(contents: str, file_name: str, overwrite: bool = True) -> str:
    """Save a blog article MDX file. Creates an audit record of the write."""
    return _article_file_tools.save_file(contents, file_name, overwrite)


# --- WhatsApp Support Tools (shared across product agents) ---
# Payment confirmation requires human approval before processing.
# CRM logging and escalation are audit-only (non-blocking).

@approval  # type: ignore[arg-type]  # blocking: pauses until admin approves
@tool(requires_confirmation=True)
def confirm_payment(
    product: str,
    client_name: str,
    amount: str,
    method: str,
    reference: str = "",
) -> str:
    """Confirm a client payment. Requires human approval before processing.

    Use this when a client says they made a payment or wants to pay.
    The payment will be held until an admin approves it.
    """
    return (
        f"PAYMENT_PENDING_APPROVAL: product={product} client={client_name} "
        f"amount={amount} method={method} ref={reference}"
    )


@approval(type="audit")
@tool(requires_confirmation=True)
def log_support_ticket(
    product: str,
    intent: str,
    summary: str,
    resolution: str,
    urgency: str = "medium",
    lead_score: int = 0,
) -> str:
    """Log a support interaction to the CRM for tracking and analytics.

    Call this after resolving any customer query to maintain records.
    """
    return (
        f"TICKET_LOGGED: product={product} intent={intent} urgency={urgency} "
        f"lead_score={lead_score} summary={summary[:100]}"
    )


@tool()
def escalate_to_human(
    product: str,
    reason: str,
    client_name: str = "unknown",
    urgency: str = "high",
) -> str:
    """Escalate a conversation to a human agent.

    Use when: complaint is serious, payment dispute, legal/compliance issue,
    client explicitly asks for a human, or you cannot resolve the issue.
    """
    return (
        f"ESCALATED: product={product} client={client_name} urgency={urgency} "
        f"reason={reason}"
    )


# --- Domain skills for product support agents ---
_whabi_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "whabi")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

_docflow_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "docflow")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

_aurora_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "aurora")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)


# --- Scriptwriter: turns briefs into video scripts + storyboards ---
scriptwriter = Agent(
    name="Scriptwriter",
    role="Write video scripts and storyboards for short-form content",
    model=FAST_MODEL,
    tools=[save_video_file, _video_file_tools],
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
    learning=_learning,
    enable_session_summaries=False,
    add_history_to_context=False,
    show_members_responses=True,
    add_datetime_to_context=False,
    markdown=True,
    followups=True,
    num_followups=3,
    followup_model=GROQ_FAST_MODEL,
)

# ---------------------------------------------------------------------------
# Content Production Workflow v2
# ---------------------------------------------------------------------------
# Pattern: Steps → Parallel(variants) → Router(HITL selection) → save
# Applies: Fan-out for variants, human-in-the-loop for selection,
# context compaction between phases.

def _compact_research(step_input: StepInput) -> StepOutput:
    """Compaction function: extract only the brief from Trend Scout output."""
    content = step_input.previous_step_content or step_input.input or ""
    # Pass through — the agent output is already a structured brief.
    # This function exists as a hook for future compaction logic.
    return StepOutput(content=content)

content_production_workflow = Workflow(
    name="content-production",
    description=(
        "Full content pipeline: research → compact → 3 script variants "
        "→ creative review → human selects best → save."
    ),
    db=SqliteDb(
        session_table="content_workflow_session",
        db_file="nexus.db",
    ),
    steps=[
        # Phase 1: Research (fast, cheap model)
        Step(name="Trend Research", agent=trend_scout, skip_on_failure=False),
        # Phase 2: Compact research into clean brief
        Step(name="Compact Brief", executor=_compact_research),
        # Phase 3: Generate 3 variants (single agent, one call)
        Step(name="Script Variants", agent=scriptwriter),
        # Phase 4: Creative review evaluates all 3
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

# ---------------------------------------------------------------------------
# Client Research Workflow v2
# ---------------------------------------------------------------------------
# Pattern: Parallel(web + knowledge) → Condition(enough data?) → Synthesis
# Applies: Fan-out for parallel research, conditional extra search,
# error tolerance on non-critical steps.

client_research_workflow = Workflow(
    name="client-research",
    description=(
        "Research a client or topic: parallel web + knowledge search, "
        "conditional deep dive if needed, structured synthesis report."
    ),
    db=SqliteDb(
        session_table="workflow_session",
        db_file="nexus.db",
    ),
    steps=[
        # Phase 1: Parallel research (web + internal knowledge simultaneously)
        Parallel(
            Step(
                name="Web Research",
                agent=research_agent,
                skip_on_failure=True,
                max_retries=2,
            ),
            Step(
                name="Knowledge Lookup",
                agent=knowledge_agent,
                skip_on_failure=True,
                max_retries=1,
            ),
            name="Parallel Research",
        ),
        # Phase 2: Synthesize all findings into structured report
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
    compression_manager=_compression,
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
    compression_manager=_compression,
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
    compression_manager=_compression,
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
    compression_manager=_compression,
)

# --- Deep Research Workflow v3 ---
# Pattern: Plan → Parallel(3 scouts) → Loop(reflect → search if needed)
#        → Synthesize → Loop(quality critic → revise if score < 7)
# v3 adds iterative quality refinement after synthesis.

def _check_sufficiency(step_input: StepInput) -> StepOutput:
    """Check if research is sufficient based on reflector output."""
    content = step_input.previous_step_content or ""
    is_sufficient = "SUFFICIENT" in content.upper() and "INSUFFICIENT" not in content.upper()
    return StepOutput(
        content=content,
        stop=is_sufficient,  # Stop the loop if sufficient
    )

# --- Quality Critic: scores the final report and provides feedback ---
_research_critic = Agent(
    name="Research Critic",
    role="Score research reports for quality and provide improvement feedback",
    model=GROQ_REASONING_MODEL,
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=4,
    instructions=[
        "You evaluate research reports for quality and completeness.",
        "",
        "## Scoring Criteria (each 0-10)",
        "1. EVIDENCE: Are claims backed by specific data and source URLs?",
        "2. ANALYSIS: Does it explain what findings MEAN, not just what they ARE?",
        "3. STRUCTURE: Is it well-organized with clear executive summary?",
        "4. ACTIONABILITY: Are recommendations specific and implementable?",
        "5. SOURCES: Are sources diverse, credible, and properly cited?",
        "",
        "## Output format (follow exactly)",
        "SCORE: [average of 5 criteria, 0-10]",
        "EVIDENCE: [X/10] - [one-line justification]",
        "ANALYSIS: [X/10] - [one-line justification]",
        "STRUCTURE: [X/10] - [one-line justification]",
        "ACTIONABILITY: [X/10] - [one-line justification]",
        "SOURCES: [X/10] - [one-line justification]",
        "VERDICT: [PASS if SCORE >= 7, REVISE if SCORE < 7]",
        "FEEDBACK: [if REVISE, 2-3 specific improvements needed]",
    ],
    db=db,
    markdown=True,
)

def _check_report_quality(step_input: StepInput) -> StepOutput:
    """Check if the research report meets quality threshold (score >= 7)."""
    content = step_input.previous_step_content or ""
    is_passing = "PASS" in content.upper() and "REVISE" not in content.upper()
    return StepOutput(
        content=content,
        stop=is_passing,  # Stop the loop if quality is sufficient
    )

deep_research_workflow = Workflow(
    name="deep-research",
    description=(
        "Production deep research v3: plan → 3 parallel searchers → "
        "reflection loop → synthesis → quality scoring loop (max 2 revisions)."
    ),
    db=SqliteDb(
        session_table="deep_research_session",
        db_file="nexus.db",
    ),
    steps=[
        # Phase 1: Decompose query into sub-queries
        Step(name="Plan", agent=_research_planner),
        # Phase 2: 3 searchers in parallel (native Parallel, not broadcast team)
        Parallel(
            Step(name="Broad Search", agent=_broad_scout, skip_on_failure=True),
            Step(name="Data Search", agent=_data_scout, skip_on_failure=True),
            Step(name="Source Search", agent=_source_scout, skip_on_failure=True),
            name="Parallel Research",
        ),
        # Phase 3: Reflection loop — evaluate, optionally search more (max 2 rounds)
        Loop(
            steps=[
                Step(name="Reflect", agent=_research_reflector),
                Step(name="Check Sufficiency", executor=_check_sufficiency),
            ],
            max_iterations=2,
            forward_iteration_output=True,
        ),
        # Phase 4: Synthesize into structured report + save to knowledge/
        Step(name="Synthesize", agent=_research_synthesizer),
        # Phase 5: Quality scoring loop — critic scores, synthesizer revises if < 7
        Loop(
            steps=[
                Step(name="Quality Review", agent=_research_critic),
                Step(name="Check Quality", executor=_check_report_quality),
            ],
            max_iterations=2,
            forward_iteration_output=True,
        ),
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
            LocalSkills(str(SKILLS_DIR / "seo-geo")),
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
    tools=[save_article_file, _article_file_tools],
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

# --- SEO/GEO Content Workflow v2 ---
# Pattern: Research → Write → Loop(Audit → Revise until PUBLISH) → save
# Applies: Iterative refinement loop, structured audit scoring,
# early termination when quality threshold met.

def _check_publish_ready(step_input: StepInput) -> StepOutput:
    """Check if the SEO auditor approved the article for publishing."""
    content = step_input.previous_step_content or ""
    is_ready = "PUBLISH" in content.upper() and "REWRITE" not in content.upper()
    return StepOutput(
        content=content,
        stop=is_ready,  # Stop the loop if ready to publish
    )

seo_content_workflow = Workflow(
    name="seo-content",
    description=(
        "SEO/GEO content pipeline: keyword research → article draft → "
        "audit/revise loop (max 2 rounds) → publish-ready MDX."
    ),
    db=SqliteDb(
        session_table="seo_content_session",
        db_file="nexus.db",
    ),
    steps=[
        # Phase 1: Find the right topic
        Step(name="Keyword Research", agent=_keyword_researcher),
        # Phase 2: Write the first draft
        Step(name="Article Draft", agent=_article_writer),
        # Phase 3: Audit/revise loop — auditor scores, writer revises if needed
        Loop(
            steps=[
                Step(name="SEO Audit", agent=_seo_auditor),
                Step(name="Check Quality", executor=_check_publish_ready),
            ],
            max_iterations=2,
            forward_iteration_output=True,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Code Review Agent (Gcode pattern)
# ---------------------------------------------------------------------------
# Sandboxed coding agent that reviews, writes, and iterates on code.
# Learns project conventions, gotchas, and patterns over time.
# All file operations restricted to workspace/ directory.

_code_workspace = Path(__file__).parent / "workspace"
_code_workspace.mkdir(exist_ok=True)

code_review_agent = Agent(
    name="Code Review Agent",
    role="Review, write, and iterate on code with self-learning",
    model=TOOL_MODEL,
    tools=[
        CodingTools(base_dir=str(_code_workspace)),
        ReasoningTools(),
    ],
    pre_hooks=_guardrails,
    reasoning=True,
    reasoning_min_steps=2,
    reasoning_max_steps=5,
    instructions=[
        "You are a code review specialist that gets sharper with every review.",
        "You operate in a sandboxed workspace directory. All files live there.",
        "",
        "## Capabilities",
        "- Review code for bugs, security issues, and style problems",
        "- Write and edit code files in the workspace",
        "- Run shell commands to test and validate code",
        "- Learn project conventions and remember past mistakes",
        "",
        "## Review Process",
        "1. Read the code carefully using read_file",
        "2. Think through potential issues using reasoning tools",
        "3. Produce a structured review:",
        "   - SEVERITY: critical / warning / info",
        "   - ISSUE: what's wrong and where (file:line)",
        "   - FIX: specific code change to resolve it",
        "   - WHY: explanation of the impact",
        "",
        "## Rules",
        "- Always check for: SQL injection, XSS, hardcoded secrets, race conditions",
        "- Flag missing error handling and edge cases",
        "- Suggest idiomatic improvements for the language",
        "- If you make a mistake, learn from it for next time",
        "- Use relative paths within the workspace only",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
    compression_manager=_compression,
)

# ---------------------------------------------------------------------------
# WhatsApp Customer Support Pipeline
# ---------------------------------------------------------------------------
# Production support system with per-product routing. Each product has a
# specialized agent with domain skills, shared tools (payment, CRM, escalation),
# and a general fallback for unclassified messages.

_support_tools = [confirm_payment, log_support_ticket, escalate_to_human]

# --- Whabi Support Agent ---
whabi_support_agent = Agent(
    name="Whabi Support",
    role="Customer support for Whabi WhatsApp Business CRM",
    model=TOOL_MODEL,
    tools=_support_tools + (_automation_tools or []),  # type: ignore[operator]
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=_whabi_skills,
    instructions=[
        "You are the support agent for Whabi, a WhatsApp Business CRM.",
        "You respond in Spanish (Latin America neutral). Be professional but warm.",
        "",
        "## What you handle",
        "- Pricing and plan questions (starter, pro, enterprise)",
        "- How to set up WhatsApp Business API integration",
        "- Lead management: importing contacts, scoring, pipelines",
        "- Campaign creation: templates, scheduling, bulk messaging",
        "- Media handling: sending images, documents, voice messages",
        "- Payment confirmation: use confirm_payment tool (requires admin approval)",
        "- CRM integration with Twenty: contacts, companies, tasks",
        "",
        "## Lead Scoring (apply when someone asks about buying)",
        "- Score 1-3: just browsing, no specific need",
        "- Score 4-6: asked about features or pricing",
        "- Score 7-8: requested demo or pricing details",
        "- Score 9-10: ready to buy, asked for invoice/contract",
        "",
        "## Rules",
        "- ALWAYS log interactions using log_support_ticket after resolving",
        "- For payments: ALWAYS use confirm_payment (never confirm manually)",
        "- For complaints or disputes: use escalate_to_human",
        "- Never share internal system details (IPs, database names, API keys)",
        "- Business hours: 8am-8pm. Outside hours, acknowledge and promise follow-up",
        "- Use formal 'usted' on first contact, switch to 'tu' only if client does first",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    compression_manager=_compression,
)

# --- Docflow Support Agent ---
docflow_support_agent = Agent(
    name="Docflow Support",
    role="Customer support for Docflow Electronic Health Records system",
    model=TOOL_MODEL,
    tools=_support_tools,
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=_docflow_skills,
    instructions=[
        "You are the support agent for Docflow, an Electronic Health Records (EHR) system.",
        "You respond in Spanish (Latin America neutral). Be professional and precise.",
        "",
        "## What you handle",
        "- EHR system questions: how to upload, search, and manage documents",
        "- Document types: lab results, prescriptions, imaging, clinical notes",
        "- Compliance questions: retention periods, data handling, audit requirements",
        "- Appointment scheduling and management",
        "- User access and permissions",
        "- Payment and subscription queries: use confirm_payment tool",
        "",
        "## Compliance (CRITICAL)",
        "- NEVER share patient data in responses, even if the client mentions it",
        "- NEVER store patient identifiers in conversation logs",
        "- Refer compliance-specific legal questions to escalate_to_human",
        "- Retention periods: clinical notes 10yr, labs 7yr, imaging 10yr, Rx 5yr",
        "",
        "## Rules",
        "- ALWAYS log interactions using log_support_ticket after resolving",
        "- For payments: ALWAYS use confirm_payment",
        "- For legal/compliance disputes: ALWAYS use escalate_to_human",
        "- If a client shares patient data, remind them not to and do NOT repeat it",
        "- Be extra careful with PII -- the guardrails will catch most, but stay vigilant",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    compression_manager=_compression,
)

# --- Aurora Support Agent ---
aurora_support_agent = Agent(
    name="Aurora Support",
    role="Customer support for Aurora voice-first business PWA",
    model=TOOL_MODEL,
    tools=_support_tools,
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=_aurora_skills,
    instructions=[
        "You are the support agent for Aurora, a voice-first Progressive Web App.",
        "You respond in Spanish (Latin America neutral). Be friendly and clear.",
        "",
        "## What you handle",
        "- Voice commands: how to use them, troubleshooting recognition issues",
        "- PWA installation: how to install on iOS, Android, desktop",
        "- Subscription and billing: plans, upgrades, cancellations",
        "- Groq Whisper integration: language support, accuracy, settings",
        "- Task management: creating, listing, completing tasks via voice",
        "- Notes: taking, searching, and organizing voice notes",
        "- Payment confirmation: use confirm_payment tool",
        "",
        "## Common Troubleshooting",
        "- Voice not recognized: check microphone permissions, try quieter environment",
        "- PWA not installing: clear cache, use Chrome/Safari, check HTTPS",
        "- Slow transcription: check internet connection, Groq API status",
        "- Wrong language detected: set language explicitly in settings",
        "",
        "## Rules",
        "- ALWAYS log interactions using log_support_ticket after resolving",
        "- For payments: ALWAYS use confirm_payment",
        "- For account deletion requests: use escalate_to_human",
        "- Guide users step-by-step, don't assume technical knowledge",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    compression_manager=_compression,
)

# --- General Support Agent (fallback) ---
general_support_agent = Agent(
    name="General Support",
    role="General customer support and product comparison",
    model=TOOL_MODEL,
    tools=[escalate_to_human, log_support_ticket, WebSearchTools(fixed_max_results=3)],
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=_skills,
    instructions=[
        "You are the general support agent for AikaLabs.",
        "You respond in Spanish (Latin America neutral).",
        "",
        "## What you handle",
        "- General company questions (who we are, what we do)",
        "- Product comparison: help clients choose between Whabi, Docflow, Aurora",
        "- Pricing overview across all products",
        "- Partnership and integration inquiries",
        "- Messages that don't clearly belong to one product",
        "",
        "## Product Summary (for routing hints)",
        "- **Whabi**: WhatsApp Business CRM. Leads, campaigns, messaging.",
        "- **Docflow**: Electronic Health Records. Documents, compliance, clinical workflows.",
        "- **Aurora**: Voice-first PWA. Tasks, notes, business operations via voice.",
        "",
        "## Rules",
        "- If the client's question is clearly about one product, answer it yourself",
        "  but mention they can get specialized help by asking about that product",
        "- For complex product-specific questions, suggest they ask again mentioning",
        "  the product name so the specialized agent handles it",
        "- ALWAYS log interactions using log_support_ticket",
        "- For complaints, legal issues, or 'hablar con un humano': use escalate_to_human",
        "- Never make up pricing -- if unsure, say you'll confirm and follow up",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
)

# --- WhatsApp Support Team (routes to product-specific agents) ---
whatsapp_support_team = Team(
    name="WhatsApp Support",
    description=(
        "Customer support team for WhatsApp. Routes messages to the correct "
        "product agent (Whabi, Docflow, Aurora) or general support."
    ),
    members=[
        whabi_support_agent,
        docflow_support_agent,
        aurora_support_agent,
        general_support_agent,
    ],
    mode=TeamMode.route,
    model=GROQ_ROUTING_MODEL,
    pre_hooks=_guardrails,
    determine_input_for_members=False,
    instructions=[
        "You are the WhatsApp support router for AikaLabs.",
        "Route each message to the BEST agent based on content.",
        "",
        "## Routing rules (pick ONE agent):",
        "- WhatsApp, CRM, leads, campaigns, messaging, contacts: → Whabi Support",
        "- Health records, EHR, documents, patients, compliance, medical: → Docflow Support",
        "- Voice, PWA, app, transcription, Whisper, tasks, notes: → Aurora Support",
        "- General questions, company info, product comparison, unclear: → General Support",
        "",
        "## Signals to look for:",
        "- Product names mentioned explicitly (whabi, docflow, aurora)",
        "- Domain keywords (CRM, EHR, voice, PWA, leads, patients)",
        "- If the message mentions multiple products, route to General Support",
        "- If the message is a greeting with no context, route to General Support",
        "",
        "Do NOT add commentary. Return the agent's response directly.",
    ],
    db=db,
    learning=_learning,
    enable_session_summaries=False,
    add_history_to_context=True,
    num_history_runs=3,
    show_members_responses=True,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Social Media Autopilot (Workflow 4)
# ---------------------------------------------------------------------------
# Scheduled daily: trend research → parallel post generation for 3 platforms
# → audit loop → save to content queue.
# Uses ScheduleManager for cron-based daily execution.

_ig_post_agent = Agent(
    name="Instagram Post Writer",
    role="Write Instagram Reels captions and hashtags in Spanish",
    model=FAST_MODEL,
    instructions=[
        "You write Instagram Reels captions in Spanish (Latin America neutral).",
        "Format: hook (first line, punchy) + 2-3 lines of value + CTA + hashtags.",
        "Max 2200 chars. Use line breaks for readability.",
        "Include 20-30 relevant hashtags mixing popular and niche.",
        "Tone: professional but accessible. Never start with 'Hola'.",
    ],
    db=db,
    markdown=True,
)

_twitter_post_agent = Agent(
    name="Twitter Post Writer",
    role="Write Twitter/X threads in Spanish optimized for engagement",
    model=FAST_MODEL,
    instructions=[
        "You write Twitter/X posts in Spanish (Latin America neutral).",
        "Format: either a single tweet (max 280 chars) or a thread (3-5 tweets).",
        "First tweet must hook. Use numbers, bold claims, or questions.",
        "Thread format: 1/ hook → 2-3/ value → last/ CTA with link placeholder.",
        "No hashtags in threads (they reduce reach on X). Use them only in single tweets.",
    ],
    db=db,
    markdown=True,
)

_linkedin_post_agent = Agent(
    name="LinkedIn Post Writer",
    role="Write LinkedIn posts in Spanish for professional audience",
    model=FAST_MODEL,
    instructions=[
        "You write LinkedIn posts in Spanish (Latin America neutral).",
        "Format: hook line + empty line + 3-5 short paragraphs + CTA.",
        "Max 3000 chars. Use line breaks aggressively (1 idea per line).",
        "Tone: thought leadership, data-driven, personal experience angle.",
        "End with a question to drive comments.",
        "No hashtags in the body. Add 3-5 at the very end.",
    ],
    db=db,
    markdown=True,
)

_social_auditor = Agent(
    name="Social Media Auditor",
    role="Audit social media posts for quality and platform compliance",
    model=GROQ_ROUTING_MODEL,
    instructions=[
        "You audit social media posts for quality.",
        "",
        "## Check each post for:",
        "- Platform-specific format compliance (char limits, hashtag rules)",
        "- Hook strength (would you stop scrolling?)",
        "- Value density (does every sentence add something?)",
        "- CTA clarity (is the next action obvious?)",
        "- Brand consistency (professional, data-driven, Spanish)",
        "",
        "## Output format",
        "PLATFORM: [instagram/twitter/linkedin]",
        "SCORE: [1-10]",
        "VERDICT: [APPROVE or REVISE]",
        "ISSUES: [specific fixes if REVISE]",
    ],
    db=db,
    markdown=True,
)


def _check_social_approved(step_input: StepInput) -> StepOutput:
    """Check if the social media auditor approved all posts."""
    content = step_input.previous_step_content or ""
    is_approved = "APPROVE" in content.upper() and "REVISE" not in content.upper()
    return StepOutput(content=content, stop=is_approved)


social_media_workflow = Workflow(
    name="social-media-autopilot",
    description=(
        "Social media pipeline: trend research → parallel post generation "
        "(Instagram + Twitter + LinkedIn) → audit loop → content queue."
    ),
    db=SqliteDb(
        session_table="social_media_session",
        db_file="nexus.db",
    ),
    steps=[
        # Phase 1: Research trending topic
        Step(name="Trend Research", agent=trend_scout),
        # Phase 2: Generate posts for all 3 platforms in parallel
        Parallel(
            Step(name="Instagram Post", agent=_ig_post_agent),
            Step(name="Twitter Post", agent=_twitter_post_agent),
            Step(name="LinkedIn Post", agent=_linkedin_post_agent),
            name="Platform Posts",
        ),
        # Phase 3: Audit loop — auditor reviews, writers revise if needed
        Loop(
            steps=[
                Step(name="Social Audit", agent=_social_auditor),
                Step(name="Check Approval", executor=_check_social_approved),
            ],
            max_iterations=2,
            forward_iteration_output=True,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Competitor Intelligence (Workflow 5)
# ---------------------------------------------------------------------------
# Weekly Monday: 3 parallel scouts research competitors → synthesis report
# → save to knowledge base for future reference.

_competitor_content_scout = Agent(
    name="Competitor Content Scout",
    role="Track what competitors are publishing and posting",
    model=GROQ_ROUTING_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    retries=0,
    instructions=[
        "You track competitor content output.",
        "Search for recent blog posts, social media, product updates from competitors.",
        "Focus on: what topics they cover, what formats they use, engagement signals.",
        "",
        "## Output format",
        "COMPETITOR_CONTENT:",
        "- [competitor name]: [what they published] [URL]",
        "- [competitor name]: [what they published] [URL]",
        "TRENDS: [patterns across competitors]",
        "GAPS: [topics they're NOT covering that we could own]",
    ],
    db=db,
    markdown=True,
    compression_manager=_compression,
)

_competitor_pricing_scout = Agent(
    name="Competitor Pricing Scout",
    role="Track competitor pricing changes and offers",
    model=GROQ_ROUTING_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    retries=0,
    instructions=[
        "You track competitor pricing and offers.",
        "Search for pricing pages, plan changes, discounts, free tier updates.",
        "",
        "## Output format",
        "PRICING_CHANGES:",
        "- [competitor]: [change description] [source URL]",
        "CURRENT_PLANS: [summary table if found]",
        "OPPORTUNITIES: [where our pricing is more competitive]",
    ],
    db=db,
    markdown=True,
    compression_manager=_compression,
)

_competitor_reviews_scout = Agent(
    name="Competitor Reviews Scout",
    role="Find recent customer reviews and sentiment about competitors",
    model=GROQ_ROUTING_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    retries=0,
    instructions=[
        "You track competitor customer sentiment.",
        "Search for reviews on G2, Capterra, ProductHunt, Reddit, Twitter.",
        "",
        "## Output format",
        "REVIEWS:",
        "- [competitor]: [sentiment summary] [source URL]",
        "COMPLAINTS: [common pain points customers mention]",
        "PRAISE: [what customers love about competitors]",
        "OPPORTUNITY: [complaints we could solve better]",
    ],
    db=db,
    markdown=True,
    compression_manager=_compression,
)

_competitor_synthesizer = Agent(
    name="Competitor Intelligence Synthesizer",
    role="Produce weekly competitor intelligence reports",
    model=TOOL_MODEL,
    tools=[FileTools(base_dir=Path(__file__).parent / "knowledge")],
    instructions=[
        "You synthesize competitor intelligence into an actionable weekly report.",
        "",
        "## Report Structure",
        "1. Executive Summary (3 sentences: biggest threat, biggest opportunity, action item)",
        "2. Content Landscape (what competitors published, gaps we can exploit)",
        "3. Pricing & Positioning (changes, how we compare)",
        "4. Customer Sentiment (what customers love/hate about competitors)",
        "5. Recommended Actions (3 specific things to do this week)",
        "",
        "## Rules",
        "- Every claim needs a source URL",
        "- Write in Spanish",
        "- Save report as: knowledge/competitor-intel-<date>.md",
        "- Be analytical: what does this MEAN for us, not just what happened",
    ],
    db=db,
    learning=_learning,
    markdown=True,
    compression_manager=_compression,
)

competitor_intel_workflow = Workflow(
    name="competitor-intelligence",
    description=(
        "Weekly competitor intelligence: 3 parallel scouts (content, pricing, reviews) "
        "→ synthesis report → saved to knowledge base."
    ),
    db=SqliteDb(
        session_table="competitor_intel_session",
        db_file="nexus.db",
    ),
    steps=[
        # Phase 1: 3 scouts research in parallel
        Parallel(
            Step(name="Content Scout", agent=_competitor_content_scout, skip_on_failure=True),
            Step(name="Pricing Scout", agent=_competitor_pricing_scout, skip_on_failure=True),
            Step(name="Reviews Scout", agent=_competitor_reviews_scout, skip_on_failure=True),
            name="Competitor Research",
        ),
        # Phase 2: Synthesize into weekly report
        Step(name="Synthesize Report", agent=_competitor_synthesizer),
    ],
)

# ---------------------------------------------------------------------------
# Media Generation Pipeline (Workflow 6)
# ---------------------------------------------------------------------------
# Router-based: user requests media → routes to image or video generation
# → description/evaluation of the result.

_image_generator = Agent(
    name="Image Generator",
    role="Generate detailed image prompts and descriptions",
    model=FAST_MODEL,
    instructions=[
        "You are an image generation specialist.",
        "Given a topic or request, produce a detailed image generation prompt.",
        "",
        "## Output format",
        "PROMPT: [detailed prompt for image generation, 50-100 words]",
        "STYLE: [art style: photorealistic, illustration, 3D render, etc.]",
        "ASPECT_RATIO: [16:9, 1:1, 9:16, 4:3]",
        "MOOD: [emotional tone of the image]",
        "COLORS: [dominant color palette]",
        "",
        "## Rules",
        "- Be specific about composition, lighting, and subject placement",
        "- Include negative prompts (what to avoid)",
        "- Optimize for the target platform (Instagram = 1:1 or 9:16)",
    ],
    db=db,
    markdown=True,
)

_video_generator = Agent(
    name="Video Generator",
    role="Create video storyboards and production plans",
    model=FAST_MODEL,
    instructions=[
        "You are a video production specialist.",
        "Given a topic, create a detailed video production plan.",
        "",
        "## Output format",
        "CONCEPT: [1-sentence video concept]",
        "DURATION: [target duration in seconds]",
        "SCENES: [numbered list of scenes with visual + narration]",
        "TRANSITIONS: [transition types between scenes]",
        "MUSIC_MOOD: [background music style]",
        "PLATFORM: [optimized for: reels, tiktok, youtube_shorts]",
        "",
        "## Rules",
        "- Max 6 scenes for short-form (< 60s)",
        "- Each scene: visual description + narration text + duration",
        "- First scene must hook in 1-3 seconds",
    ],
    db=db,
    markdown=True,
)

_media_describer = Agent(
    name="Media Describer",
    role="Evaluate and describe generated media concepts",
    model=GROQ_ROUTING_MODEL,
    instructions=[
        "You evaluate media concepts (image prompts or video storyboards).",
        "Describe how the final result would look and feel.",
        "Rate the concept 1-10 for: visual impact, brand alignment, platform fit.",
        "Suggest one specific improvement.",
    ],
    db=db,
    markdown=True,
)


def _select_media_pipeline(step_input: StepInput) -> list:
    """Route to image or video pipeline based on input content."""
    raw_input = step_input.input
    content = str(raw_input).lower() if raw_input else ""
    if any(w in content for w in ["video", "reel", "tiktok", "clip", "motion"]):
        return [
            Step(name="Generate Video", agent=_video_generator),
            Step(name="Describe Video", agent=_media_describer),
        ]
    return [
        Step(name="Generate Image", agent=_image_generator),
        Step(name="Describe Image", agent=_media_describer),
    ]


_image_pipeline = Steps(
    name="image_pipeline",
    description="Image generation and evaluation",
    steps=[
        Step(name="Generate Image", agent=_image_generator),
        Step(name="Describe Image", agent=_media_describer),
    ],
)

_video_pipeline = Steps(
    name="video_pipeline",
    description="Video storyboard and evaluation",
    steps=[
        Step(name="Generate Video", agent=_video_generator),
        Step(name="Describe Video", agent=_media_describer),
    ],
)

media_generation_workflow = Workflow(
    name="media-generation",
    description=(
        "Media generation pipeline: routes to image or video generation "
        "based on input, then evaluates the result."
    ),
    db=SqliteDb(
        session_table="media_generation_session",
        db_file="nexus.db",
    ),
    steps=[
        Router(
            name="Media Type Router",
            description="Routes to image or video pipeline based on request",
            selector=_select_media_pipeline,
            choices=[_image_pipeline, _video_pipeline],
        ),
    ],
)

# ---------------------------------------------------------------------------
# Scheduled Tasks (ScheduleManager)
# ---------------------------------------------------------------------------
# Programmatic schedule creation for automated workflows.
# Schedules are persisted in SQLite and polled by the AgentOS scheduler.

from agno.scheduler import ScheduleManager

_schedule_mgr = ScheduleManager(db)

# Daily social media autopilot (10am weekdays, America/Bogota)
_schedule_mgr.create(
    name="daily-social-media",
    cron="0 10 * * 1-5",
    endpoint="/workflows/social-media-autopilot/runs",
    payload={"message": "Create today's social media posts about the latest AI trend"},
    description="Daily social media content generation for all platforms",
    timezone="America/Bogota",
    if_exists="update",
)

# Weekly competitor intelligence (Monday 9am, America/Bogota)
_schedule_mgr.create(
    name="weekly-competitor-intel",
    cron="0 9 * * 1",
    endpoint="/workflows/competitor-intelligence/runs",
    payload={"message": "Generate weekly competitor intelligence report for Whabi, Docflow, Aurora competitors"},
    description="Weekly competitor analysis across content, pricing, and reviews",
    timezone="America/Bogota",
    if_exists="update",
)

# Daily research briefing (8am weekdays, America/Bogota)
_schedule_mgr.create(
    name="daily-research-briefing",
    cron="0 8 * * 1-5",
    endpoint="/agents/Research Agent/runs",
    payload={"message": "Find today's top AI trend relevant to WhatsApp CRM, EHR, and voice-first apps"},
    description="Morning AI trend briefing",
    timezone="America/Bogota",
    if_exists="update",
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
# Multi-Channel Gateway (WhatsApp + Slack + Telegram)
# ---------------------------------------------------------------------------
# All channels point to Cerebro for intelligent routing. Each channel
# maintains its own session history but shares knowledge and learnings.
#
# WhatsApp: WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_VERIFY_TOKEN
# Slack:    SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET (+ pip install slack-sdk)
# Telegram: TELEGRAM_BOT_TOKEN (+ pip install 'agno[telegram]')

_interfaces: list = []

# --- WhatsApp ---
if os.getenv("WHATSAPP_ACCESS_TOKEN"):
    _interfaces.append(
        Whatsapp(
            team=whatsapp_support_team,  # Product-specific routing (Whabi/Docflow/Aurora)
            phone_number_id=os.getenv("WHATSAPP_PHONE_ID"),
            access_token=os.getenv("WHATSAPP_ACCESS_TOKEN"),
            verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN", "nexus-verify"),
            send_user_number_to_context=True,  # Include sender info for CRM lookup
        )
    )

# --- Slack ---
if os.getenv("SLACK_BOT_TOKEN"):
    try:
        from agno.os.interfaces.slack import Slack

        _interfaces.append(
            Slack(
                agent=research_agent,
                team=cerebro,
            )
        )
    except ImportError:
        pass  # slack-sdk not installed

# --- Telegram ---
if os.getenv("TELEGRAM_BOT_TOKEN"):
    try:
        from agno.os.interfaces.telegram import Telegram

        _interfaces.append(
            Telegram(
                agent=research_agent,
                team=cerebro,
            )
        )
    except ImportError:
        pass  # pyTelegramBotAPI not installed

# ---------------------------------------------------------------------------
# AgentOS
# ---------------------------------------------------------------------------
# Scheduler: already enabled (scheduler=True). Schedules are managed at
# runtime via the AgentOS REST API, not in code. Examples:
#
#   # Create a daily research task (8am weekdays, America/Bogota):
#   POST http://localhost:7777/v1/schedules
#   {
#     "name": "daily-research",
#     "cron_expr": "0 8 * * 1-5",
#     "endpoint": "/v1/agents/Research Agent/runs",
#     "method": "POST",
#     "payload": {"message": "Find today's top AI trend for content"},
#     "timezone": "America/Bogota"
#   }
#
#   # Create a weekly content review:
#   POST http://localhost:7777/v1/schedules
#   {
#     "name": "weekly-content-review",
#     "cron_expr": "0 9 * * 1",
#     "endpoint": "/v1/agents/Analytics Agent/runs",
#     "method": "POST",
#     "payload": {"message": "Generate weekly content performance report"},
#     "timezone": "America/Bogota"
#   }
#
# Manage schedules: GET/PATCH/DELETE /v1/schedules/{schedule_id}

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
        code_review_agent,
        whabi_support_agent,
        docflow_support_agent,
        aurora_support_agent,
        general_support_agent,
    ],
    teams=[cerebro, content_team, whatsapp_support_team],
    workflows=[
        client_research_workflow,
        content_production_workflow,
        deep_research_workflow,
        seo_content_workflow,
        social_media_workflow,
        competitor_intel_workflow,
        media_generation_workflow,
    ],
    knowledge=[knowledge_base],
    registry=registry,
    interfaces=_interfaces or None,
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
