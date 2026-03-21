# NEXUS UI — Master Prompt for Production Dashboard

## Project Overview

Build a production-grade command center for NEXUS, a multi-agent AI system running on Agno framework. The current UI is a basic chat interface (single page.tsx, 215 lines). Transform it into a full dashboard that serves as the central hub for managing agents, teams, workflows, WhatsApp conversations, CRM data, approvals, and content — all connected to the same AgentOS backend.

## Tech Stack

- **Framework**: Next.js 15 (App Router, already initialized)
- **Language**: TypeScript
- **Styling**: Tailwind CSS (already configured)
- **UI Components**: shadcn/ui (install: `npx shadcn@latest init`)
- **Icons**: Lucide React
- **State**: Zustand for global state, React Query (TanStack Query) for API caching
- **Charts**: Recharts for analytics dashboards
- **Markdown**: react-markdown + remark-gfm for agent responses
- **Backend**: AgentOS REST API at `http://localhost:7777` (configurable via `NEXT_PUBLIC_API_URL`)

## Backend API Reference (AgentOS)

All endpoints accept/return JSON unless noted. Teams endpoint uses FormData.

### Core Endpoints

```
GET    /agents                              → List all registered agents
GET    /agents/{agent_id}                   → Agent details
POST   /agents/{agent_id}/runs              → Run agent (FormData: message, stream, session_id, user_id)
POST   /agents/{agent_id}/runs/{run_id}/cancel → Cancel run
POST   /agents/{agent_id}/runs/{run_id}/continue → Continue paused run

GET    /teams                               → List all teams
GET    /teams/{team_id}                     → Team details
POST   /teams/{team_id}/runs                → Run team (FormData: message, stream, session_id, user_id)
POST   /teams/{team_id}/runs/{run_id}/cancel → Cancel run

GET    /workflows                           → List all workflows
GET    /workflows/{workflow_id}             → Workflow details
POST   /workflows/{workflow_id}/runs        → Run workflow (FormData: message, stream, session_id, user_id)
WS     /workflows/ws                        → WebSocket for workflow streaming

GET    /sessions                            → List sessions
GET    /memory                              → List memories

GET    /approvals                           → List pending approvals
GET    /approvals/count                     → Count pending approvals
GET    /approvals/{id}                      → Approval details
POST   /approvals/{id}/resolve              → Approve/reject (body: {status, resolved_by})

GET    /schedules                           → List scheduled tasks
POST   /schedules                           → Create schedule
PATCH  /schedules/{id}                      → Update schedule
DELETE /schedules/{id}                      → Delete schedule
POST   /schedules/{id}/trigger              → Trigger immediately
POST   /schedules/{id}/enable               → Enable
POST   /schedules/{id}/disable              → Disable
```

### Important: Team runs use FormData, not JSON

```typescript
const formData = new FormData();
formData.append("message", text);
formData.append("stream", "false");  // false = JSON response, true = SSE stream
formData.append("session_id", sessionId);
formData.append("user_id", userId);

const res = await fetch(`${API_URL}/teams/nexus/runs`, {
  method: "POST",
  body: formData,
});
const data = await res.json(); // { content: "...", agent_name: "Research Agent", ... }
```

### Approval flow (human-in-the-loop)

When an agent calls a tool with `@approval` (e.g., `confirm_payment`), the run pauses:
```json
{ "status": "paused", "is_paused": true, "active_requirements": [...] }
```
The UI must show an approval dialog. After user approves/rejects, call:
```
POST /teams/{team_id}/runs/{run_id}/continue
```

## System Architecture

### Agents (46 total)

**Registered in AgentOS (visible in dashboard):**
- Research Agent, Knowledge Agent, Automation Agent
- Trend Scout, Scriptwriter, Creative Director, Analytics Agent
- Code Review Agent, Dash (business analytics), Pal (personal assistant)
- Email Agent, Scheduler Agent, Invoice Agent, Onboarding Agent
- Whabi Support, Docflow Support, Aurora Support, General Support
- Product Manager, UX Researcher, Technical Writer
- Copywriter ES, SEO Strategist, Social Media Planner

**Internal (used in workflows, not directly accessible):**
- 5 search scouts, Research Planner, Research Synthesizer
- Keyword Researcher, Article Writer, SEO Auditor
- 3 social media writers, Social Media Auditor
- 3 competitor scouts, Competitor Synthesizer
- Image Generator (NanoBanana), Video Generator, Media Describer

### Teams (7)

| Team ID | Name | Mode | Members |
|---------|------|------|---------|
| `nexus` | NEXUS Master | route | 12 agents + 5 sub-teams |
| `cerebro` | Cerebro | route | Research, Knowledge, Automation |
| `content-factory` | Content Factory | route | Trend Scout, Scriptwriter, Analytics |
| `product-dev` | Product Development | coordinate | PM, UX Researcher, Tech Writer |
| `creative-studio` | Creative Studio | route | Image Gen, Video Gen, Media Describer |
| `marketing-latam` | Marketing Latam | coordinate | Copywriter ES, SEO, Social Media |
| `whatsapp-support` | WhatsApp Support | route | Whabi, Docflow, Aurora, General |

### Workflows (7)

| ID | Name | Steps |
|----|------|-------|
| `deep-research` | Deep Research | Plan → Parallel scouts → Quality gate → Report |
| `content-production` | Content Production | Trend → Compact → Script → Creative review |
| `client-research` | Client Research | Parallel(web + knowledge) → Synthesis |
| `seo-content` | SEO Content | Keyword → Article → Audit loop |
| `social-media-autopilot` | Social Media | Trend → Parallel(IG/TW/LI) → Audit |
| `competitor-intelligence` | Competitor Intel | Parallel(3 scouts) → Synthesis |
| `media-generation` | Media Generation | Router(image vs video) → Generation |

### Products (context for the UI)

- **Whabi**: WhatsApp Business CRM (leads, campaigns, messaging)
- **Docflow**: EHR system (health records, documents, compliance)
- **Aurora**: Voice-first PWA (Nuxt 3, Clerk, Groq Whisper)

## Dashboard Layout

### Navigation (Left Sidebar)

```
NEXUS
├── 💬 Chat (main NEXUS conversation)
├── 📱 WhatsApp (live conversations)
├── 👥 CRM (Twenty CRM data)
├── 🤖 Agents (agent status & direct access)
├── 👥 Teams (team management)
├── ⚡ Workflows (run & monitor)
├── ✅ Approvals (pending approvals badge)
├── 📅 Schedules (cron jobs)
├── 📊 Analytics (usage, costs, performance)
└── ⚙️ Settings (API keys, preferences)
```

### Page Specifications

#### 1. Chat (`/`)
The main NEXUS conversation interface. Current functionality preserved but enhanced:
- Markdown rendering for agent responses (code blocks, tables, lists)
- Agent avatar/badge showing which agent responded
- Suggested follow-up questions (from `followups` in response)
- File upload support (images, PDFs — AgentOS accepts multipart)
- Session history sidebar (list past sessions, click to resume)
- Approval inline cards: when response has `is_paused: true`, show approve/reject buttons inline

#### 2. WhatsApp (`/whatsapp`)
Live view of WhatsApp conversations handled by the WhatsApp Support Team:
- List of active conversations (phone number, last message, timestamp)
- Click to view full conversation thread
- Manual reply input: type a message and send it via WhatsApp API
- Agent response preview: see what the agent would respond before sending
- Conversation status: active, waiting, resolved
- Filter by product: Whabi, Docflow, Aurora, General

**Data source**: WhatsApp conversations are stored in the session database. Query via:
```
GET /sessions?team_id=whatsapp-support
```

#### 3. CRM (`/crm`)
Interface to Twenty CRM data via the Automation Agent's MCP tools:
- Contacts list with search
- Companies list
- Recent activities/notes
- Quick actions: "Add contact", "Log interaction", "Create task"
- All actions go through the Automation Agent (not direct CRM API)

**Implementation**: Send messages to the Automation Agent:
```
POST /agents/Automation Agent/runs
FormData: message="List all contacts from this week"
```

#### 4. Agents (`/agents`)
Agent management dashboard:
- Grid/list of all registered agents with status indicators
- Click agent → detail view with:
  - Agent description and role
  - Tools available
  - Recent runs (last 10)
  - Direct chat (send message to specific agent, bypassing NEXUS routing)
- Performance metrics per agent (response time, success rate)

#### 5. Teams (`/teams`)
Team overview:
- Visual diagram of team structure (NEXUS → sub-teams → agents)
- Click team → detail view with members, mode, recent runs
- Direct team chat (send to specific team)

#### 6. Workflows (`/workflows`)
Workflow runner and monitor:
- List of 7 workflows with descriptions
- "Run" button → input form → execute workflow
- Progress indicator showing current step
- Results display with markdown rendering
- History of past workflow runs

#### 7. Approvals (`/approvals`)
Pending approval queue:
- Badge count in sidebar navigation
- List of pending approvals with:
  - Tool name (confirm_payment, save_video_file, etc.)
  - Agent that requested it
  - Parameters (amount, file name, etc.)
  - Approve / Reject buttons
  - Timestamp
- Resolved approvals history

#### 8. Schedules (`/schedules`)
Cron job management:
- List of active schedules
- Create new schedule (cron expression builder)
- Enable/disable toggle
- Trigger manually button
- Run history per schedule

#### 9. Analytics (`/analytics`)
Usage and performance dashboard:
- Token usage over time (chart)
- Requests per agent/team (bar chart)
- Response time distribution
- Cost breakdown (MiniMax vs OpenRouter)
- Active sessions count
- Most used agents ranking

#### 10. Settings (`/settings`)
Configuration:
- API URL configuration
- User ID / session preferences
- Theme (dark mode is default)
- API key status indicators (which keys are set)

## Design System

### Colors (Dark Theme — current palette)
```
Background:     #0a0a0a (main), #1a1a2e (header/sidebar)
Surface:        #111111 (cards), #1a1a1a (elevated)
Border:         #2a2a2a (subtle), #3a3a3a (hover)
Primary:        #e94560 (AikaLabs red — buttons, accents)
Primary hover:  #d63d56
Text:           #ffffff (primary), #a0a0a0 (secondary), #666666 (muted)
Success:        #10b981
Warning:        #f59e0b
Error:          #ef4444
Agent badge:    #3b82f6 (blue)
```

### Typography
- Font: Inter (system fallback: -apple-system, sans-serif)
- Headings: font-bold, tracking-tight
- Body: text-sm (14px) for most content
- Code: font-mono, bg-gray-900

### Components (shadcn/ui)
Install these components:
```bash
npx shadcn@latest add button card input textarea badge dialog
npx shadcn@latest add tabs table dropdown-menu command
npx shadcn@latest add sheet scroll-area separator skeleton
npx shadcn@latest add toast tooltip avatar
```

## Key Implementation Details

### API Communication Pattern

```typescript
// lib/api.ts — centralized API client
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7777";

export async function runTeam(teamId: string, message: string, sessionId: string) {
  const formData = new FormData();
  formData.append("message", message);
  formData.append("stream", "false");
  formData.append("session_id", sessionId);
  formData.append("user_id", "nexus-ui-user");

  const res = await fetch(`${API_URL}/teams/${teamId}/runs`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function runAgent(agentId: string, message: string, sessionId: string) {
  const formData = new FormData();
  formData.append("message", message);
  formData.append("stream", "false");
  formData.append("session_id", sessionId);
  formData.append("user_id", "nexus-ui-user");

  const res = await fetch(`${API_URL}/agents/${agentId}/runs`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function listAgents() {
  const res = await fetch(`${API_URL}/agents`);
  return res.json();
}

export async function listTeams() {
  const res = await fetch(`${API_URL}/teams`);
  return res.json();
}

export async function listWorkflows() {
  const res = await fetch(`${API_URL}/workflows`);
  return res.json();
}

export async function listApprovals() {
  const res = await fetch(`${API_URL}/approvals`);
  return res.json();
}

export async function resolveApproval(id: string, status: "approved" | "rejected", resolvedBy: string) {
  const res = await fetch(`${API_URL}/approvals/${id}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, resolved_by: resolvedBy }),
  });
  return res.json();
}
```

### Approval Handling in Chat

When a team run returns `is_paused: true`:

```typescript
if (data.is_paused && data.active_requirements) {
  // Show approval card inline in chat
  for (const req of data.active_requirements) {
    if (req.needs_confirmation) {
      // Render: "Invoice Agent wants to confirm_payment($500 for Clinica Norte)"
      // With [Approve] [Reject] buttons
      // On approve: POST /teams/nexus/runs/{run_id}/continue
    }
  }
}
```

### Session Management

```typescript
// Store in Zustand
interface NexusStore {
  sessionId: string;
  userId: string;
  activeTeam: string; // "nexus" by default
  pendingApprovals: number;
  // ...
}
```

### File Structure

```
nexus-ui/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout with sidebar
│   │   ├── page.tsx                # Chat (main)
│   │   ├── whatsapp/page.tsx       # WhatsApp conversations
│   │   ├── crm/page.tsx            # CRM interface
│   │   ├── agents/
│   │   │   ├── page.tsx            # Agent grid
│   │   │   └── [id]/page.tsx       # Agent detail + direct chat
│   │   ├── teams/
│   │   │   ├── page.tsx            # Team overview
│   │   │   └── [id]/page.tsx       # Team detail + direct chat
│   │   ├── workflows/
│   │   │   ├── page.tsx            # Workflow list
│   │   │   └── [id]/page.tsx       # Workflow runner
│   │   ├── approvals/page.tsx      # Approval queue
│   │   ├── schedules/page.tsx      # Schedule management
│   │   ├── analytics/page.tsx      # Usage dashboard
│   │   └── settings/page.tsx       # Configuration
│   ├── components/
│   │   ├── layout/
│   │   │   ├── sidebar.tsx         # Navigation sidebar
│   │   │   └── header.tsx          # Top bar with search
│   │   ├── chat/
│   │   │   ├── message-bubble.tsx  # Chat message with markdown
│   │   │   ├── chat-input.tsx      # Input with file upload
│   │   │   ├── approval-card.tsx   # Inline approval UI
│   │   │   └── agent-badge.tsx     # Agent name badge
│   │   ├── whatsapp/
│   │   │   ├── conversation-list.tsx
│   │   │   └── conversation-thread.tsx
│   │   └── shared/
│   │       ├── markdown-renderer.tsx
│   │       └── loading-skeleton.tsx
│   ├── lib/
│   │   ├── api.ts                  # API client
│   │   ├── store.ts                # Zustand store
│   │   └── utils.ts                # Helpers
│   └── hooks/
│       ├── use-agents.ts           # React Query hooks
│       ├── use-teams.ts
│       ├── use-approvals.ts
│       └── use-sessions.ts
```

## Critical Requirements

1. **Spanish-first UI**: All labels, placeholders, and messages in Spanish (Latam). Agent responses may be in English or Spanish — render as-is.

2. **Dark theme only**: No light mode. The current dark palette is the brand identity.

3. **Responsive**: Must work on desktop (primary) and tablet. Mobile is secondary but sidebar should collapse.

4. **No CopilotKit**: Connect directly to AgentOS REST API. No AG-UI protocol, no CopilotKit SDK. Pure fetch/React Query.

5. **stream=false**: All API calls use `stream: "false"` for clean JSON responses. No SSE parsing needed.

6. **Approval UX**: When a run pauses for approval, the UI MUST show the approval dialog. This is critical for payment confirmations.

7. **Error handling**: Show toast notifications for API errors. Never crash on malformed responses.

8. **Loading states**: Skeleton loaders for lists, bounce animation for chat. Never show blank screens.

9. **Markdown in responses**: Agent responses contain markdown (headers, code blocks, tables, lists). Render properly with syntax highlighting for code.

10. **Real-time approval badge**: Poll `/approvals/count` every 30 seconds. Show badge on sidebar.
