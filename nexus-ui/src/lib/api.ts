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
  agent_id: string;
  role?: string;
  description?: string;
  model?: { id?: string };
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
  team_id: string;
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
  workflow_id: string;
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
