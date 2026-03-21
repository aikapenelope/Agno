# NEXUS UI

Frontend for the NEXUS multi-agent system, built with [CopilotKit](https://copilotkit.ai) + [AG-UI protocol](https://ag-ui.com).

## Prerequisites

- Node.js 18+
- NEXUS AgentOS running (`python nexus.py` on port 7777)
- `ag-ui-protocol` installed (`pip install ag-ui-protocol`)

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
    │
    ▼
CopilotKit (React + AG-UI protocol)
    │  POST /agui (streaming SSE)
    ▼
AgentOS (localhost:7777)
    │
    ▼
NEXUS Master Team (MiniMax M2.7 orchestrator)
    │
    ├── Research Agent      "investiga X"
    ├── Dash                "cuantos leads esta semana"
    ├── Pal                 "guardame esta nota"
    ├── Email Agent         "redacta un email para X"
    ├── Scheduler Agent     "recuerdame llamar a X"
    ├── Invoice Agent       "genera cotizacion para X"
    ├── Code Review Agent   "revisa este codigo"
    ├── Onboarding Agent    "como configuro Whabi"
    ├── Knowledge Agent     "que dice nuestra KB sobre X"
    ├── Automation Agent    "ejecuta el workflow de n8n"
    ├── Trend Scout         "busca tendencias de AI"
    └── Analytics Agent     "metricas de Instagram"
```

## Deploy to Vercel

```bash
npx vercel
```

Set `NEXT_PUBLIC_AGUI_URL` to your production AgentOS URL.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_AGUI_URL` | `http://localhost:7777` | AgentOS backend URL |
