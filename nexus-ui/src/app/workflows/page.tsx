"use client";

import { useState, useEffect } from "react";
import {
  Play,
  Loader2,
  Workflow,
  ChevronDown,
  ChevronUp,
  X,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { listWorkflows, runWorkflow, type WorkflowInfo } from "@/lib/api";
import PageHeader from "@/components/layout/page-header";

/* ------------------------------------------------------------------ */
/* Static descriptions (AgentOS may not return these)                   */
/* ------------------------------------------------------------------ */

const WORKFLOW_META: Record<string, { steps: string; icon: string }> = {
  "deep-research": {
    steps: "Plan → Parallel scouts → Quality gate → Report",
    icon: "🔍",
  },
  "content-production": {
    steps: "Trend → Compact → Script → Creative review",
    icon: "📝",
  },
  "client-research": {
    steps: "Parallel(web + knowledge) → Synthesis",
    icon: "🏢",
  },
  "seo-content": {
    steps: "Keyword → Article → Audit loop",
    icon: "📈",
  },
  "social-media-autopilot": {
    steps: "Trend → Parallel(IG/TW/LI) → Audit",
    icon: "📱",
  },
  "competitor-intelligence": {
    steps: "Parallel(3 scouts) → Synthesis",
    icon: "🎯",
  },
  "media-generation": {
    steps: "Router(image vs video) → Generation",
    icon: "🎨",
  },
};

/* ------------------------------------------------------------------ */
/* Run dialog                                                          */
/* ------------------------------------------------------------------ */

function RunDialog({
  workflow,
  onClose,
}: {
  workflow: WorkflowInfo;
  onClose: () => void;
}) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState(
    () => `wf-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
  );

  const wfId = workflow.workflow_id || workflow.name;
  const meta = WORKFLOW_META[wfId] || WORKFLOW_META[workflow.name];

  async function run() {
    if (!input.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await runWorkflow(wfId, input.trim(), sessionId);
      const content =
        typeof data.content === "string"
          ? data.content
          : ((data.content as Record<string, unknown>)?.text as string) ||
            JSON.stringify(data, null, 2);
      setResult(content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div className="bg-[#0c0c0f] border border-[#1e1e24] rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e1e24] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
              <span className="text-sm">{meta?.icon || "⚡"}</span>
            </div>
            <div>
              <h3 className="text-[14px] font-medium text-white">
                {workflow.name}
              </h3>
              {meta && (
                <p className="text-[11px] text-zinc-600">{meta.steps}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Input */}
        <div className="px-6 py-4 border-b border-[#1e1e24] shrink-0">
          <label className="text-[12px] text-zinc-500 mb-2 block">
            Describe lo que quieres investigar o producir:
          </label>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ej: Investiga las tendencias de AI agents en Latam para Q2 2026..."
            rows={3}
            className="w-full bg-[#0f0f12] border border-[#1e1e24] rounded-xl px-4 py-3 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700 transition-colors resize-none"
            disabled={loading}
          />
          <button
            onClick={run}
            disabled={loading || !input.trim()}
            className="mt-3 flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-[13px] font-medium hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Ejecutando...
              </>
            ) : (
              <>
                <Play size={14} />
                Ejecutar Workflow
              </>
            )}
          </button>
        </div>

        {/* Result */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="text-red-400 text-[13px] bg-red-500/10 border border-red-500/20 rounded-xl p-4">
              {error}
            </div>
          )}
          {result && (
            <div className="agent-response text-[13px] text-zinc-300 leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {result}
              </ReactMarkdown>
            </div>
          )}
          {!result && !error && !loading && (
            <div className="text-center text-zinc-600 text-[13px] py-8">
              Escribe tu consulta y ejecuta el workflow.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Workflow card                                                        */
/* ------------------------------------------------------------------ */

function WorkflowCard({
  workflow,
  onRun,
}: {
  workflow: WorkflowInfo;
  onRun: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const wfId = workflow.workflow_id || workflow.name;
  const meta = WORKFLOW_META[wfId] || WORKFLOW_META[workflow.name];

  return (
    <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl hover:border-zinc-700/50 transition-colors">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-violet-500/10 flex items-center justify-center shrink-0">
            <span className="text-sm">{meta?.icon || "⚡"}</span>
          </div>
          <div className="min-w-0">
            <h3 className="text-[13px] font-medium text-white">
              {workflow.name}
            </h3>
            <p className="text-[11px] text-zinc-600 truncate">
              {workflow.description || meta?.steps || "Workflow"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-3">
          <button
            onClick={onRun}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400 text-[12px] font-medium hover:bg-emerald-600/20 transition-colors"
          >
            <Play size={12} />
            Ejecutar
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {expanded && meta && (
        <div className="px-4 pb-4 pt-0">
          <div className="bg-[#0a0a0c] rounded-lg p-3 border border-[#1a1a1e]">
            <div className="text-[11px] text-zinc-500 mb-1.5 font-medium uppercase tracking-wider">
              Pipeline
            </div>
            <div className="text-[12px] text-zinc-400 font-mono">
              {meta.steps}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Workflows page                                                      */
/* ------------------------------------------------------------------ */

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowInfo[]>([]);
  const [running, setRunning] = useState<WorkflowInfo | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listWorkflows()
      .then((data) => setWorkflows(Array.isArray(data) ? data : []))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <PageHeader title="Workflows" />

      {/* List */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-3">
          {error && (
            <div className="text-center text-red-400 text-[13px] py-8">
              {error}
            </div>
          )}
          {!error && workflows.length === 0 && (
            <div className="text-center text-zinc-600 text-[13px] py-12">
              <Loader2
                size={20}
                className="animate-spin mx-auto mb-3 text-zinc-500"
              />
              Cargando workflows...
            </div>
          )}
          {workflows.map((wf) => (
            <WorkflowCard
              key={wf.workflow_id || wf.name}
              workflow={wf}
              onRun={() => setRunning(wf)}
            />
          ))}

          {/* Static fallback if API returns empty */}
          {!error && workflows.length === 0 && (
            <div className="space-y-3 mt-4">
              {Object.entries(WORKFLOW_META).map(([id, meta]) => (
                <WorkflowCard
                  key={id}
                  workflow={{ name: id, id: id, workflow_id: id, description: meta.steps }}
                  onRun={() =>
                    setRunning({ name: id, id: id, workflow_id: id, description: meta.steps })
                  }
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Run dialog */}
      {running && (
        <RunDialog workflow={running} onClose={() => setRunning(null)} />
      )}
    </div>
  );
}
