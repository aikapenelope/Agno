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

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.voyageai import VoyageAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.groq import Groq
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.registry import Registry
from agno.team import Team
from agno.tools.mcp import MCPTools
from agno.tools.arxiv import ArxivTools
from agno.tools.calculator import CalculatorTools
from agno.tools.csv_toolkit import CsvTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.email import EmailTools
from agno.tools.exa import ExaTools
from agno.tools.file import FileTools
from agno.tools.github import GithubTools
from agno.tools.hackernews import HackerNewsTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.tools.python import PythonTools
from agno.tools.reddit import RedditTools
from agno.tools.slack import SlackTools
from agno.tools.tavily import TavilyTools
from agno.tools.todoist import TodoistTools
from agno.tools.websearch import WebSearchTools
from agno.tools.wikipedia import WikipediaTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.youtube import YouTubeTools
from agno.vectordb.lancedb import LanceDb, SearchType

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

knowledge_base = Knowledge(vector_db=vector_db)

# Index all supported files in the knowledge/ folder on startup.
for file_path in sorted(KNOWLEDGE_DIR.iterdir()):
    if file_path.suffix.lower() in {".pdf", ".txt", ".md", ".csv", ".json"}:
        knowledge_base.insert(path=file_path, skip_if_exists=True)

# ---------------------------------------------------------------------------
# Model Configuration
# ---------------------------------------------------------------------------

# --- Groq Models ---
# Reasoning model: GPT-OSS 120B - best reasoning on Groq, cheaper than Llama 3.3.
# Has tool calling issues, so only used where tools are not needed.
REASONING_MODEL = Groq(id="openai/gpt-oss-120b")

# Tool model: Llama 3.3 70B - reliable tool calling with fixed_max_results workaround.
TOOL_MODEL = Groq(id="llama-3.3-70b-versatile")

# Fast model: Llama 3.1 8B - ultra fast and cheap for simple tasks.
FAST_MODEL = Groq(id="llama-3.1-8b-instant")

# --- MiniMax Models (OpenAI-compatible API) ---
# M2.5: 204K context, advanced reasoning + tool calling, ~60 tps.
MINIMAX_MODEL = OpenAIChat(
    id="MiniMax-M2.5",
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url="https://api.minimax.io/v1",
)

# M2.5 Highspeed: same performance, ~100 tps. Best for fast responses.
MINIMAX_FAST_MODEL = OpenAIChat(
    id="MiniMax-M2.5-highspeed",
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url="https://api.minimax.io/v1",
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
    instructions=[
        "You are a research specialist.",
        "Use the web_search tool to find current, accurate information.",
        "Always include sources with URLs and dates.",
        "Present data in structured formats when possible.",
        "Be thorough but concise.",
    ],
    db=db,
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
    instructions=[
        "You are a knowledge specialist.",
        "Search the knowledge base for relevant information before answering.",
        "Provide context from internal knowledge and past analyses.",
        "Cross-reference information across different domains.",
        "Cite specific facts and relationships.",
        "When no relevant knowledge is found, work from conversation context.",
    ],
    db=db,
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
if os.getenv("N8N_API_KEY"):
    _automation_tools.append(
        MCPTools(
            command="npx -y @makafeli/n8n-workflow-builder",
            env={
                "N8N_HOST": "http://localhost:5678",
                "N8N_API_KEY": os.getenv("N8N_API_KEY", ""),
            },
            timeout_seconds=30,
        )
    )

# Twenty CRM: manage contacts, companies, tasks, notes.
if os.getenv("TWENTY_API_KEY"):
    _automation_tools.append(
        MCPTools(
            command="node ~/twenty-crm-mcp-server/index.js",
            env={
                "TWENTY_API_KEY": os.getenv("TWENTY_API_KEY", ""),
                "TWENTY_BASE_URL": os.getenv("TWENTY_BASE_URL", "http://localhost:3000"),
            },
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
    instructions=[
        "You are an automation specialist with access to n8n and Twenty CRM.",
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
        "## General",
        "- Report results of executed automations clearly.",
        "- Confirm before executing any destructive or irreversible actions.",
        "- If a service is not connected, explain what you would do if it were.",
    ],
    db=db,
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
    model=TOOL_MODEL,  # Team leader needs tool calling to delegate tasks to members
    knowledge=knowledge_base,
    instructions=[
        "You are Cerebro, a senior analyst leading a research team.",
        "",
        "## Process",
        "1. Analyze the request and decompose it into subtasks",
        "2. Delegate to the right specialists:",
        "   - Research Agent: current web data, market info, news, competitors",
        "   - Knowledge Agent: internal context, documents, historical data",
        "   - Automation Agent: n8n workflows, Twenty CRM (contacts, companies, tasks)",
        "3. Synthesize all findings into a structured report",
        "",
        "## Output Format",
        "After gathering information from your team, provide:",
        "- **Executive Summary**: 2-3 sentence overview",
        "- **Key Findings**: organized by source (web research, internal knowledge)",
        "- **Analysis & Insights**: your synthesis and interpretation",
        "- **Recommendations**: actionable next steps",
        "- **Sources**: URLs and references",
        "",
        "Be decisive and analytical. Acknowledge uncertainty when data is limited.",
    ],
    db=db,
    enable_session_summaries=True,
    add_history_to_context=True,
    num_history_runs=5,
    show_members_responses=True,
    add_datetime_to_context=True,
    markdown=True,
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
    Newspaper4kTools(),
    PythonTools(),
    WebSearchTools(fixed_max_results=5),
    WikipediaTools(),
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

registry = Registry(
    name="NEXUS Registry",
    tools=_registry_tools,
    models=[
        REASONING_MODEL,
        TOOL_MODEL,
        FAST_MODEL,
        MINIMAX_MODEL,
        MINIMAX_FAST_MODEL,
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
    agents=[research_agent, knowledge_agent, automation_agent],
    teams=[cerebro],
    knowledge=[knowledge_base],
    registry=registry,
    db=db,
    tracing=True,
)
app = agent_os.get_app()

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # reload=False required when using MCP tools (lifespan conflicts)
    agent_os.serve(app="nexus:app", port=7777, reload=False)
