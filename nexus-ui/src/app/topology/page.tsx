"use client";

import { useCallback, useState, useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
  Handle,
  Position,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Bot,
  Users,
  Workflow,
  Wrench,
  Database,
  Globe,
  MessageSquare,
  X,
  Send,
  Loader2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import PageHeader from "@/components/layout/page-header";
import { runAgent, runTeam, listAgents, listTeams, listWorkflows, type AgentInfo, type TeamInfo, type WorkflowInfo } from "@/lib/api";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface AgentNode {
  id: string;
  name: string;
  tools: string[];
  model: string;
  mcp?: string[];
  learning?: string;
}

interface TeamNode {
  id: string;
  name: string;
  mode: string;
  members: string[];
}

interface WorkflowNode {
  id: string;
  name: string;
  steps: string[];
}

/* ------------------------------------------------------------------ */
/* Static metadata (enriches API data with info the API doesn't return) */
/* ------------------------------------------------------------------ */

const AGENT_META: Record<string, { mcp?: string[]; learning?: string }> = {
  "automation-agent": { mcp: ["n8n", "Twenty CRM"], learning: "minimal" },
  "dash": { mcp: ["Twenty CRM"], learning: "full" },
  "pal": { learning: "full" },
  "onboarding-agent": { learning: "full" },
  "invoice-agent": { learning: "full" },
  "whabi-support": { learning: "full" },
  "docflow-support": { learning: "full" },
  "aurora-support": { learning: "full" },
  "general-support": { learning: "full" },
  "knowledge-agent": { learning: "minimal" },
  "code-review-agent": { learning: "minimal" },
};

const WORKFLOW_STEPS: Record<string, string[]> = {
  "deep-research": ["Planner", "Scouts (parallel)", "Quality Gate", "Synthesizer"],
  "content-production": ["Trend", "Compact", "Script", "Review"],
  "seo-content": ["Keywords", "Article", "Audit"],
  "social-media-autopilot": ["Trend", "IG/TW/LI (parallel)", "Audit"],
  "competitor-intelligence": ["3 Scouts (parallel)", "Synthesis"],
  "client-research": ["Web + KB (parallel)", "Synthesis"],
  "media-generation": ["Router", "Generate", "Describe"],
};

const MCP_SERVERS = [
  { id: "mcp-n8n", name: "n8n", type: "Workflow Automation" },
  { id: "mcp-twenty", name: "Twenty CRM", type: "CRM Database" },
];

/* ------------------------------------------------------------------ */
/* Transform API data to topology nodes                                */
/* ------------------------------------------------------------------ */

function apiAgentToNode(a: AgentInfo): AgentNode {
  const meta = AGENT_META[a.id] || {};
  const tools: string[] = [];
  if (Array.isArray(a.tools)) {
    for (const t of a.tools) {
      if (typeof t === "string") tools.push(t);
      else if (typeof t === "object" && t !== null && "name" in t) tools.push((t as { name: string }).name);
    }
  }
  return {
    id: a.id || a.name.toLowerCase().replace(/\s+/g, "-"),
    name: a.name,
    tools,
    model: a.model?.model || a.model?.name || "MiniMax",
    mcp: meta.mcp,
    learning: meta.learning || "minimal",
  };
}

function apiTeamToNode(t: TeamInfo): TeamNode {
  return {
    id: t.id || t.team_id || t.name.toLowerCase().replace(/\s+/g, "-"),
    name: t.name,
    mode: t.mode || "route",
    members: (t.members || []).map((m) => {
      if (typeof m === "string") return m;
      if (typeof m === "object" && m !== null && "name" in m) {
        const name = (m as { name: string }).name;
        return name.toLowerCase().replace(/\s+/g, "-");
      }
      return String(m);
    }),
  };
}

function apiWorkflowToNode(w: WorkflowInfo): WorkflowNode {
  const wfId = w.id || w.workflow_id || w.name.toLowerCase().replace(/\s+/g, "-");
  return {
    id: wfId,
    name: w.name,
    steps: WORKFLOW_STEPS[wfId] || WORKFLOW_STEPS[w.name] || ["Step 1", "Step 2", "Step 3"],
  };
}

/* ------------------------------------------------------------------ */
/* Custom node components                                              */
/* ------------------------------------------------------------------ */

function TeamNodeComponent({ data }: { data: { label: string; mode: string; memberCount: number; color: string; onClick: () => void } }) {
  return (
    <div
      onClick={data.onClick}
      className="bg-[#0f0f12] border-2 rounded-xl px-4 py-3 min-w-[160px] cursor-pointer hover:brightness-110 transition-all"
      style={{ borderColor: data.color }}
    >
      <Handle type="target" position={Position.Top} className="!bg-zinc-600 !w-2 !h-2" />
      <div className="flex items-center gap-2 mb-1">
        <Users size={12} style={{ color: data.color }} />
        <span className="text-[12px] font-semibold text-white">{data.label}</span>
      </div>
      <div className="flex items-center gap-2 text-[10px] text-zinc-500">
        <span className="px-1.5 py-0.5 rounded bg-zinc-900">{data.mode}</span>
        <span>{data.memberCount} miembros</span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-zinc-600 !w-2 !h-2" />
    </div>
  );
}

function AgentNodeComponent({ data }: { data: { agent: AgentNode; onClick: () => void } }) {
  const a = data.agent;
  return (
    <div
      onClick={data.onClick}
      className="bg-[#0f0f12] border border-[#2a2a30] rounded-lg px-3 py-2.5 min-w-[150px] cursor-pointer hover:border-emerald-500/50 transition-all group"
    >
      <Handle type="target" position={Position.Top} className="!bg-zinc-700 !w-1.5 !h-1.5" />
      <div className="flex items-center gap-2 mb-1.5">
        <Bot size={11} className="text-emerald-400" />
        <span className="text-[11px] font-medium text-white group-hover:text-emerald-400 transition-colors">{a.name}</span>
      </div>
      <div className="flex flex-wrap gap-1">
        {a.tools.slice(0, 3).map((t) => (
          <span key={t} className="text-[8px] text-zinc-500 bg-zinc-900 px-1.5 py-0.5 rounded flex items-center gap-0.5">
            <Wrench size={7} /> {t.replace("Tools", "")}
          </span>
        ))}
        {a.tools.length > 3 && (
          <span className="text-[8px] text-zinc-600">+{a.tools.length - 3}</span>
        )}
      </div>
      {a.mcp && a.mcp.length > 0 && (
        <div className="flex gap-1 mt-1">
          {a.mcp.map((m) => (
            <span key={m} className="text-[8px] text-violet-400 bg-violet-500/10 px-1.5 py-0.5 rounded flex items-center gap-0.5">
              <Database size={7} /> {m}
            </span>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2 mt-1.5 text-[8px] text-zinc-600">
        <span>{a.model}</span>
        {a.learning && <span className="text-zinc-700">• {a.learning}</span>}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-zinc-700 !w-1.5 !h-1.5" />
    </div>
  );
}

function WorkflowNodeComponent({ data }: { data: { workflow: WorkflowNode; onClick: () => void } }) {
  const w = data.workflow;
  return (
    <div
      onClick={data.onClick}
      className="bg-[#0f0f12] border border-violet-500/30 rounded-lg px-3 py-2.5 min-w-[140px] cursor-pointer hover:border-violet-500/60 transition-all"
    >
      <div className="flex items-center gap-2 mb-1.5">
        <Workflow size={11} className="text-violet-400" />
        <span className="text-[11px] font-medium text-white">{w.name}</span>
      </div>
      <div className="text-[8px] text-zinc-500 font-mono">
        {w.steps.join(" → ")}
      </div>
    </div>
  );
}

function McpNodeComponent({ data }: { data: { name: string; type: string } }) {
  return (
    <div className="bg-[#0f0f12] border border-amber-500/30 rounded-lg px-3 py-2.5 min-w-[120px]">
      <Handle type="target" position={Position.Left} className="!bg-amber-500 !w-2 !h-2" />
      <div className="flex items-center gap-2 mb-1">
        <Globe size={11} className="text-amber-400" />
        <span className="text-[11px] font-medium text-white">{data.name}</span>
      </div>
      <span className="text-[8px] text-zinc-500">{data.type}</span>
    </div>
  );
}

const nodeTypes: NodeTypes = {
  teamNode: TeamNodeComponent,
  agentNode: AgentNodeComponent,
  workflowNode: WorkflowNodeComponent,
  mcpNode: McpNodeComponent,
};

/* ------------------------------------------------------------------ */
/* Build graph layout                                                  */
/* ------------------------------------------------------------------ */

function buildGraph(
  AGENTS: AgentNode[],
  TEAMS: TeamNode[],
  WORKFLOWS: WorkflowNode[],
  onNodeClick: (type: string, id: string) => void,
) {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const TEAM_COLORS: Record<string, string> = {
    nexus: "#10b981",
    cerebro: "#8b5cf6",
    "content-factory": "#06b6d4",
    "product-dev": "#f59e0b",
    "creative-studio": "#ec4899",
    "marketing-latam": "#3b82f6",
    "whatsapp-support": "#22c55e",
  };

  // NEXUS at top center
  nodes.push({
    id: "nexus",
    type: "teamNode",
    position: { x: 500, y: 30 },
    data: { label: "NEXUS Master", mode: "route", memberCount: 17, color: TEAM_COLORS.nexus, onClick: () => onNodeClick("team", "nexus") },
  });

  // Sub-teams in a row below NEXUS
  const subTeams = TEAMS.filter((t) => t.id !== "nexus");
  const teamStartX = 50;
  const teamSpacing = 200;

  subTeams.forEach((team, i) => {
    const x = teamStartX + i * teamSpacing;
    const y = 160;

    nodes.push({
      id: team.id,
      type: "teamNode",
      position: { x, y },
      data: { label: team.name, mode: team.mode, memberCount: team.members.length, color: TEAM_COLORS[team.id] || "#71717a", onClick: () => onNodeClick("team", team.id) },
    });

    // Edge from NEXUS to sub-team
    if (team.id !== "whatsapp-support") {
      edges.push({
        id: `nexus-${team.id}`,
        source: "nexus",
        target: team.id,
        style: { stroke: TEAM_COLORS[team.id] || "#333", strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: TEAM_COLORS[team.id] || "#333" },
      });
    }

    // Agents under each team
    const teamAgents = team.members.filter((m) => !TEAMS.find((t) => t.id === m));
    teamAgents.forEach((agentId, j) => {
      const agent = AGENTS.find((a) => a.id === agentId);
      if (!agent) return;

      const ax = x - 30 + (j % 2) * 170;
      const ay = y + 120 + Math.floor(j / 2) * 100;

      nodes.push({
        id: agent.id,
        type: "agentNode",
        position: { x: ax, y: ay },
        data: { agent, onClick: () => onNodeClick("agent", agent.id) },
      });

      edges.push({
        id: `${team.id}-${agent.id}`,
        source: team.id,
        target: agent.id,
        style: { stroke: "#27272a", strokeWidth: 1 },
        animated: false,
      });
    });
  });

  // MCP servers on the right
  MCP_SERVERS.forEach((mcp, i) => {
    nodes.push({
      id: mcp.id,
      type: "mcpNode",
      position: { x: 1400, y: 200 + i * 100 },
      data: { name: mcp.name, type: mcp.type },
    });
  });

  // Connect MCP to agents that use them
  edges.push({ id: "mcp-n8n-auto", source: "automation-agent", target: "mcp-n8n", style: { stroke: "#f59e0b", strokeDasharray: "4 4" }, animated: true });
  edges.push({ id: "mcp-twenty-auto", source: "automation-agent", target: "mcp-twenty", style: { stroke: "#f59e0b", strokeDasharray: "4 4" }, animated: true });
  edges.push({ id: "mcp-twenty-dash", source: "dash", target: "mcp-twenty", style: { stroke: "#f59e0b", strokeDasharray: "4 4" }, animated: true });

  // Workflows at the bottom
  WORKFLOWS.forEach((wf, i) => {
    nodes.push({
      id: wf.id,
      type: "workflowNode",
      position: { x: 50 + i * 190, y: 750 },
      data: { workflow: wf, onClick: () => onNodeClick("workflow", wf.id) },
    });
  });

  return { nodes, edges };
}

/* ------------------------------------------------------------------ */
/* Detail panel                                                        */
/* ------------------------------------------------------------------ */

function DetailPanel({
  type,
  id,
  onClose,
  agents: AGENTS,
  teams: TEAMS,
  workflows: WORKFLOWS,
}: {
  type: string;
  id: string;
  onClose: () => void;
  agents: AgentNode[];
  teams: TeamNode[];
  workflows: WorkflowNode[];
}) {
  const [chatInput, setChatInput] = useState("");
  const [chatOutput, setChatOutput] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const agent = AGENTS.find((a) => a.id === id);
  const team = TEAMS.find((t) => t.id === id);
  const workflow = WORKFLOWS.find((w) => w.id === id);

  async function sendMessage() {
    if (!chatInput.trim() || loading) return;
    setLoading(true);
    setChatOutput(null);
    try {
      const data =
        type === "team"
          ? await runTeam(id, chatInput.trim(), `topo-${Date.now()}`)
          : await runAgent(id, chatInput.trim(), `topo-${Date.now()}`);
      const content = typeof data.content === "string" ? data.content : JSON.stringify(data);
      setChatOutput(content);
    } catch (err) {
      setChatOutput(`Error: ${err instanceof Error ? err.message : "Fallo"}`);
    } finally {
      setLoading(false);
      setChatInput("");
    }
  }

  return (
    <div className="absolute right-0 top-0 bottom-0 w-[380px] bg-[#0c0c0f] border-l border-[#1e1e24] flex flex-col z-50 shadow-2xl">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e1e24] shrink-0">
        <div className="flex items-center gap-2">
          {type === "agent" && <Bot size={14} className="text-emerald-400" />}
          {type === "team" && <Users size={14} className="text-blue-400" />}
          {type === "workflow" && <Workflow size={14} className="text-violet-400" />}
          <span className="text-[14px] font-medium text-white">
            {agent?.name || team?.name || workflow?.name}
          </span>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-colors">
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Agent detail */}
        {agent && (
          <>
            <div>
              <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Modelo</div>
              <span className="text-[12px] text-zinc-300 bg-zinc-900 px-2 py-1 rounded">{agent.model}</span>
            </div>
            {agent.tools.length > 0 && (
              <div>
                <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Tools ({agent.tools.length})</div>
                <div className="space-y-1">
                  {agent.tools.map((t) => (
                    <div key={t} className="flex items-center gap-2 text-[12px] text-zinc-400 bg-zinc-900/50 px-2.5 py-1.5 rounded-lg">
                      <Wrench size={10} className="text-zinc-600" /> {t}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {agent.mcp && agent.mcp.length > 0 && (
              <div>
                <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">MCP Servers</div>
                <div className="space-y-1">
                  {agent.mcp.map((m) => (
                    <div key={m} className="flex items-center gap-2 text-[12px] text-violet-400 bg-violet-500/10 px-2.5 py-1.5 rounded-lg">
                      <Database size={10} /> {m}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {agent.learning && (
              <div>
                <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Learning</div>
                <span className="text-[12px] text-zinc-400">{agent.learning === "full" ? "Full (profile + memory + entities + knowledge)" : "Minimal (learned knowledge only)"}</span>
              </div>
            )}
          </>
        )}

        {/* Team detail */}
        {team && (
          <>
            <div>
              <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Modo</div>
              <span className="text-[12px] text-zinc-300 bg-zinc-900 px-2 py-1 rounded">{team.mode}</span>
            </div>
            <div>
              <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Miembros ({team.members.length})</div>
              <div className="space-y-1">
                {team.members.map((m) => {
                  const a = AGENTS.find((ag) => ag.id === m);
                  const t = TEAMS.find((te) => te.id === m);
                  return (
                    <div key={m} className="flex items-center gap-2 text-[12px] text-zinc-400 bg-zinc-900/50 px-2.5 py-1.5 rounded-lg">
                      {a ? <Bot size={10} className="text-emerald-400" /> : <Users size={10} className="text-blue-400" />}
                      {a?.name || t?.name || m}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* Workflow detail */}
        {workflow && (
          <div>
            <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Pipeline</div>
            <div className="space-y-2">
              {workflow.steps.map((step, i) => (
                <div key={step} className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-violet-500/20 flex items-center justify-center text-[9px] text-violet-400 font-bold shrink-0">
                    {i + 1}
                  </div>
                  <span className="text-[12px] text-zinc-300">{step}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick chat */}
        {(type === "agent" || type === "team") && (
          <div className="border-t border-[#1e1e24] pt-4">
            <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">
              <MessageSquare size={10} className="inline mr-1" />
              Chat rapido
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                placeholder="Mensaje..."
                className="flex-1 bg-zinc-900 border border-[#1e1e24] rounded-lg px-3 py-2 text-[12px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !chatInput.trim()}
                className="p-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-30 transition-colors"
              >
                {loading ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
              </button>
            </div>
            {chatOutput && (
              <div className="mt-3 bg-zinc-900/50 border border-[#1e1e24] rounded-lg p-3 max-h-[200px] overflow-y-auto">
                <div className="agent-response text-[12px] text-zinc-300 leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{chatOutput}</ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Topology page                                                       */
/* ------------------------------------------------------------------ */

export default function TopologyPage() {
  const [detail, setDetail] = useState<{ type: string; id: string } | null>(null);
  const [agents, setAgents] = useState<AgentNode[]>([]);
  const [teams, setTeams] = useState<TeamNode[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowNode[]>([]);
  const [loading, setLoading] = useState(true);

  const handleNodeClick = useCallback((type: string, id: string) => {
    setDetail({ type, id });
  }, []);

  // Load data from API
  useEffect(() => {
    Promise.all([
      listAgents().catch(() => []),
      listTeams().catch(() => []),
      listWorkflows().catch(() => []),
    ]).then(([rawAgents, rawTeams, rawWorkflows]) => {
      const a = Array.isArray(rawAgents) ? rawAgents.map(apiAgentToNode) : [];
      const t = Array.isArray(rawTeams) ? rawTeams.map(apiTeamToNode) : [];
      const w = Array.isArray(rawWorkflows) ? rawWorkflows.map(apiWorkflowToNode) : [];
      setAgents(a);
      setTeams(t);
      setWorkflows(w);
      setLoading(false);
    });
  }, []);

  const { nodes: graphNodes, edges: graphEdges } = useMemo(
    () => buildGraph(agents, teams, workflows, handleNodeClick),
    [agents, teams, workflows, handleNodeClick],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Update nodes/edges when data loads
  useEffect(() => {
    if (!loading && graphNodes.length > 0) {
      setNodes(graphNodes);
      setEdges(graphEdges);
    }
  }, [graphNodes, graphEdges, loading, setNodes, setEdges]);

  const badge = `${agents.length} agentes · ${teams.length} teams · ${workflows.length} workflows`;

  return (
    <div style={{ width: "100%", height: "100vh", display: "flex", flexDirection: "column" }}>
      <PageHeader title="Topologia" badge={loading ? "Cargando..." : badge} />

      <div style={{ flex: 1, position: "relative" }}>
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Loader2 size={24} className="animate-spin mx-auto mb-3 text-zinc-500" />
              <p className="text-[13px] text-zinc-600">Cargando topologia desde AgentOS...</p>
            </div>
          </div>
        ) : (
          <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.3}
          maxZoom={2}
          defaultEdgeOptions={{ animated: false }}
          proOptions={{ hideAttribution: true }}
          style={{ background: "#09090b" }}
        >
          <Background color="#1a1a1e" gap={40} size={1} />
          <Controls
            showInteractive={false}
            className="!bg-[#0f0f12] !border-[#1e1e24] !rounded-xl !shadow-xl [&>button]:!bg-[#0f0f12] [&>button]:!border-[#1e1e24] [&>button]:!text-zinc-400 [&>button:hover]:!bg-zinc-800"
          />
          <MiniMap
            nodeColor={(n) => {
              if (n.type === "teamNode") return "#10b981";
              if (n.type === "agentNode") return "#27272a";
              if (n.type === "workflowNode") return "#8b5cf6";
              if (n.type === "mcpNode") return "#f59e0b";
              return "#333";
            }}
            maskColor="rgba(0,0,0,0.8)"
            className="!bg-[#0f0f12] !border-[#1e1e24] !rounded-xl"
          />
          </ReactFlow>
        )}

        {detail && (
          <DetailPanel
            type={detail.type}
            id={detail.id}
            onClose={() => setDetail(null)}
            agents={agents}
            teams={teams}
            workflows={workflows}
          />
        )}
      </div>
    </div>
  );
}
