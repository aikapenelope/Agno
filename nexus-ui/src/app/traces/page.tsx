"use client";

import { useState, useEffect, useCallback } from "react";
import { Clock, Bot, Wrench, Zap, ChevronRight, ArrowLeft, RefreshCw, Loader2, Search, Hash, Timer } from "lucide-react";
import PageHeader from "@/components/layout/page-header";
import { listTraces, getTrace, type Trace } from "@/lib/api";

function formatDuration(ms?: number): string {
  if (!ms) return "--";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatDate(ts?: number): string {
  if (!ts) return "";
  return new Date(ts * 1000).toLocaleString("es", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function statusColor(s?: string): string {
  if (s === "success" || s === "completed") return "bg-emerald-500";
  if (s === "error" || s === "failed") return "bg-red-500";
  if (s === "running") return "bg-amber-500 animate-pulse";
  return "bg-zinc-600";
}

/* Trace detail */
function TraceDetail({ traceId, onBack }: { traceId: string; onBack: () => void }) {
  const [trace, setTrace] = useState<Trace | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getTrace(traceId).then((d) => setTrace(d)).catch(() => {}).finally(() => setLoading(false));
  }, [traceId]);

  if (loading) return <div className="flex items-center justify-center h-full"><Loader2 size={20} className="animate-spin text-zinc-500" /></div>;
  if (!trace) return <div className="text-center text-zinc-600 py-12">Trace no encontrado</div>;

  return (
    <div className="h-full flex flex-col">
      <div className="h-14 flex items-center gap-3 px-6 border-b border-[#1e1e24] shrink-0">
        <button onClick={onBack} className="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-colors"><ArrowLeft size={16} /></button>
        <div>
          <h2 className="text-[14px] font-medium text-white font-mono">{trace.trace_id.slice(0, 12)}...</h2>
          <div className="flex items-center gap-2 text-[11px] text-zinc-600">
            {trace.agent_id && <span>Agent: {trace.agent_id}</span>}
            {trace.team_id && <span>Team: {trace.team_id}</span>}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: "Duracion", value: formatDuration(trace.duration_ms), icon: Timer },
              { label: "Tokens In", value: trace.tokens_in?.toLocaleString() || "--", icon: Hash },
              { label: "Tokens Out", value: trace.tokens_out?.toLocaleString() || "--", icon: Hash },
              { label: "Estado", value: trace.status || "unknown", icon: Zap },
            ].map((s) => (
              <div key={s.label} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-3">
                <div className="flex items-center gap-1.5 text-[10px] text-zinc-600 mb-1"><s.icon size={10} />{s.label}</div>
                <div className="text-[15px] font-medium text-white">{s.value}</div>
              </div>
            ))}
          </div>

          {/* Input */}
          {trace.input && (
            <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4">
              <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Input</div>
              <p className="text-[13px] text-zinc-300 whitespace-pre-wrap">{trace.input}</p>
            </div>
          )}

          {/* Tool calls */}
          {trace.tool_calls && trace.tool_calls.length > 0 && (
            <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4">
              <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-3">Tool Calls ({trace.tool_calls.length})</div>
              <div className="space-y-2">
                {trace.tool_calls.map((tc, i) => (
                  <div key={i} className="flex items-center justify-between bg-zinc-900/50 rounded-lg px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Wrench size={11} className="text-zinc-500" />
                      <span className="text-[12px] text-zinc-300 font-mono">{tc.name}</span>
                    </div>
                    <span className="text-[11px] text-zinc-600">{formatDuration(tc.duration_ms)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Output */}
          {trace.output && (
            <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4">
              <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Output</div>
              <p className="text-[13px] text-zinc-300 whitespace-pre-wrap max-h-[300px] overflow-y-auto">{trace.output}</p>
            </div>
          )}

          {/* Metadata */}
          {trace.metadata && Object.keys(trace.metadata).length > 0 && (
            <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4">
              <div className="text-[10px] text-zinc-600 uppercase tracking-wider mb-2">Metadata</div>
              <pre className="text-[11px] text-zinc-400 font-mono overflow-x-auto">{JSON.stringify(trace.metadata, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* Traces page */
export default function TracesPage() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const fetchTraces = useCallback(() => {
    setLoading(true);
    listTraces(100).then((d) => { setTraces(Array.isArray(d) ? d : []); setError(""); }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchTraces(); }, [fetchTraces]);

  if (selected) return <TraceDetail traceId={selected} onBack={() => setSelected(null)} />;

  const filtered = traces.filter((t) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (t.trace_id || "").toLowerCase().includes(s) || (t.agent_id || "").toLowerCase().includes(s) || (t.team_id || "").toLowerCase().includes(s) || (t.input || "").toLowerCase().includes(s);
  });

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="Traces" badge={`${traces.length} registrados`}>
        <button onClick={fetchTraces} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors"><RefreshCw size={14} className={loading ? "animate-spin" : ""} /></button>
      </PageHeader>

      <div className="px-6 py-3">
        <div className="relative max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar por agente, team, o contenido..." className="w-full bg-[#0f0f12] border border-[#1e1e24] rounded-lg pl-9 pr-3 py-2 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700 transition-colors" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6">
        <div className="max-w-4xl mx-auto">
          {error && <div className="text-center text-red-400 text-[13px] py-4">{error}</div>}
          {loading && traces.length === 0 && <div className="text-center py-12"><Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /><span className="text-[13px] text-zinc-600">Cargando traces...</span></div>}
          {!loading && !error && filtered.length === 0 && <div className="text-center py-16"><Clock size={28} className="mx-auto mb-3 text-zinc-700" /><p className="text-[14px] text-zinc-500">No hay traces</p><p className="text-[11px] text-zinc-700">Los traces aparecen cuando los agentes procesan requests.</p></div>}

          <div className="space-y-1.5">
            {filtered.map((t) => (
              <button key={t.trace_id} onClick={() => setSelected(t.trace_id)} className="w-full text-left bg-[#0f0f12] border border-[#1e1e24] rounded-xl px-4 py-3 hover:border-zinc-700/50 transition-all group">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${statusColor(t.status)}`} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-[12px] font-mono text-zinc-400">{t.trace_id.slice(0, 10)}...</span>
                        {t.agent_id && <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">{t.agent_id}</span>}
                        {t.team_id && <span className="text-[10px] text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded">{t.team_id}</span>}
                      </div>
                      {t.input && <p className="text-[11px] text-zinc-600 truncate max-w-[500px]">{t.input}</p>}
                    </div>
                  </div>
                  <div className="flex items-center gap-4 shrink-0 ml-3">
                    {t.duration_ms && <span className="text-[11px] text-zinc-500 flex items-center gap-1"><Timer size={10} />{formatDuration(t.duration_ms)}</span>}
                    {(t.tokens_in || t.tokens_out) && <span className="text-[10px] text-zinc-600">{((t.tokens_in || 0) + (t.tokens_out || 0)).toLocaleString()} tok</span>}
                    {t.created_at && <span className="text-[10px] text-zinc-700">{formatDate(t.created_at)}</span>}
                    <ChevronRight size={12} className="text-zinc-700 group-hover:text-zinc-500" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
