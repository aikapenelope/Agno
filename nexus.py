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
        export DIRECTUS_TOKEN="your-directus-token"
        export DIRECTUS_URL="http://localhost:8055"

    MCP servers (requires Docker running with n8n and Directus):
        - n8n workflow builder: creates and manages n8n workflows
        - Directus CRM: manages contacts, companies, tasks, conversations

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
try:
    from agno.os.interfaces.agui import AGUI

    _agui_available = True
except ImportError:
    _agui_available = False
from agno.os.interfaces.whatsapp.whatsapp import Whatsapp
from agno.tools.decorator import tool
from agno.db.sqlite import SqliteDb
from agno.eval.base import BaseEval
from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail
from agno.learn.machine import LearningMachine
from agno.learn import (
    DecisionLogConfig,
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
from agno.tools.sql import SQLTools
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
# Hybrid strategy: MiniMax (subscription, unlimited) for most agents.
# OpenAI via OpenRouter (pay-per-token) only for features MiniMax can't do.
#
# MiniMax works for: tool calling, skills, learning, compression
# MiniMax fails for: output_schema, reasoning=True, json_object response_format

_openrouter_kwargs = {
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "base_url": "https://openrouter.ai/api/v1",
}

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
    "supports_native_structured_outputs": False,
    "supports_json_schema_outputs": False,
}

# --- MiniMax (subscription, use for everything that works) ---
TOOL_MODEL = OpenAIChat(id="MiniMax-M2.7", **_minimax_kwargs)
FAST_MODEL = OpenAIChat(id="MiniMax-M2.7", **_minimax_kwargs)

# --- OpenAI via OpenRouter (pay-per-token, only for incompatible features) ---
# Used by: knowledge_agent (reasoning), code_review_agent (reasoning),
#          _synthesis_agent (output_schema), followups (json_object),
#          LearningMachine user_memory (json_object internally)
REASONING_MODEL = OpenAIChat(id="openai/gpt-5-mini", **_openrouter_kwargs)

# Followup model: needs json_object support (MiniMax can't do this)
FOLLOWUP_MODEL = OpenAIChat(id="openai/gpt-5-nano", **_openrouter_kwargs)

# Learning model: user_memory needs json_object internally
LEARNING_MODEL = OpenAIChat(id="openai/gpt-4o-mini", **_openrouter_kwargs)

# --- Groq Models (free, for routing and background tasks) ---
GROQ_FAST_MODEL = Groq(id="llama-3.1-8b-instant")
GROQ_ROUTING_MODEL = Groq(id="openai/gpt-oss-20b")

# --- Learning Machine ---
# Full learning system: profile, memory, entities, and accumulated knowledge.
# Uses TOOL_MODEL (MiniMax M2.7) for extraction -- EntityMemory needs reliable
# tool calling (create_entity, add_fact, add_event) which Groq cannot provide.
# All data stored in SQLite (nexus.db) + LanceDB (lancedb/) locally on Mac.

# Minimal learning: only learned_knowledge (patterns, solutions).
# Used by: research agents, content agents, scouts — stateless agents that
# benefit from remembering patterns but don't need to track user profiles.
# Matches Agno's official Pal/Dash pattern (cookbook/01_demo).
_learning = LearningMachine(
    model=TOOL_MODEL,  # MiniMax works for AGENTIC mode (tool calling)
    knowledge=learnings_knowledge,
    learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
)

# Full learning: profile + memory + entities + knowledge + decision log.
# Used by: support agents, Pal, Onboarding — agents that need to remember
# user preferences, track entities (clients, products), and audit decisions.
# Matches Agno's support_agent pattern (cookbook/08_learning/07_patterns).
_learning_full = LearningMachine(
    model=TOOL_MODEL,  # MiniMax works for AGENTIC mode (tool calling)
    knowledge=learnings_knowledge,
    user_profile=UserProfileConfig(mode=LearningMode.AGENTIC),
    user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
    entity_memory=EntityMemoryConfig(mode=LearningMode.AGENTIC),
    learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    decision_log=DecisionLogConfig(mode=LearningMode.AGENTIC),
)

# --- Context Compression ---
# Compresses long tool results to save tokens in agents with heavy tool usage.
# Uses FAST_MODEL (MiniMax M2.7-hs, 100 tps) for fast compression.
_compression = CompressionManager(
    model=FAST_MODEL,
    compress_tool_results=True,
)

# ---------------------------------------------------------------------------
# Guardrails (applied to all agents and teams)
# ---------------------------------------------------------------------------
# PII detection blocks SSNs, credit cards, emails, phone numbers in input.
# Prompt injection blocks jailbreak attempts and instruction overrides.

_guardrails = [
    PIIDetectionGuardrail(
        mask_pii=True,           # Mask instead of blocking (fewer false positives)
        enable_phone_check=False, # Too many false positives (any 10-digit number triggers)
    ),
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
    id="research-agent",
    role="Search the web for current information and data",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=5)],
    tool_call_limit=5,
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
    followup_model=FOLLOWUP_MODEL,
    compression_manager=_compression,
)

# ---------------------------------------------------------------------------
# Knowledge Agent
# ---------------------------------------------------------------------------

knowledge_agent = Agent(
    name="Knowledge Agent",
    id="knowledge-agent",
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
    followup_model=FOLLOWUP_MODEL,
)

# ---------------------------------------------------------------------------
# MCP Servers (conditionally loaded based on env vars)
# ---------------------------------------------------------------------------

import requests as _requests

_DIRECTUS_URL = os.getenv("DIRECTUS_URL", "http://localhost:8055")
_DIRECTUS_TOKEN = os.getenv("DIRECTUS_TOKEN", "")
_DIRECTUS_HEADERS = {
    "Authorization": f"Bearer {_DIRECTUS_TOKEN}",
    "Content-Type": "application/json",
}


def _directus_create(collection: str, data: dict) -> dict:
    """Create a record in Directus. Returns the response or error."""
    if not _DIRECTUS_TOKEN:
        return {"error": "DIRECTUS_TOKEN not configured"}
    try:
        resp = _requests.post(
            f"{_DIRECTUS_URL}/items/{collection}",
            json=data,
            headers=_DIRECTUS_HEADERS,
            timeout=10,
        )
        if resp.ok:
            return resp.json()
        return {"error": f"Directus {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"error": f"Directus connection failed: {e}"}


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
    After approval, the payment is logged in Directus CRM.
    """
    result = _directus_create("payments", {
        "amount": float(amount) if amount.replace(".", "").isdigit() else 0,
        "method": method,
        "reference": reference,
        "status": "approved",
        "approved_by": "nexus-agent",
        "product": product,
    })

    _directus_create("tasks", {
        "title": f"Seguimiento pago: {client_name} ({product})",
        "body": f"Pago de {amount} via {method}. Ref: {reference}. Verificar acreditacion.",
        "status": "TODO",
    })

    if "error" in result:
        return f"PAYMENT_APPROVED (CRM error: {result['error']}): {client_name} {amount} {method}"

    return (
        f"PAYMENT_CONFIRMED_AND_LOGGED: product={product} client={client_name} "
        f"amount={amount} method={method} ref={reference} — Registrado en Directus"
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
    Creates a ticket in Directus CRM.
    """
    result = _directus_create("tickets", {
        "product": product,
        "intent": intent,
        "summary": summary,
        "resolution": resolution,
        "urgency": urgency,
        "status": "resolved" if resolution else "open",
    })

    if urgency == "high" or lead_score >= 7:
        _directus_create("tasks", {
            "title": f"Follow-up: {product} - {intent} (score: {lead_score})",
            "body": f"Urgencia: {urgency}. {summary[:200]}",
            "status": "todo",
        })

    if "error" in result:
        return f"TICKET_LOGGED (CRM error: {result['error']}): {product} {intent}"

    return (
        f"TICKET_LOGGED: product={product} intent={intent} urgency={urgency} "
        f"lead_score={lead_score} — Registrado en Directus"
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
    Creates an urgent task in Directus for the support team.
    """
    result = _directus_create("tasks", {
        "title": f"ESCALACION: {product} - {client_name}",
        "body": (
            f"Producto: {product}\n"
            f"Cliente: {client_name}\n"
            f"Urgencia: {urgency}\n"
            f"Razon: {reason}\n"
            f"Estado: REQUIERE ATENCION HUMANA"
        ),
        "status": "todo",
    })

    _directus_create("events", {
        "type": "escalation",
        "payload": {"product": product, "client": client_name, "reason": reason, "urgency": urgency},
    })

    if "error" in result:
        return f"ESCALATED (CRM error: {result['error']}): {product} {client_name} {reason}"

    return (
        f"ESCALATED_AND_LOGGED: product={product} client={client_name} urgency={urgency} "
        f"reason={reason} — Tarea creada en Directus para atencion humana"
    )


@tool()
def save_contact(
    first_name: str,
    last_name: str = "",
    email: str = "",
    phone: str = "",
    job_title: str = "",
    city: str = "",
    company_name: str = "",
    lead_score: int = 0,
    product: str = "",
    notes: str = "",
) -> str:
    """Save or update a contact in Directus CRM.

    ALWAYS call this when you learn a client's name, email, phone, or company.
    Call it at the START of a conversation if the client identifies themselves,
    and again at the END if you learned new information during the conversation.
    """
    person_data: dict = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
    }
    if job_title:
        person_data["job_title"] = job_title
    if city:
        person_data["city"] = city
    if product:
        person_data["product"] = product
    if lead_score > 0:
        person_data["lead_score"] = lead_score
    if company_name:
        person_data["notes"] = f"Empresa: {company_name}"
    person_data["source"] = "whatsapp"
    person_data["status"] = "lead"

    result = _directus_create("contacts", person_data)

    if notes:
        _directus_create("events", {
            "type": "contact_note",
            "payload": {"name": f"{first_name} {last_name}", "product": product, "lead_score": lead_score, "notes": notes},
        })

    if "error" in result:
        return f"CONTACT_SAVED (CRM error: {result['error']}): {first_name} {last_name}"

    return (
        f"CONTACT_SAVED: {first_name} {last_name}"
        f"{f' ({email})' if email else ''}"
        f"{f' tel:{phone}' if phone else ''}"
        f"{f' empresa:{company_name}' if company_name else ''}"
        f" — Registrado en Directus"
    )


@tool()
def save_company(
    name: str,
    domain: str = "",
    employees: int = 0,
    industry: str = "",
    address: str = "",
    notes: str = "",
) -> str:
    """Save a company in Directus CRM.

    Call this when a client mentions their company name, especially if they
    are a potential B2B client. Include domain and industry if mentioned.
    """
    company_data: dict = {"name": name}
    if domain:
        company_data["domainName"] = domain
    if employees > 0:
        company_data["employees"] = employees
    if address:
        company_data["address"] = address

    result = _directus_create("companies", company_data)

    if notes or industry:
        _directus_create("events", {
            "type": "company_note",
            "payload": {"company": name, "industry": industry, "notes": notes},
        })

    if "error" in result:
        return f"COMPANY_SAVED (CRM error: {result['error']}): {name}"

    return f"COMPANY_SAVED: {name}{f' ({domain})' if domain else ''} — Registrado en Directus"


@tool()
def log_conversation(
    client_name: str,
    product: str,
    channel: str = "whatsapp",
    summary: str = "",
    intent: str = "",
    sentiment: str = "neutral",
    lead_score: int = 0,
    next_action: str = "",
) -> str:
    """Log a complete conversation summary in Directus CRM.

    ALWAYS call this at the END of every conversation. Include:
    - What the client asked about (intent)
    - How the conversation went (sentiment: positive/neutral/negative)
    - What to do next (next_action)
    - Lead score if applicable
    """
    result = _directus_create("conversations", {
        "channel": channel,
        "direction": "inbound",
        "raw_message": summary,
        "agent_response": next_action or "",
        "intent": intent,
        "sentiment": sentiment,
        "lead_score": lead_score,
        "agent_name": "nexus-support",
    })

    if next_action:
        _directus_create("tasks", {
            "title": f"Seguimiento: {client_name} ({product})",
            "body": f"Accion: {next_action}\nContexto: {summary[:200]}",
            "status": "todo",
        })

    if "error" in result:
        return f"CONVERSATION_LOGGED (CRM error: {result['error']}): {client_name}"

    return (
        f"CONVERSATION_LOGGED: {client_name} ({product}) via {channel} "
        f"intent={intent} sentiment={sentiment} score={lead_score} — Registrado en Directus"
    )
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

# Directus CRM: direct REST API tools + official MCP server.
# Direct tools (save_contact, etc.) use _directus_create() for fast writes.
# MCP server (@directus/content-mcp) gives agents full read/query access.
_automation_tools.extend([save_contact, save_company, log_conversation, log_support_ticket])

if os.getenv("DIRECTUS_TOKEN"):
    _automation_tools.append(
        MCPTools(
            command="npx @directus/content-mcp@latest",
            env={
                "DIRECTUS_URL": os.getenv("DIRECTUS_URL", "http://localhost:8055"),
                "DIRECTUS_TOKEN": os.getenv("DIRECTUS_TOKEN", ""),
            },
            include_tools=[
                "read-items",
                "create-item",
                "update-item",
                "read-collections",
                "read-fields",
                "read-flows",
                "trigger-flow",
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
    id="automation-agent",
    role="Execute workflows, manage CRM, and run automations",
    model=TOOL_MODEL,  # Needs reliable tool calling for MCP
    tools=_automation_tools or None,  # type: ignore[arg-type]
    tool_call_limit=5,
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=_skills,
    instructions=[
        "You are an automation specialist with access to n8n, Directus CRM, and Obsidian.",
        "IMPORTANT: Always USE your tools to execute actions. NEVER just explain how to do something.",
        "When asked to do something, DO IT using your tools. Do not describe steps.",
        "",
        "## n8n (workflow automation)",
        "- List, create, execute, activate, and deactivate n8n workflows.",
        "- When asked to automate something, check if a workflow already exists first.",
        "",
        "## Directus CRM (direct REST API)",
        "- save_contact(first_name, last_name, email, phone, job_title, city, company_name, lead_score, product, notes)",
        "- save_company(name, domain, employees, industry, address, notes)",
        "- log_conversation(client_name, product, channel, summary, intent, sentiment, lead_score, next_action)",
        "- log_support_ticket(product, intent, summary, resolution, urgency, lead_score)",
        "- All data goes directly to Directus CRM REST API",
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
    followup_model=FOLLOWUP_MODEL,
    compression_manager=_compression,
)

# ---------------------------------------------------------------------------
# Cerebro Team
# ---------------------------------------------------------------------------

cerebro = Team(
    id="cerebro",
    name="Cerebro",
    description="Multi-agent analysis system that decomposes complex tasks",
    members=[research_agent, knowledge_agent, automation_agent],
    mode=TeamMode.route,
    respond_directly=True,
    tool_call_limit=1,
    model=TOOL_MODEL,  # MiniMax for precise routing
    knowledge=knowledge_base,
    # pre_hooks on individual agents, not team leader
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
    # No learning on team leader (routes only, members have their own learning)
    enable_session_summaries=False,
    add_history_to_context=False,
    show_members_responses=False,
    add_datetime_to_context=False,
    markdown=True,
    followups=True,
    num_followups=3,
    followup_model=FOLLOWUP_MODEL,
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
    id="trend-scout",
    role="Research AI/tech trends and produce content briefs",
    model=TOOL_MODEL,
    tools=[
        DuckDuckGoTools(),
        WebSearchTools(fixed_max_results=3),
    ],
    tool_call_limit=5,
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
# CRM logging and escalation create real records in Directus CRM.
# Directus REST API: http://localhost:8055/items/



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
    id="scriptwriter",
    role="Write video scripts and storyboards for short-form content",
    model=FAST_MODEL,
    tools=[save_video_file, _video_file_tools],
    tool_call_limit=5,
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
    id="creative-director",
    role="Evaluate video storyboards and describe how they will look visually",
    model=FAST_MODEL,
    tools=[FileTools(base_dir=Path.home() / "nexus-videos", enable_save_file=False)],
    tool_call_limit=5,
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
    id="analytics-agent",
    role="Analyze content performance and generate optimization reports",
    model=TOOL_MODEL,
    tools=[
        WebSearchTools(fixed_max_results=5),
        CalculatorTools(),
        FileTools(),
    ],
    tool_call_limit=5,
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
    id="content-factory",
    name="Content Factory",
    description="Video content production team for Instagram Reels and TikTok",
    mode=TeamMode.route,
    respond_directly=True,
    tool_call_limit=1,
    members=[trend_scout, scriptwriter, analytics_agent],
    model=TOOL_MODEL,  # MiniMax for precise routing
    # pre_hooks on individual agents, not team leader
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
    # No learning on team leader (routes only, members have their own learning)
    enable_session_summaries=False,
    add_history_to_context=False,
    show_members_responses=False,
    add_datetime_to_context=False,
    markdown=True,
    followups=True,
    num_followups=3,
    followup_model=FOLLOWUP_MODEL,
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
# Deep Research System v6
# ---------------------------------------------------------------------------
# Pattern: Smart Planner → Parallel(N specialized scouts) → Quality Gate → Synthesizer
#
# v6: Multiple search providers. Each scout uses a different search backend.
# Scouts are created conditionally based on available API keys.
# The planner knows which scouts are available and assigns work accordingly.
# Minimum: WebSearchTools (always available, free).
# Premium: TavilyTools, ExaTools, FirecrawlTools, SpiderTools (need API keys).

# --- Search scouts: one per provider, created conditionally ---

_research_scouts: list = []

# Scout 1: Tavily (best for news, articles, general AI-optimized search)
if os.getenv("TAVILY_API_KEY"):
    _tavily_scout = Agent(
        name="Tavily Scout",
        role="AI-optimized web search for news, articles, and current information",
        model=TOOL_MODEL,
        tools=[TavilyTools()],
        tool_call_limit=3,
        retries=1,
        skills=_deep_search_skills,
        instructions=[
            "You are a research agent using Tavily (AI-optimized search).",
            "The Research Planner has given you a plan. Follow it.",
            "",
            "## Your strength: Tavily returns clean, AI-ready snippets.",
            "- Best for: news articles, blog posts, recent announcements, tech coverage",
            "- Tavily automatically extracts relevant content from pages",
            "- Use the planner's query and site filters",
            "",
            "## Process",
            "1. Execute the planner's query via tavily_search",
            "2. If results are thin, do ONE follow-up with a refined query",
            "3. Extract findings with source URLs",
            "",
            "## Output format",
            "FINDINGS:",
            "- **[Key fact]** ([Source](URL)) — [Why this matters]",
            "",
            "GAPS: [What you couldn't find]",
        ],
        db=db,
        markdown=True,
        compression_manager=_compression,
    )
    _research_scouts.append(("Tavily Search", _tavily_scout))

# Scout 2: Exa (best for semantic search, finding similar content, research papers)
if os.getenv("EXA_API_KEY"):
    _exa_scout = Agent(
        name="Exa Scout",
        role="Semantic search for research papers, similar content, and deep web results",
        model=TOOL_MODEL,
        tools=[ExaTools()],
        tool_call_limit=3,
        retries=1,
        skills=_deep_search_skills,
        instructions=[
            "You are a research agent using Exa (semantic/neural search).",
            "The Research Planner has given you a plan. Follow it.",
            "",
            "## Your strength: Exa finds content by MEANING, not just keywords.",
            "- Best for: research papers, technical docs, finding similar content",
            "- Exa excels at finding niche content that keyword search misses",
            "- Use the planner's query but phrase it as a natural question",
            "",
            "## Process",
            "1. Execute the planner's query via exa_search",
            "2. If results are thin, try rephrasing as a question",
            "3. Extract findings with source URLs",
            "",
            "## Output format",
            "FINDINGS:",
            "- **[Key fact]** ([Source](URL)) — [Why this matters]",
            "",
            "GAPS: [What you couldn't find]",
        ],
        db=db,
        markdown=True,
        compression_manager=_compression,
    )
    _research_scouts.append(("Exa Search", _exa_scout))

# Scout 3: Firecrawl (best for extracting full page content, structured data)
if os.getenv("FIRECRAWL_API_KEY"):
    _firecrawl_scout = Agent(
        name="Firecrawl Scout",
        role="Deep page extraction for detailed content, documentation, and structured data",
        model=TOOL_MODEL,
        tools=[FirecrawlTools()],
        tool_call_limit=3,
        retries=1,
        skills=_deep_search_skills,
        instructions=[
            "You are a research agent using Firecrawl (deep page extraction).",
            "The Research Planner has given you a plan. Follow it.",
            "",
            "## Your strength: Firecrawl extracts FULL page content, not just snippets.",
            "- Best for: documentation pages, GitHub READMEs, detailed articles",
            "- Use when you need the complete content of a specific URL",
            "- The planner may give you specific URLs to scrape",
            "",
            "## Process",
            "1. If the planner gave specific URLs, scrape those directly",
            "2. Otherwise, search and then scrape the most relevant result",
            "3. Extract detailed findings from the full content",
            "",
            "## Output format",
            "FINDINGS:",
            "- **[Key fact]** ([Source](URL)) — [Why this matters]",
            "",
            "GAPS: [What you couldn't find]",
        ],
        db=db,
        markdown=True,
        compression_manager=_compression,
    )
    _research_scouts.append(("Firecrawl Search", _firecrawl_scout))

# Scout 4: Spider (best for crawling entire sites, sitemaps, bulk extraction)
_spider_scout = Agent(
    name="Spider Scout",
    role="Web crawling for site-wide content, sitemaps, and bulk data extraction",
    model=TOOL_MODEL,
    tools=[SpiderTools()],
    tool_call_limit=3,
    retries=1,
    skills=_deep_search_skills,
    instructions=[
        "You are a research agent using Spider (web crawler).",
        "The Research Planner has given you a plan. Follow it.",
        "",
        "## Your strength: Spider crawls sites and extracts structured content.",
        "- Best for: crawling GitHub repos, documentation sites, company blogs",
        "- Use when you need to explore multiple pages from one domain",
        "- Good for finding all pages related to a topic on a specific site",
        "",
        "## Process",
        "1. Use the planner's target site/URL to crawl",
        "2. Extract relevant content from crawled pages",
        "3. Summarize findings with source URLs",
        "",
        "## Output format",
        "FINDINGS:",
        "- **[Key fact]** ([Source](URL)) — [Why this matters]",
        "",
        "GAPS: [What you couldn't find]",
    ],
    db=db,
    markdown=True,
    compression_manager=_compression,
)
_research_scouts.append(("Spider Search", _spider_scout))

# Scout 5: WebSearch (always available, free fallback)
_websearch_scout = Agent(
    name="WebSearch Scout",
    role="General web search using DuckDuckGo as free fallback",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=8)],
    tool_call_limit=3,
    retries=1,
    skills=_deep_search_skills,
    instructions=[
        "You are a research agent using general web search.",
        "The Research Planner has given you a plan. Follow it.",
        "",
        "## Your strength: Free, always available, good for general queries.",
        "- Best for: general web results, community forums, broad coverage",
        "- Use the planner's query with site: filters for precision",
        "",
        "## Process",
        "1. Execute the planner's query via web_search",
        "2. If results are thin, do ONE follow-up with refined keywords",
        "3. Extract findings with source URLs",
        "",
        "## Output format",
        "FINDINGS:",
        "- **[Key fact]** ([Source](URL)) — [Why this matters]",
        "",
        "GAPS: [What you couldn't find]",
    ],
    db=db,
    markdown=True,
    compression_manager=_compression,
)
_research_scouts.append(("WebSearch", _websearch_scout))

# --- Build the list of available scout names for the planner ---
_available_scout_names = [name for name, _ in _research_scouts]

# --- Planner: generates a full research execution plan ---
# The planner knows which scouts are available and assigns work to each.
_research_planner = Agent(
    name="Research Planner",
    role="Create a detailed research execution plan assigning work to available search agents",
    model=TOOL_MODEL,
    instructions=[
        "You are a research strategist. Given a topic, create a DETAILED execution plan",
        f"for {len(_research_scouts)} parallel research agents.",
        "",
        f"## Available agents: {', '.join(_available_scout_names)}",
        "",
        "## Agent capabilities:",
        "- **Tavily Scout**: AI-optimized search. Best for news, articles, blogs, announcements.",
        "- **Exa Scout**: Semantic/neural search. Best for research papers, similar content, niche topics.",
        "- **Firecrawl Scout**: Full page extraction. Best for scraping specific URLs, docs, READMEs.",
        "- **Spider Scout**: Web crawler. Best for crawling GitHub repos, documentation sites.",
        "- **WebSearch Scout**: General search (DuckDuckGo). Free fallback for broad queries.",
        "",
        "## For EACH available agent, provide a section:",
        "AGENT_[NAME]:",
        "  QUERY: [compound search query with keywords and site: filters]",
        "  STRATEGY: [what this agent should focus on given its strengths]",
        "  EXTRACT: [specific data points to look for]",
        "",
        "## Rules",
        "- Assign DIFFERENT angles to each agent. No overlap.",
        "- Queries must be COMPOUND: multiple relevant keywords in one query",
        "- Always include year (2025 or 2026) in queries for freshness",
        "- For Latam topics, include both English and Spanish queries",
        "- site: filters are critical for quality",
        "- If only WebSearch is available, split the topic into 1 broad query",
        "",
        "## Output format",
        "TOPIC_ANALYSIS: [1 sentence: what is this topic and why it matters]",
        "LANGUAGE_STRATEGY: [primary search language and why]",
        "",
        "Then one section per available agent with QUERY, STRATEGY, EXTRACT.",
    ],
    db=db,
    markdown=True,
)

# --- Quality gate: stop early if research is too thin ---
def _quality_gate(step_input: StepInput) -> StepOutput:
    """Check that the analysis has enough substance to proceed."""
    content = str(step_input.previous_step_content or "")
    if len(content) < 200:
        return StepOutput(
            content="Quality gate failed: research too thin. Insufficient data to produce a report.",
            stop=True,
            success=False,
        )
    return StepOutput(content=content, success=True)

# --- Synthesizer: produces the final research report as readable markdown ---
# NOTE: No output_schema. MiniMax doesn't support native structured outputs,
# and forcing JSON mode produces {"executive_summary": "..."} instead of a
# readable report. The skills teach the agent the correct report structure.
_research_synthesizer = Agent(
    name="Research Synthesizer",
    role="Produce comprehensive research reports from collected findings",
    model=TOOL_MODEL,
    tools=[FileTools(base_dir=Path(__file__).parent / "knowledge")],
    tool_call_limit=5,
    skills=_deep_synthesis_skills,
    instructions=[
        "You synthesize research findings into a comprehensive markdown report.",
        "",
        "## Process",
        "1. Read ALL findings from the research scouts",
        "2. Organize by theme, not by source",
        "3. Produce a well-structured markdown report with:",
        "",
        "## Report Structure (follow exactly)",
        "### Executive Summary",
        "2-3 sentences. The key takeaway with the most important number.",
        "",
        "### Key Findings",
        "5-8 bullet points. Each with a specific fact, source URL, and analysis.",
        "Format: **[Finding]** ([Source](URL)) — [What it means]",
        "",
        "### Analysis",
        "2-3 paragraphs connecting findings into a narrative.",
        "What patterns emerge? What contradictions? What's the 'so what'?",
        "",
        "### Gaps and Uncertainties",
        "What data was unavailable? What claims have only one source?",
        "",
        "### Recommendations",
        "3-5 specific, actionable next steps tied to findings.",
        "",
        "### Sources",
        "All URLs cited, deduplicated.",
        "",
        "## Rules",
        "- Write in markdown, NOT JSON. The user reads this directly.",
        "- Every finding must have a source URL. No unsourced claims.",
        "- If data conflicts between sources, note the conflict.",
        "- Write in Spanish if the topic is Latam-specific, English otherwise.",
        "- Be analytical: say what it MEANS, not just what it IS.",
        "- Save the report using save_file: research-<topic-slug>-<date>.md",
    ],
    db=db,
    learning=_learning,
    markdown=True,
    compression_manager=_compression,
)

deep_research_workflow = Workflow(
    name="deep-research",
    description=(
        "Production deep research v6: smart planner → N specialized scouts "
        f"({', '.join(_available_scout_names)}) in parallel → quality gate → markdown report."
    ),
    db=SqliteDb(
        session_table="deep_research_session",
        db_file="nexus.db",
    ),
    steps=[
        # Phase 1: Planner creates execution plan for available scouts
        Step(name="Plan", agent=_research_planner),
        # Phase 2: All available scouts search in parallel
        Parallel(
            *[Step(name=name, agent=agent, skip_on_failure=True) for name, agent in _research_scouts],
            name="Parallel Research",
        ),
        # Phase 3: Quality gate — stop early if research is too thin
        Step(name="Quality Gate", executor=_quality_gate),
        # Phase 4: Synthesize into readable markdown report + save to knowledge/
        Step(name="Final Report", agent=_research_synthesizer),
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
    model=TOOL_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    tool_call_limit=5,
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
    tool_call_limit=5,
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
    model=TOOL_MODEL,
    tools=[FileTools(base_dir=Path(__file__).parent, enable_save_file=False)],
    tool_call_limit=5,
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
    id="code-review-agent",
    role="Review, write, and iterate on code with self-learning",
    model=TOOL_MODEL,
    tools=[
        CodingTools(base_dir=str(_code_workspace)),
        ReasoningTools(),
    ],
    tool_call_limit=5,
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
# Dash — Data Analytics Agent
# ---------------------------------------------------------------------------
# Queries Directus CRM for Whabi/Docflow/Aurora data and produces insights.
# Learns query patterns, metric definitions, and business rules over time.
# NOTE: Uses Directus REST API for CRM data access.

_dash_tools: list = [
    CalculatorTools(),
    PythonTools(),
]
if _automation_tools:
    _dash_tools.extend(_automation_tools)  # Directus CRM + n8n MCP

dash = Agent(
    name="Dash",
    id="dash",
    role="Data analytics agent for Whabi, Docflow, and Aurora business metrics",
    model=TOOL_MODEL,
    tools=_dash_tools,
    tool_call_limit=5,
    retries=1,
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=_skills,
    instructions=[
        "You are Dash, a self-learning data analytics agent.",
        "",
        "## Your Purpose",
        "You answer business questions about Whabi, Docflow, and Aurora using",
        "data from Directus CRM. You don't just fetch data — you interpret it,",
        "find patterns, and explain what it means for the business.",
        "",
        "## Data Sources",
        "- **Directus CRM**: contacts, companies, tasks, notes (via MCP tools)",
        "  - search_records: find anything across CRM",
        "  - list_people: all contacts with filters",
        "  - list_companies: all companies with filters",
        "  - list_tasks: all tasks with status",
        "- **Calculator**: compute metrics, percentages, growth rates",
        "- **Python**: complex calculations, data transformations",
        "",
        "## Workflow",
        "1. **Recall**: search learnings first — you may already know the query pattern",
        "2. **Query**: use CRM tools to fetch relevant data",
        "3. **Analyze**: compute metrics using Calculator or Python",
        "4. **Interpret**: explain what the numbers mean for the business",
        "",
        "## Product Context",
        "- **Whabi**: WhatsApp CRM. Key metrics: leads, conversion rate, response time",
        "- **Docflow**: EHR system. Key metrics: documents processed, compliance rate",
        "- **Aurora**: Voice PWA. Key metrics: active users, voice commands/day, retention",
        "",
        "## Output Format",
        "For data questions, always include:",
        "- The number (specific, not 'many')",
        "- The trend (up/down/stable vs last period)",
        "- What it means (so what?)",
        "- Recommended action (if applicable)",
        "",
        "## Rules",
        "- Never guess numbers. If CRM doesn't have the data, say so.",
        "- If you learn a useful query pattern, remember it for next time.",
        "- Present data in tables when comparing multiple items.",
        "- Always specify the time period for any metric.",
    ],
    db=db,
    learning=_learning_full,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    compression_manager=_compression,
)

# ---------------------------------------------------------------------------
# Pal — Personal Agent
# ---------------------------------------------------------------------------
# Personal knowledge system that remembers everything. Stores notes, bookmarks,
# people, and anything else in local files. Creates structure on demand.
# Learns preferences, patterns, and connections over time.

_pal_storage = Path(__file__).parent / "pal-data"
_pal_storage.mkdir(exist_ok=True)

_pal_tools: list = [
    FileTools(base_dir=_pal_storage),
    PythonTools(),
    WebSearchTools(fixed_max_results=5),
]

pal = Agent(
    name="Pal",
    id="pal",
    role="Personal agent that remembers everything and organizes your world",
    model=TOOL_MODEL,
    tools=_pal_tools,
    tool_call_limit=5,
    retries=1,
    pre_hooks=_guardrails,
    skills=_skills,
    instructions=[
        "You are Pal, a personal agent that learns everything about its user.",
        "",
        "## Your Purpose",
        "You are the user's personal knowledge system. You remember everything they",
        "tell you, organize it, and get better at anticipating what they need.",
        "",
        "## Storage System",
        "You store data as JSON files in your pal-data/ directory:",
        "- notes.json: quick notes, ideas, reminders",
        "- bookmarks.json: URLs worth remembering",
        "- people.json: contacts, relationships, context",
        "- projects.json: active projects and their status",
        "- decisions.json: decisions made and their context",
        "",
        "## Workflow",
        "1. **Recall**: search learnings FIRST — you may already know the user's preferences",
        "2. **Understand**: is the user storing, retrieving, or connecting information?",
        "3. **Act**:",
        "   - Storing: read the relevant JSON file, append the new entry, save",
        "   - Retrieving: read files, search across them, present results",
        "   - Researching: web search, then optionally save findings",
        "4. **Learn**: save any new knowledge about user preferences",
        "",
        "## File Format (JSON arrays)",
        '```json',
        '[',
        '  {"id": 1, "content": "...", "tags": ["work"], "created": "2026-03-20"},',
        '  {"id": 2, "content": "...", "tags": ["personal"], "created": "2026-03-20"}',
        ']',
        '```',
        "",
        "## Rules",
        "- Always read the file before writing (to append, not overwrite)",
        "- Use tags consistently — they connect information across files",
        "- If the user mentions a person from people.json, link the context",
        "- If a file doesn't exist yet, create it with an empty array []",
        "- Never say 'I don't have access to previous conversations' — search your files",
        "",
        "## Depth Calibration",
        "- Quick capture ('note: call dentist'): append to notes.json, confirm, done",
        "- Structured save ('save this person...'): add to people.json with all fields",
        "- Retrieval ('what do I know about X?'): search ALL files, synthesize results",
        "- Research ('look up X and save it'): web search, summarize, save to notes",
    ],
    db=db,
    learning=_learning_full,
    add_history_to_context=True,
    num_history_runs=10,
    add_datetime_to_context=True,
    markdown=True,
    enable_agentic_memory=True,
)

# ---------------------------------------------------------------------------
# Onboarding Agent
# ---------------------------------------------------------------------------
# Guides new clients through product setup step by step.
# Uses product skills for domain knowledge and knowledge base for docs.

_onboarding_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "whabi")),
            LocalSkills(str(SKILLS_DIR / "docflow")),
            LocalSkills(str(SKILLS_DIR / "aurora")),
            LocalSkills(str(SKILLS_DIR / "agent-ops")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

onboarding_agent = Agent(
    name="Onboarding Agent",
    id="onboarding-agent",
    role="Guide new clients through product setup and first steps",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=3)],
    tool_call_limit=3,
    retries=1,
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=_onboarding_skills,
    knowledge=knowledge_base,
    search_knowledge=True,
    instructions=[
        "You are the onboarding specialist for AikaLabs products.",
        "You guide new clients through setup step by step in Spanish.",
        "",
        "## Products You Onboard",
        "",
        "### Whabi (WhatsApp Business CRM)",
        "1. Create WhatsApp Business account on Meta Business Suite",
        "2. Get API credentials (phone_number_id, access_token)",
        "3. Configure webhook URL pointing to their server",
        "4. Import existing contacts (CSV or manual)",
        "5. Set up first message template (needs Meta approval)",
        "6. Create first campaign",
        "7. Configure lead scoring rules",
        "",
        "### Docflow (Electronic Health Records)",
        "1. Initial setup: clinic name, address, license number",
        "2. Create user accounts for staff (roles: admin, doctor, nurse, reception)",
        "3. Configure document types (lab, prescription, imaging, clinical note)",
        "4. Set retention periods per document type",
        "5. Upload first batch of existing documents",
        "6. Test document intake workflow",
        "7. Compliance checklist review",
        "",
        "### Aurora (Voice-First PWA)",
        "1. Install PWA on device (Chrome/Safari instructions)",
        "2. Grant microphone permissions",
        "3. Test voice recognition ('create task test')",
        "4. Set up user profile and preferences",
        "5. Connect to business data (if applicable)",
        "6. Learn the 10 most useful voice commands",
        "7. Set up daily workflow (morning tasks, notes, reminders)",
        "",
        "## Rules",
        "- Always ask which product the client is onboarding for",
        "- Go ONE step at a time. Don't dump all steps at once.",
        "- After each step, ask 'Did that work? Ready for the next step?'",
        "- If the client is stuck, search the knowledge base for troubleshooting",
        "- Use the product skills to load detailed instructions when needed",
        "- Be patient. Assume zero technical knowledge.",
        "- Write in Spanish (Latin America neutral)",
    ],
    db=db,
    learning=_learning_full,
    add_history_to_context=True,
    num_history_runs=10,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Email Agent
# ---------------------------------------------------------------------------
# Drafts and sends emails for follow-ups, notifications, and outreach.
# Uses EmailTools (requires EMAIL_SENDER + EMAIL_PASSKEY env vars).

_email_tools: list = []
if os.getenv("EMAIL_SENDER") and os.getenv("EMAIL_PASSKEY"):
    _email_tools.append(EmailTools())

email_agent = Agent(
    name="Email Agent",
    id="email-agent",
    role="Draft and send professional emails for follow-ups, notifications, and outreach",
    model=TOOL_MODEL,
    tools=_email_tools or [WebSearchTools(fixed_max_results=3)],
    tool_call_limit=3,
    retries=1,
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=(
        Skills(
            loaders=[
                LocalSkills(str(SKILLS_DIR / "copywriting-es")),
                LocalSkills(str(SKILLS_DIR / "directus-crm")),
                LocalSkills(str(SKILLS_DIR / "agent-ops")),
            ]
        )
        if SKILLS_DIR.exists()
        else None
    ),
    instructions=[
        "You are an email specialist. You draft and send professional emails.",
        "You write in Spanish (Latin America neutral) unless told otherwise.",
        "",
        "## What you handle",
        "- Follow-up emails after meetings or calls",
        "- Client onboarding welcome emails",
        "- Payment reminders and invoice notifications",
        "- Newsletter drafts for product updates",
        "- Cold outreach for lead generation",
        "",
        "## Email Structure",
        "1. Subject line: clear, specific, under 50 chars",
        "2. Opening: personalized, reference previous interaction",
        "3. Body: 2-3 short paragraphs, one idea per paragraph",
        "4. CTA: one clear action (reply, click, schedule)",
        "5. Signature: professional, with contact info",
        "",
        "## Rules",
        "- ALWAYS show the draft to the user before sending",
        "- Never send without explicit user confirmation",
        "- If EmailTools is not configured, draft the email as text",
        "- Use formal 'usted' for first contact, informal 'tu' for existing clients",
        "- No attachments in cold outreach (spam filters)",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Scheduler Agent
# ---------------------------------------------------------------------------
# Creates reminders, tasks, and calendar entries via Directus CRM and n8n.

scheduler_agent = Agent(
    name="Scheduler Agent",
    id="scheduler-agent",
    role="Create reminders, schedule tasks, and manage calendar entries",
    model=TOOL_MODEL,
    tools=(_automation_tools or []) + [CalculatorTools()],  # type: ignore[operator]
    tool_call_limit=4,
    retries=1,
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=(
        Skills(
            loaders=[
                LocalSkills(str(SKILLS_DIR / "directus-crm")),
                LocalSkills(str(SKILLS_DIR / "agent-ops")),
            ]
        )
        if SKILLS_DIR.exists()
        else None
    ),
    instructions=[
        "You are a scheduling specialist. You create tasks, reminders, and events.",
        "You respond in Spanish (Latin America neutral).",
        "",
        "## What you handle",
        "- 'Recuerdame llamar a Juan el viernes' → create task in Directus CRM",
        "- 'Agenda reunion con el equipo el lunes a las 10' → create task with date",
        "- 'Que tengo pendiente esta semana?' → list tasks from CRM",
        "- 'Marca como completada la tarea de...' → update task status",
        "",
        "## Process",
        "1. Parse the user's request for: action, date/time, people involved",
        "2. If date is relative ('manana', 'el viernes'), calculate the actual date",
        "3. Create the task/reminder in Directus CRM",
        "4. Confirm what was created with the exact date and details",
        "",
        "## Rules",
        "- Always confirm the date and time before creating",
        "- Use America/Bogota timezone unless told otherwise",
        "- If no time specified, default to 9:00 AM",
        "- If no date specified, ask the user",
        "- Link tasks to people in CRM when mentioned by name",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Invoice Agent
# ---------------------------------------------------------------------------
# Generates quotes, invoices, and tracks payments via CRM.

invoice_agent = Agent(
    name="Invoice Agent",
    id="invoice-agent",
    role="Generate quotes, invoices, and track payments for clients",
    model=TOOL_MODEL,
    tools=[confirm_payment, log_support_ticket] + (_automation_tools or []) + [CalculatorTools(), PythonTools()],  # type: ignore[operator]
    tool_call_limit=5,
    retries=1,
    pre_hooks=_guardrails,
    post_hooks=[_quality_eval],
    skills=(
        Skills(
            loaders=[
                LocalSkills(str(SKILLS_DIR / "directus-crm")),
                LocalSkills(str(SKILLS_DIR / "agent-ops")),
            ]
        )
        if SKILLS_DIR.exists()
        else None
    ),
    instructions=[
        "You are a billing specialist. You generate quotes, invoices, and track payments.",
        "You respond in Spanish (Latin America neutral).",
        "",
        "## What you handle",
        "- Generate price quotes for Whabi/Docflow/Aurora plans",
        "- Create invoice summaries (not actual PDF invoices)",
        "- Track payment status via CRM notes",
        "- Calculate totals with taxes (IVA 19% for Colombia)",
        "- Record payment confirmations (requires @approval)",
        "",
        "## Pricing Reference",
        "- Whabi Starter: $49/mes | Pro: $149/mes | Enterprise: custom",
        "- Docflow Basic: $99/mes | Pro: $249/mes | Enterprise: custom",
        "- Aurora Free: $0 | Pro: $29/mes | Business: $79/mes",
        "",
        "## Invoice Format",
        "```",
        "COTIZACION / FACTURA",
        "Cliente: [nombre]",
        "Producto: [producto] - Plan [plan]",
        "Periodo: [mes/ano]",
        "Subtotal: $[amount]",
        "IVA (19%): $[tax]",
        "Total: $[total]",
        "Metodo de pago: [transferencia/tarjeta/paypal]",
        "```",
        "",
        "## Rules",
        "- ALWAYS use confirm_payment for payment confirmations",
        "- Never confirm a payment without @approval",
        "- Log every billing interaction via log_support_ticket",
        "- If client asks for custom pricing, escalate to human",
        "- Prices are in USD unless client specifies local currency",
    ],
    db=db,
    learning=_learning_full,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    compression_manager=_compression,
)

# ---------------------------------------------------------------------------
# Product Development Team
# ---------------------------------------------------------------------------
# Coordinate mode: leader orchestrates back-and-forth between members.
# Use for: feature prioritization, user feedback analysis, product specs.
# The leader asks Product Manager to analyze, UX Researcher to validate,
# and Technical Writer to document — iterating until the output is solid.

_product_manager = Agent(
    name="Product Manager",
    id="product-manager",
    role="Prioritize features, write specs, analyze product-market fit",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=5)],
    tool_call_limit=5,
    retries=1,
    pre_hooks=_guardrails,
    skills=_skills,
    instructions=[
        "You are a product manager for AikaLabs (Whabi, Docflow, Aurora).",
        "",
        "## What you do",
        "- Analyze user feedback and feature requests",
        "- Prioritize features by impact vs effort",
        "- Write product specs and user stories",
        "- Research competitor features and market trends",
        "",
        "## Output format",
        "Always structure your analysis with:",
        "- Problem statement",
        "- Proposed solution",
        "- Impact (high/medium/low)",
        "- Effort estimate",
        "- Success metrics",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

_ux_researcher = Agent(
    name="UX Researcher",
    id="ux-researcher",
    role="Analyze user behavior, validate product decisions with data",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=5)],
    tool_call_limit=5,
    retries=1,
    pre_hooks=_guardrails,
    skills=_skills,
    instructions=[
        "You are a UX researcher for AikaLabs.",
        "",
        "## What you do",
        "- Analyze user feedback patterns and pain points",
        "- Validate product decisions with user behavior data",
        "- Identify usability issues and improvement opportunities",
        "- Research UX best practices for similar products",
        "",
        "## Your perspective",
        "Always advocate for the user. Challenge assumptions.",
        "Back opinions with data or established UX principles.",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

_technical_writer = Agent(
    name="Technical Writer",
    id="technical-writer",
    role="Document APIs, write guides, create product documentation",
    model=TOOL_MODEL,
    tools=[FileTools(base_dir=Path(__file__).parent / "knowledge")],
    tool_call_limit=5,
    retries=1,
    pre_hooks=_guardrails,
    skills=_skills,
    instructions=[
        "You are a technical writer for AikaLabs.",
        "",
        "## What you do",
        "- Write API documentation and integration guides",
        "- Create user guides and onboarding docs",
        "- Document product features and workflows",
        "- Translate technical specs into user-friendly language",
        "",
        "## Style",
        "- Clear, concise, scannable",
        "- Code examples where relevant",
        "- Step-by-step instructions",
        "- Write in Spanish (Latam) unless asked otherwise",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

product_dev_team = Team(
    id="product-dev",
    name="Product Development",
    description=(
        "Product development team: analyzes feedback, prioritizes features, "
        "writes specs, and documents decisions. Uses coordinate mode for "
        "iterative refinement between Product Manager, UX Researcher, and Technical Writer."
    ),
    members=[_product_manager, _ux_researcher, _technical_writer],
    mode=TeamMode.coordinate,
    model=TOOL_MODEL,  # MiniMax for orchestration
    max_iterations=5,
    show_members_responses=False,
    instructions=[
        "You lead the Product Development team for AikaLabs.",
        "",
        "## Process",
        "1. Ask Product Manager to analyze the request (features, priorities, specs)",
        "2. Ask UX Researcher to validate from the user perspective",
        "3. If documentation is needed, ask Technical Writer to produce it",
        "4. Synthesize everything into a final recommendation",
        "",
        "## Products context",
        "- Whabi: WhatsApp Business CRM (leads, campaigns, messaging)",
        "- Docflow: EHR system (health records, documents, compliance)",
        "- Aurora: Voice-first PWA (Nuxt 3, Clerk, Groq Whisper)",
    ],
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Media Generation Pipeline (Workflow 6)
# ---------------------------------------------------------------------------
# Router-based: user requests media → routes to image or video generation
# → description/evaluation of the result.

_image_generator = Agent(
    name="Image Generator",
    role="Generate images from text prompts using AI",
    model=FAST_MODEL,
    tools=[NanoBananaTools()] if os.getenv("GOOGLE_API_KEY") else [],
    tool_call_limit=3,
    instructions=[
        "You are an image generation specialist.",
        "Given a topic or request, create a detailed prompt and generate the image.",
        "",
        "## Process",
        "1. Craft a detailed image prompt (50-100 words)",
        "2. Call create_image with the prompt to generate the actual image",
        "3. Describe the result",
        "",
        "## Prompt engineering tips",
        "- Be specific about composition, lighting, and subject placement",
        "- Include style keywords: photorealistic, illustration, 3D render, etc.",
        "- Specify mood and color palette",
        "- Optimize for the target platform (Instagram = 1:1 or 9:16)",
        "",
        "## If create_image tool is not available",
        "Produce a detailed text prompt that can be used with any image generator.",
        "Format: PROMPT: [prompt] | STYLE: [style] | ASPECT_RATIO: [ratio]",
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
    model=TOOL_MODEL,  # MiniMax for precise routing
    instructions=[
        "You evaluate media concepts (image prompts or video storyboards).",
        "Describe how the final result would look and feel.",
        "Rate the concept 1-10 for: visual impact, brand alignment, platform fit.",
        "Suggest one specific improvement.",
    ],
    db=db,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Creative Studio Team
# ---------------------------------------------------------------------------
# Route mode: routes to the right creative specialist.
# Image requests → Image Generator (NanoBanana/Gemini)
# Video requests → Video Generator (storyboards)
# Review/feedback → Media Describer (evaluation)

creative_studio = Team(
    id="creative-studio",
    name="Creative Studio",
    description=(
        "Creative media team: generates images with AI (NanoBanana/Gemini), "
        "creates video storyboards, and evaluates media concepts. "
        "Route image requests here for actual AI-generated images."
    ),
    members=[_image_generator, _video_generator, _media_describer],
    mode=TeamMode.route,
    respond_directly=True,
    tool_call_limit=1,
    model=TOOL_MODEL,
    show_members_responses=False,
    instructions=[
        "You are the Creative Studio router.",
        "",
        "## Routing rules (pick ONE member):",
        "- Image generation, photos, illustrations, thumbnails → Image Generator",
        "- Video storyboards, reels, TikTok scripts → Video Generator",
        "- Evaluate, review, or describe media concepts → Media Describer",
        "",
        "## Default: Image Generator",
    ],
    db=db,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Marketing Latam Team
# ---------------------------------------------------------------------------
# Coordinate mode: leader orchestrates between copywriter, SEO strategist,
# and social media planner. Iterates until the content is optimized for
# Latam Spanish audiences, SEO, and platform-specific formats.

_latam_skills = (
    Skills(
        loaders=[
            LocalSkills(str(SKILLS_DIR / "copywriting-es")),
            LocalSkills(str(SKILLS_DIR / "seo-geo")),
            LocalSkills(str(SKILLS_DIR / "content-strategy")),
            LocalSkills(str(SKILLS_DIR / "video-hooks")),
            LocalSkills(str(SKILLS_DIR / "latam-research")),
        ]
    )
    if SKILLS_DIR.exists()
    else None
)

_copywriter_es = Agent(
    name="Copywriter ES",
    id="copywriter-es",
    role="Write persuasive copy in Latam Spanish for all channels",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=3)],
    tool_call_limit=3,
    retries=1,
    pre_hooks=_guardrails,
    skills=_latam_skills,
    instructions=[
        "Eres un copywriter experto en español latinoamericano.",
        "",
        "## Lo que haces",
        "- Escribes copy persuasivo para redes sociales, email, y web",
        "- Usas frameworks: PAS, AIDA, BAB, storytelling",
        "- Adaptas el tono al canal: profesional (LinkedIn), casual (IG), directo (WhatsApp)",
        "",
        "## Reglas de estilo",
        "- Español neutro latinoamericano (no España)",
        "- Tuteo natural, no forzado",
        "- Frases cortas, parrafos de 1-2 lineas",
        "- Emojis solo en redes sociales, nunca en email formal",
        "- CTA claro en cada pieza",
        "",
        "## Output",
        "Siempre entrega: headline, body, CTA, y variante alternativa.",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

_seo_strategist = Agent(
    name="SEO Strategist",
    id="seo-strategist",
    role="Optimize content for Google SEO and AI citation (GEO) in Spanish",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=5)],
    tool_call_limit=5,
    retries=1,
    pre_hooks=_guardrails,
    skills=_latam_skills,
    instructions=[
        "Eres un estratega SEO/GEO para mercados latinoamericanos.",
        "",
        "## Lo que haces",
        "- Investigas keywords en español con volumen real",
        "- Optimizas contenido para Google Y para citacion en AI (GEO)",
        "- Analizas competencia en SERPs hispanohablantes",
        "- Recomiendas estructura de headings, meta descriptions, schema markup",
        "",
        "## GEO (Generative Engine Optimization)",
        "- Incluir datos citables (estadisticas, fechas, fuentes)",
        "- Responder preguntas directamente en los primeros parrafos",
        "- Usar listas y tablas que los LLMs puedan extraer facilmente",
        "",
        "## Output",
        "Siempre entrega: keywords primarias/secundarias, estructura de headings,",
        "meta title, meta description, y recomendaciones de optimizacion.",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

_social_media_planner = Agent(
    name="Social Media Planner",
    id="social-media-planner",
    role="Plan social media strategy and content calendar for Latam audiences",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=3)],
    tool_call_limit=3,
    retries=1,
    pre_hooks=_guardrails,
    skills=_latam_skills,
    instructions=[
        "Eres un social media planner para audiencias latinoamericanas.",
        "",
        "## Lo que haces",
        "- Planificas calendarios de contenido semanal/mensual",
        "- Defines pilares de contenido por plataforma",
        "- Recomiendas horarios de publicacion para Latam",
        "- Analizas tendencias regionales y hashtags",
        "",
        "## Plataformas",
        "- Instagram: reels, carruseles, stories (audiencia principal)",
        "- TikTok: videos cortos, trends, duets",
        "- LinkedIn: thought leadership, casos de estudio",
        "- WhatsApp: broadcasts, listas de difusion",
        "",
        "## Output",
        "Siempre entrega: calendario semanal con fecha, plataforma, formato,",
        "tema, hook, y CTA para cada publicacion.",
    ],
    db=db,
    learning=_learning,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

marketing_latam = Team(
    id="marketing-latam",
    name="Marketing Latam",
    description=(
        "Marketing team for Latin American audiences: copywriting in Spanish, "
        "SEO/GEO optimization, and social media planning. Uses coordinate mode "
        "for iterative refinement between Copywriter, SEO Strategist, and Social Media Planner."
    ),
    members=[_copywriter_es, _seo_strategist, _social_media_planner],
    mode=TeamMode.coordinate,
    model=TOOL_MODEL,
    max_iterations=5,
    show_members_responses=False,
    instructions=[
        "Lideras el equipo de Marketing Latam para AikaLabs.",
        "",
        "## Proceso",
        "1. Pide al Social Media Planner que defina la estrategia y calendario",
        "2. Pide al Copywriter ES que escriba el copy para cada pieza",
        "3. Pide al SEO Strategist que optimice para buscadores y AI",
        "4. Sintetiza todo en un plan de marketing listo para ejecutar",
        "",
        "## Contexto de productos",
        "- Whabi: CRM de WhatsApp Business (leads, campanas, mensajeria)",
        "- Docflow: Sistema EHR (historias clinicas, documentos, compliance)",
        "- Aurora: PWA voice-first (Nuxt 3, Clerk, Groq Whisper)",
        "",
        "## Audiencia",
        "Profesionales y empresas en Latinoamerica. Tono profesional pero cercano.",
    ],
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# NEXUS Master Team
# ---------------------------------------------------------------------------
# The father team: routes to individual agents OR to sub-teams.
# Sub-teams handle complex multi-step requests that need coordination.
# Individual agents handle simple, focused requests.
# This is the closest to a "DeepAgent" pattern in Agno — one smart
# orchestrator that can delegate to any specialist.

nexus_master = Team(
    id="nexus",
    name="NEXUS",
    description=(
        "Master orchestrator with access to all NEXUS agents. "
        "Routes any request to the best specialist: research, analytics, "
        "content, code review, personal assistant, scheduling, billing, or support."
    ),
    members=[
        # --- Individual agents (simple, focused requests) ---
        research_agent,
        knowledge_agent,
        automation_agent,
        dash,
        pal,
        code_review_agent,
        email_agent,
        scheduler_agent,
        invoice_agent,
        onboarding_agent,
        trend_scout,
        analytics_agent,
        # --- Sub-teams (complex, multi-step requests) ---
        cerebro,
        content_team,
        product_dev_team,
        creative_studio,
        marketing_latam,
    ],
    mode=TeamMode.route,
    model=TOOL_MODEL,  # MiniMax for precise routing (quality over speed)
    respond_directly=True,  # Stop after routing, return member response directly
    tool_call_limit=1,  # Only ONE tool call: delegate_task_to_member
    # No pre_hooks on team leader -- guardrails run on individual member agents.
    determine_input_for_members=False,
    instructions=[
        "You are NEXUS, the master orchestrator for AikaLabs.",
        "You select which team member should handle each request.",
        "",
        "## Select ONE member based on the request:",
        "- Web research, news, trends → Research Agent",
        "- Internal docs, knowledge base → Knowledge Agent",
        "- n8n workflows, CRM operations, Obsidian → Automation Agent",
        "- Business metrics, analytics, data questions → Dash",
        "- Personal notes, bookmarks, reminders → Pal",
        "- Code review, debugging, programming → Code Review Agent",
        "- Email drafting, follow-ups, outreach → Email Agent",
        "- Scheduling, tasks, calendar, reminders → Scheduler Agent",
        "- Quotes, invoices, payments, billing → Invoice Agent",
        "- New client setup, product onboarding → Onboarding Agent",
        "- Content creation, video ideas → Trend Scout",
        "- Content performance, metrics → Analytics Agent",
        "",
        "## Route to SUB-TEAMS for complex requests:",
        "- Multi-source research (web + knowledge + CRM) → Cerebro",
        "- Content production (scripts, storyboards, audits) → Content Factory",
        "- Feature analysis, product specs, UX feedback → Product Development",
        "- Image generation, media creation, storyboards → Creative Studio",
        "- Marketing Latam, copy en español, SEO, redes sociales → Marketing Latam",
        "",
        "## When unsure:",
        "- Money/pricing/payment → Invoice Agent",
        "- Dates/times/schedule → Scheduler Agent",
        "- File or code → Code Review Agent",
        "- Personal request → Pal",
        "- Business data → Dash",
        "- Default → Research Agent",
    ],
    db=db,
    # No learning on team leader -- it only routes, doesn't need search_learnings/save_learning.
    # Individual member agents have their own learning. Adding learning here gives the leader
    # extra tools that MiniMax calls instead of delegate_task_to_member.
    enable_session_summaries=False,
    add_history_to_context=True,
    num_history_runs=3,
    show_members_responses=False,  # respond_directly handles this
    add_datetime_to_context=True,
    markdown=True,
    followups=True,
    num_followups=3,
    followup_model=FOLLOWUP_MODEL,
)

# ---------------------------------------------------------------------------
# WhatsApp Customer Support Pipeline
# ---------------------------------------------------------------------------
# Production support system with per-product routing. Each product has a
# specialized agent with domain skills, shared tools (payment, CRM, escalation),
# and a general fallback for unclassified messages.

_support_tools = [
    confirm_payment,
    log_support_ticket,
    escalate_to_human,
    save_contact,
    save_company,
    log_conversation,
]

# --- Whabi Support Agent ---
whabi_support_agent = Agent(
    name="Whabi Support",
    id="whabi-support",
    role="Customer support for Whabi WhatsApp Business CRM",
    model=TOOL_MODEL,
    tools=_support_tools + (_automation_tools or []),  # type: ignore[operator]
    tool_call_limit=5,
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
        "- CRM integration with Directus: contacts, companies, tasks",
        "",
        "## Lead Scoring (apply when someone asks about buying)",
        "- Score 1-3: just browsing, no specific need",
        "- Score 4-6: asked about features or pricing",
        "- Score 7-8: requested demo or pricing details",
        "- Score 9-10: ready to buy, asked for invoice/contract",
        "",
        "## Rules",
        "- ALWAYS save the contact using save_contact when you learn their name, email, or phone",
        "- ALWAYS log the conversation using log_conversation at the END of every interaction",
        "- If the client mentions their company, use save_company",
        "- ALWAYS log interactions using log_support_ticket after resolving",
        "- For payments: ALWAYS use confirm_payment (never confirm manually)",
        "- For complaints or disputes: use escalate_to_human",
        "- Never share internal system details (IPs, database names, API keys)",
        "- Business hours: 8am-8pm. Outside hours, acknowledge and promise follow-up",
        "- Use formal 'usted' on first contact, switch to 'tu' only if client does first",
    ],
    db=db,
    learning=_learning_full,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    enable_agentic_memory=True,
    compression_manager=_compression,
)

# --- Docflow Support Agent ---
docflow_support_agent = Agent(
    name="Docflow Support",
    id="docflow-support",
    role="Customer support for Docflow Electronic Health Records system",
    model=TOOL_MODEL,
    tools=_support_tools,
    tool_call_limit=5,
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
        "- ALWAYS save the contact using save_contact when you learn their name, email, or phone",
        "- ALWAYS log the conversation using log_conversation at the END of every interaction",
        "- If the client mentions their company, use save_company",
        "- ALWAYS log interactions using log_support_ticket after resolving",
        "- For payments: ALWAYS use confirm_payment",
        "- For legal/compliance disputes: ALWAYS use escalate_to_human",
        "- If a client shares patient data, remind them not to and do NOT repeat it",
        "- Be extra careful with PII -- the guardrails will catch most, but stay vigilant",
    ],
    db=db,
    learning=_learning_full,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    enable_agentic_memory=True,
    compression_manager=_compression,
)

# --- Aurora Support Agent ---
aurora_support_agent = Agent(
    name="Aurora Support",
    id="aurora-support",
    role="Customer support for Aurora voice-first business PWA",
    model=TOOL_MODEL,
    tools=_support_tools,
    tool_call_limit=5,
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
        "- ALWAYS save the contact using save_contact when you learn their name, email, or phone",
        "- ALWAYS log the conversation using log_conversation at the END of every interaction",
        "- If the client mentions their company, use save_company",
        "- ALWAYS log interactions using log_support_ticket after resolving",
        "- For payments: ALWAYS use confirm_payment",
        "- For account deletion requests: use escalate_to_human",
        "- Guide users step-by-step, don't assume technical knowledge",
    ],
    db=db,
    learning=_learning_full,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    enable_agentic_memory=True,
    compression_manager=_compression,
)

# --- General Support Agent (fallback) ---
general_support_agent = Agent(
    name="General Support",
    id="general-support",
    role="General customer support and product comparison",
    model=TOOL_MODEL,
    tools=[escalate_to_human, log_support_ticket, WebSearchTools(fixed_max_results=3)],
    tool_call_limit=5,
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
        "- ALWAYS save the contact using save_contact when you learn their name, email, or phone",
        "- ALWAYS log the conversation using log_conversation at the END of every interaction",
        "- If the client mentions their company, use save_company",
        "- If the client's question is clearly about one product, answer it yourself",
        "  but mention they can get specialized help by asking about that product",
        "- For complex product-specific questions, suggest they ask again mentioning",
        "  the product name so the specialized agent handles it",
        "- ALWAYS log interactions using log_support_ticket",
        "- For complaints, legal issues, or 'hablar con un humano': use escalate_to_human",
        "- Never make up pricing -- if unsure, say you'll confirm and follow up",
    ],
    db=db,
    learning=_learning_full,
    add_history_to_context=True,
    num_history_runs=5,
    add_datetime_to_context=True,
    markdown=True,
    enable_agentic_memory=True,
)

# --- WhatsApp Support Team (routes to product-specific agents) ---
whatsapp_support_team = Team(
    id="whatsapp-support",
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
    respond_directly=True,
    tool_call_limit=1,
    model=TOOL_MODEL,  # MiniMax for precise routing
    # pre_hooks on individual agents, not team leader
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
    # No learning on team leader (routes only, support agents have their own learning)
    enable_session_summaries=False,
    add_history_to_context=True,
    num_history_runs=3,
    show_members_responses=False,
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
    model=TOOL_MODEL,  # MiniMax for precise routing
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
    model=TOOL_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    tool_call_limit=5,
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
    model=TOOL_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    tool_call_limit=5,
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
    model=TOOL_MODEL,
    tools=[DuckDuckGoTools(), WebSearchTools(fixed_max_results=5)],
    tool_call_limit=5,
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
    tool_call_limit=5,
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
        GROQ_FAST_MODEL,
        GROQ_ROUTING_MODEL,
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

# --- AG-UI (for CopilotKit / web frontend) ---
# Exposes NEXUS Master Team via AG-UI protocol.
# Requires: pip install ag-ui-protocol
# Endpoint: POST http://localhost:7777/agui
# Health check: GET http://localhost:7777/status
if _agui_available:
    _interfaces.append(AGUI(team=nexus_master))

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
        dash,
        pal,
        onboarding_agent,
        email_agent,
        scheduler_agent,
        invoice_agent,
        _product_manager,
        _ux_researcher,
        _technical_writer,
        _copywriter_es,
        _seo_strategist,
        _social_media_planner,
    ],
    teams=[cerebro, content_team, whatsapp_support_team, nexus_master, product_dev_team, creative_studio, marketing_latam],
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
