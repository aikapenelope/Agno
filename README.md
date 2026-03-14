# NEXUS Cerebro

Multi-agent analysis system powered by [Agno](https://agno.com) and [Groq](https://groq.com).

Cerebro orchestrates specialized agents to decompose complex tasks, research the web, query a knowledge graph (Graphiti), and execute automations (n8n).

## Architecture

```
os.agno.com (free) ── Chat UI + Traces + Metrics
  │
localhost:7777 ── AgentOS (FastAPI, 50+ APIs)
  │
  ├── Cerebro (Team leader, Groq llama-3.3-70b)
  │     Decomposes, coordinates, synthesizes
  │
  ├── Research Agent (Groq llama-3.3-70b)
  │     WebSearchTools
  │
  ├── Knowledge Agent (Groq llama-3.3-70b)
  │     MCPTools → Graphiti (when connected)
  │
  ├── Automation Agent (Groq llama-3.3-70b)
  │     MCPTools → n8n (when connected)
  │
  └── SQLite (sessions, memories, traces)
```

## Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set Groq API key
export GROQ_API_KEY="your-key"

# Run
python nexus.py
```

## Connect AgentOS UI

1. Open [os.agno.com](https://os.agno.com)
2. Click "Add new OS" → "Local"
3. Enter endpoint: `http://localhost:7777`
4. Chat with Cerebro and individual agents

## Connect MCP Servers

Edit `nexus.py` and uncomment the `MCPTools` lines with your server URLs:

```python
# Knowledge Agent - Graphiti
tools=[MCPTools(url="http://localhost:8000/sse", transport="sse")]

# Automation Agent - n8n
tools=[MCPTools(url="http://localhost:5678/mcp", transport="sse")]
```

## Costs

| Component | Cost |
|---|---|
| Agno + AgentOS | $0 (open source + free tier) |
| Groq API (free tier) | $0 (30 req/min) |
| Groq API (paid) | ~$0.59/1M input tokens |
| Observability | $0 (native tracing) |
