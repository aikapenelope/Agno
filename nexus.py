"""
NEXUS Cerebro - Multi-Agent Analysis System
============================================

A multi-agent analysis system powered by Agno and Groq.
Cerebro orchestrates specialized agents to decompose complex tasks,
research the web, query a knowledge graph, and execute automations.

Based on official Agno cookbook patterns:
- cookbook/05_agent_os/demo.py (AgentOS setup)
- cookbook/90_models/groq/agent_team.py (Groq + Team)
- cookbook/91_tools/mcp/graphiti.py (MCP integration)
- cookbook/00_quickstart/multi_agent_team.py (Team patterns)

Prerequisites:
    pip install -r requirements.txt

    Set environment variable:
        export GROQ_API_KEY="your-groq-api-key"

    Optional MCP servers (connect when ready):
        - Graphiti MCP server for knowledge graph
        - n8n MCP server for workflow automation

Usage:
    python nexus.py
    Then connect AgentOS UI at https://os.agno.com -> Add new OS -> Local
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.groq import Groq
from agno.os import AgentOS
from agno.team import Team
from agno.tools.websearch import WebSearchTools

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

db = SqliteDb(db_file="nexus.db")

# ---------------------------------------------------------------------------
# Model Configuration
# ---------------------------------------------------------------------------

# Reasoning model: GPT-OSS 120B - best reasoning on Groq, cheaper than Llama 3.3.
# Has tool calling issues, so only used where tools are not needed.
REASONING_MODEL = Groq(id="openai/gpt-oss-120b")

# Tool model: Llama 3.3 70B - reliable tool calling with fixed_max_results workaround.
TOOL_MODEL = Groq(id="llama-3.3-70b-versatile")

# Fast model: Llama 3.1 8B - ultra fast and cheap for simple tasks.
FAST_MODEL = Groq(id="llama-3.1-8b-instant")

# ---------------------------------------------------------------------------
# Research Agent
# ---------------------------------------------------------------------------

research_agent = Agent(
    name="Research Agent",
    role="Search the web for current information and data",
    model=TOOL_MODEL,
    tools=[WebSearchTools(fixed_max_results=5)],
    instructions=[
        "You are a research specialist.",
        "Search the web for current, accurate information.",
        "Always include sources with URLs and dates.",
        "Present data in structured formats when possible.",
        "Be thorough but concise.",
    ],
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    update_memory_on_run=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Knowledge Agent
# ---------------------------------------------------------------------------
# MCP URL placeholder: update when Graphiti MCP server is ready.
# Example: MCPTools(url="http://localhost:8000/sse", transport="sse")

knowledge_agent = Agent(
    name="Knowledge Agent",
    role="Query internal knowledge and provide context from the knowledge graph",
    model=REASONING_MODEL,
    # tools=[MCPTools(url="http://localhost:8000/sse", transport="sse")],
    instructions=[
        "You are a knowledge specialist.",
        "Provide context from internal knowledge and past analyses.",
        "Cross-reference information across different domains.",
        "Cite specific facts and relationships.",
        "When the knowledge graph is not connected, work from conversation context.",
    ],
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    update_memory_on_run=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Automation Agent
# ---------------------------------------------------------------------------
# MCP URL placeholder: update when n8n MCP server is ready.
# Example: MCPTools(url="http://localhost:5678/mcp", transport="sse")

automation_agent = Agent(
    name="Automation Agent",
    role="Execute workflows and automations",
    model=FAST_MODEL,
    # tools=[MCPTools(url="http://localhost:5678/mcp", transport="sse")],
    instructions=[
        "You are an automation specialist.",
        "Execute workflows when actions are needed.",
        "Report the results of executed automations clearly.",
        "Confirm before executing any destructive or irreversible actions.",
        "When n8n is not connected, describe what automation you would execute.",
    ],
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    update_memory_on_run=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# Cerebro Team
# ---------------------------------------------------------------------------

cerebro = Team(
    name="Cerebro",
    description="Multi-agent analysis system that decomposes complex tasks",
    members=[research_agent, knowledge_agent, automation_agent],
    model=REASONING_MODEL,
    instructions=[
        "You are Cerebro, a senior analyst leading a research team.",
        "",
        "## Process",
        "1. Analyze the request and decompose it into subtasks",
        "2. Delegate to the right specialists:",
        "   - Research Agent: current web data, market info, news, competitors",
        "   - Knowledge Agent: internal context, past decisions, historical data",
        "   - Automation Agent: only when actions need to be executed",
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
    update_memory_on_run=True,
    enable_session_summaries=True,
    add_history_to_context=True,
    num_history_runs=5,
    show_members_responses=True,
    add_datetime_to_context=True,
    markdown=True,
)

# ---------------------------------------------------------------------------
# AgentOS
# ---------------------------------------------------------------------------

agent_os = AgentOS(
    id="nexus",
    description="NEXUS Cerebro - Multi-agent analysis system",
    agents=[research_agent, knowledge_agent, automation_agent],
    teams=[cerebro],
    tracing=True,
)
app = agent_os.get_app()

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent_os.serve(app="nexus:app", port=7777, reload=True)
