"use client";

import { useState, useEffect } from "react";
import { BarChart3, RefreshCw, Loader2, Zap, Clock, Hash, Bot, Users, Workflow, TrendingUp } from "lucide-react";
import PageHeader from "@/components/layout/page-header";
import { getMetrics, refreshMetrics, listAgents, listTeams, listWorkflows, listTraces, listSessions, type Trace } from "@/lib/api";

function StatCard({ label, value, sub, icon: Icon, color }: { label: string; value: string; sub: string; icon: typeof Bot; color: string }) {
  return (
    <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[12px] text-zinc-500 font-medium">{label}</span>
        <div className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center`}><Icon size={14} className="text-white" /></div>
      </div>
      <div className="text-2xl font-semibold text-white tracking-tight">{value}</div>
      <div className="text-[11px] text-zinc-600 mt-1">{sub}</div>
    </div>
  );
}

function BarViz({ data, max }: { data: Array<{ label: string; value: number }>; max: number }) {
  return (
    <div className="space-y-2">
      {data.map((d) => (
        <div key={d.label} className="flex items-center gap-3">
          <span className="text-[11px] text-zinc-500 w-[120px] truncate text-right">{d.label}</span>
          <div className="flex-1 h-5 bg-zinc-900 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-600/60 rounded-full transition-all duration-500" style={{ width: `${max > 0 ? (d.value / max) * 100 : 0}%` }} />
          </div>
          <span className="text-[11px] text-zinc-400 w-[50px] text-right">{d.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<Record<string, unknown>>({});
  const [agentCount, setAgentCount] = useState(0);
  const [teamCount, setTeamCount] = useState(0);
  const [workflowCount, setWorkflowCount] = useState(0);
  const [sessionCount, setSessionCount] = useState(0);
  const [traces, setTraces] = useState<Trace[]>([]);

  function fetchAll() {
    setLoading(true);
    Promise.all([
      getMetrics().catch(() => ({})),
      listAgents().catch(() => []),
      listTeams().catch(() => []),
      listWorkflows().catch(() => []),
      listSessions().catch(() => []),
      listTraces(200).catch(() => []),
    ]).then(([m, a, t, w, s, tr]) => {
      setMetrics(m as Record<string, unknown>);
      setAgentCount(Array.isArray(a) ? a.length : 0);
      setTeamCount(Array.isArray(t) ? t.length : 0);
      setWorkflowCount(Array.isArray(w) ? w.length : 0);
      setSessionCount(Array.isArray(s) ? s.length : 0);
      setTraces(Array.isArray(tr) ? tr : []);
      setLoading(false);
    });
  }

  useEffect(() => { fetchAll(); }, []);

  // Compute analytics from traces
  const totalTokens = traces.reduce((sum, t) => sum + (t.tokens_in || 0) + (t.tokens_out || 0), 0);
  const avgDuration = traces.length > 0 ? Math.round(traces.reduce((sum, t) => sum + (t.duration_ms || 0), 0) / traces.length) : 0;
  const errorCount = traces.filter((t) => t.status === "error" || t.status === "failed").length;

  // Agent usage from traces
  const agentUsage: Record<string, number> = {};
  for (const t of traces) {
    const key = t.agent_id || t.team_id || "unknown";
    agentUsage[key] = (agentUsage[key] || 0) + 1;
  }
  const topAgents = Object.entries(agentUsage).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([label, value]) => ({ label, value }));
  const maxUsage = topAgents.length > 0 ? topAgents[0].value : 1;

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="Analytics" badge={loading ? "Cargando..." : `${traces.length} traces`}>
        <button onClick={() => { refreshMetrics().catch(() => {}); fetchAll(); }} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </PageHeader>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {loading && (
            <div className="text-center py-12"><Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /><span className="text-[13px] text-zinc-600">Cargando metricas...</span></div>
          )}

          {!loading && (
            <>
              {/* Top stats */}
              <div className="grid grid-cols-4 gap-4">
                <StatCard label="Agentes" value={String(agentCount)} sub="Registrados en AgentOS" icon={Bot} color="bg-emerald-600/20" />
                <StatCard label="Teams" value={String(teamCount)} sub={`${workflowCount} workflows`} icon={Users} color="bg-blue-600/20" />
                <StatCard label="Sesiones" value={String(sessionCount)} sub="Total historico" icon={Workflow} color="bg-violet-600/20" />
                <StatCard label="Traces" value={String(traces.length)} sub={`${errorCount} errores`} icon={Zap} color="bg-amber-600/20" />
              </div>

              {/* Token & performance stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-1 text-[11px] text-zinc-500"><Hash size={11} />Tokens Totales</div>
                  <div className="text-xl font-semibold text-white">{totalTokens.toLocaleString()}</div>
                  <div className="text-[11px] text-zinc-600 mt-1">
                    Costo estimado: ~${((totalTokens / 1_000_000) * 0.15).toFixed(4)}
                  </div>
                </div>
                <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-1 text-[11px] text-zinc-500"><Clock size={11} />Tiempo Promedio</div>
                  <div className="text-xl font-semibold text-white">{avgDuration > 1000 ? `${(avgDuration / 1000).toFixed(1)}s` : `${avgDuration}ms`}</div>
                  <div className="text-[11px] text-zinc-600 mt-1">Por request</div>
                </div>
                <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-1 text-[11px] text-zinc-500"><TrendingUp size={11} />Tasa de Exito</div>
                  <div className="text-xl font-semibold text-white">{traces.length > 0 ? `${(((traces.length - errorCount) / traces.length) * 100).toFixed(1)}%` : "--"}</div>
                  <div className="text-[11px] text-zinc-600 mt-1">{traces.length - errorCount} exitosos / {traces.length} total</div>
                </div>
              </div>

              {/* Agent usage chart */}
              <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-[14px] font-medium text-white">Uso por Agente/Team</h3>
                  <span className="text-[11px] text-zinc-600">Top 10</span>
                </div>
                {topAgents.length > 0 ? (
                  <BarViz data={topAgents} max={maxUsage} />
                ) : (
                  <p className="text-[13px] text-zinc-600 text-center py-4">Sin datos de uso todavia</p>
                )}
              </div>

              {/* Raw metrics from API */}
              {Object.keys(metrics).length > 0 && (
                <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
                  <h3 className="text-[14px] font-medium text-white mb-3">Metricas del Sistema (raw)</h3>
                  <pre className="text-[11px] text-zinc-400 font-mono overflow-x-auto max-h-[200px]">{JSON.stringify(metrics, null, 2)}</pre>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
