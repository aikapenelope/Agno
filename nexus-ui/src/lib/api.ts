const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7777";

/* ------------------------------------------------------------------ */
/* Generic helpers                                                     */
/* ------------------------------------------------------------------ */

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

function formRun(message: string, sessionId: string, userId = "nexus-ui") {
  const fd = new FormData();
  fd.append("message", message);
  fd.append("stream", "false");
  fd.append("session_id", sessionId);
  fd.append("user_id", userId);
  return fd;
}

/* ------------------------------------------------------------------ */
/* Agents                                                              */
/* ------------------------------------------------------------------ */

export interface AgentInfo {
  name: string;
  id: string;
  role?: string;
  description?: string;
  model?: { id?: string; name?: string; model?: string };
  tools?: string[];
}

export const listAgents = () => request<AgentInfo[]>("/agents");

export const runAgent = (agentId: string, message: string, sessionId: string) =>
  request<Record<string, unknown>>(`/agents/${encodeURIComponent(agentId)}/runs`, {
    method: "POST",
    body: formRun(message, sessionId),
  });

/* ------------------------------------------------------------------ */
/* Teams                                                               */
/* ------------------------------------------------------------------ */

export interface TeamInfo {
  name: string;
  id: string;
  team_id?: string;
  description?: string;
  mode?: string;
  members?: Array<{ name: string }>;
}

export const listTeams = () => request<TeamInfo[]>("/teams");

export const runTeam = (teamId: string, message: string, sessionId: string) =>
  request<Record<string, unknown>>(`/teams/${encodeURIComponent(teamId)}/runs`, {
    method: "POST",
    body: formRun(message, sessionId),
  });

/* ------------------------------------------------------------------ */
/* Workflows                                                           */
/* ------------------------------------------------------------------ */

export interface WorkflowInfo {
  name: string;
  id: string;
  workflow_id?: string;
  description?: string;
}

export const listWorkflows = () => request<WorkflowInfo[]>("/workflows");

export const runWorkflow = (wfId: string, message: string, sessionId: string) =>
  request<Record<string, unknown>>(`/workflows/${encodeURIComponent(wfId)}/runs`, {
    method: "POST",
    body: formRun(message, sessionId),
  });

/* ------------------------------------------------------------------ */
/* Approvals                                                           */
/* ------------------------------------------------------------------ */

export interface Approval {
  id: string;
  source_name?: string;
  context?: Record<string, unknown>;
  status: string;
  created_at?: number;
}

export const listApprovals = () => request<Approval[]>("/approvals");
export const approvalCount = () => request<{ count: number }>("/approvals/count");
export const resolveApproval = (id: string, status: "approved" | "rejected") =>
  request<unknown>(`/approvals/${id}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, resolved_by: "nexus-ui" }),
  });

/* ------------------------------------------------------------------ */
/* Schedules                                                           */
/* ------------------------------------------------------------------ */

export const listSchedules = () => request<unknown[]>("/schedules");

/* ------------------------------------------------------------------ */
/* Sessions (chat history)                                             */
/* ------------------------------------------------------------------ */

export interface SessionInfo {
  session_id: string;
  agent_id?: string;
  team_id?: string;
  user_id?: string;
  created_at?: number;
  updated_at?: number;
  session_data?: Record<string, unknown>;
}

export interface SessionRun {
  run_id: string;
  input?: string;
  output?: string;
  content?: string;
  agent_name?: string;
  created_at?: number;
}

export const listSessions = () => request<SessionInfo[]>("/sessions");
export const getSessionRuns = (sessionId: string) =>
  request<SessionRun[]>(`/sessions/${encodeURIComponent(sessionId)}/runs`);

/* ------------------------------------------------------------------ */
/* Traces                                                              */
/* ------------------------------------------------------------------ */

export interface Trace {
  trace_id: string;
  agent_id?: string;
  team_id?: string;
  workflow_id?: string;
  session_id?: string;
  user_id?: string;
  input?: string;
  output?: string;
  status?: string;
  duration_ms?: number;
  tokens_in?: number;
  tokens_out?: number;
  model?: string;
  tool_calls?: Array<{ name: string; duration_ms?: number }>;
  created_at?: number;
  metadata?: Record<string, unknown>;
}

export const listTraces = (limit = 50) =>
  request<Trace[]>(`/traces?limit=${limit}`);
export const getTrace = (traceId: string) =>
  request<Trace>(`/traces/${encodeURIComponent(traceId)}`);
export const searchTraces = (query: string) =>
  request<Trace[]>(`/traces/search?query=${encodeURIComponent(query)}`);

/* ------------------------------------------------------------------ */
/* Metrics                                                             */
/* ------------------------------------------------------------------ */

export const getMetrics = () => request<Record<string, unknown>>("/metrics");
export const refreshMetrics = () =>
  request<Record<string, unknown>>("/metrics/refresh", { method: "POST" });

/* ------------------------------------------------------------------ */
/* Knowledge                                                           */
/* ------------------------------------------------------------------ */

export interface KnowledgeContent {
  content_id: string;
  name?: string;
  source?: string;
  content_type?: string;
  status?: string;
  created_at?: number;
  metadata?: Record<string, unknown>;
}

export const listKnowledge = () => request<KnowledgeContent[]>("/knowledge/content");
export const searchKnowledge = (query: string) =>
  request<unknown[]>(`/knowledge/search?query=${encodeURIComponent(query)}`);
export const getKnowledgeConfig = () => request<unknown>("/knowledge/config");

export async function uploadKnowledge(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request<unknown>("/knowledge/content", { method: "POST", body: fd });
}

/* ------------------------------------------------------------------ */
/* Memory                                                              */
/* ------------------------------------------------------------------ */

export interface Memory {
  id: string;
  user_id?: string;
  content?: string;
  topic?: string;
  memory_type?: string;
  created_at?: number;
  metadata?: Record<string, unknown>;
}

export const listMemories = () => request<Memory[]>("/memory");
export const listMemoryTopics = () => request<string[]>("/memory_topics");
export const deleteMemory = (id: string) =>
  request<unknown>(`/memory/${id}`, { method: "DELETE" });
