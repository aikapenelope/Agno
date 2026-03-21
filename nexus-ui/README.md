# NEXUS UI

Frontend for the NEXUS multi-agent system. Connects directly to AgentOS REST API.

## Prerequisites

- Node.js 18+
- NEXUS AgentOS running (`python nexus.py` on port 7777)

## Setup

```bash
cd nexus-ui
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## How it works

```
Browser (localhost:3000)
    |
    v
Next.js app (React)
    |  POST /v1/teams/NEXUS/runs
    v
AgentOS (localhost:7777)
    |
    v
NEXUS Master Team (MiniMax M2.7 orchestrator)
    |
    +-- Research Agent      "investiga X"
    +-- Dash                "cuantos leads esta semana"
    +-- Pal                 "guardame esta nota"
    +-- Email Agent         "redacta un email para X"
    +-- Scheduler Agent     "recuerdame llamar a X"
    +-- Invoice Agent       "genera cotizacion para X"
    +-- Code Review Agent   "revisa este codigo"
    +-- Onboarding Agent    "como configuro Whabi"
    +-- Knowledge Agent     "que dice nuestra KB sobre X"
    +-- Automation Agent    "ejecuta el workflow de n8n"
    +-- Trend Scout         "busca tendencias de AI"
    +-- Analytics Agent     "metricas de Instagram"
```

## Deploy to Vercel

```bash
npx vercel
```

Set `NEXT_PUBLIC_API_URL` to your production AgentOS URL.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:7777` | AgentOS backend URL |

## Why not CopilotKit?

CopilotKit requires a middleware runtime between the frontend and the agent backend.
The AG-UI protocol integration with Agno is still maturing (JSON-RPC format mismatch
as of March 2026). This UI connects directly to AgentOS REST API which is stable
and fully functional. When CopilotKit adds direct AG-UI endpoint support, we can
switch to it for generative UI features.
