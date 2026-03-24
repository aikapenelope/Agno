"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Clock,
  MessageSquare,
  ChevronRight,
  ArrowLeft,
  Loader2,
  RefreshCw,
  Bot,
  User,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import PageHeader from "@/components/layout/page-header";
import {
  listSessions,
  getSessionRuns,
  type SessionInfo,
  type SessionRun,
} from "@/lib/api";

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function formatDate(ts?: number): string {
  if (!ts) return "";
  const d = new Date(ts * 1000);
  return d.toLocaleDateString("es", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function timeAgo(ts?: number): string {
  if (!ts) return "";
  const diff = Math.floor(Date.now() / 1000 - ts);
  if (diff < 60) return "ahora";
  if (diff < 3600) return `hace ${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)}h`;
  return `hace ${Math.floor(diff / 86400)}d`;
}

/* ------------------------------------------------------------------ */
/* Session detail (runs/messages)                                      */
/* ------------------------------------------------------------------ */

function SessionDetail({
  session,
  onBack,
}: {
  session: SessionInfo;
  onBack: () => void;
}) {
  const [runs, setRuns] = useState<SessionRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    getSessionRuns(session.session_id)
      .then((data) => setRuns(Array.isArray(data) ? data : []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [session.session_id]);

  return (
    <div className="h-full flex flex-col">
      <div className="h-14 flex items-center gap-3 px-6 border-b border-[#1e1e24] shrink-0">
        <button
          onClick={onBack}
          className="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-colors"
        >
          <ArrowLeft size={16} />
        </button>
        <div>
          <h2 className="text-[14px] font-medium text-white truncate max-w-[400px]">
            {session.session_id}
          </h2>
          <div className="flex items-center gap-3 text-[11px] text-zinc-600">
            {session.team_id && <span>Team: {session.team_id}</span>}
            {session.agent_id && <span>Agent: {session.agent_id}</span>}
            {session.created_at && <span>{formatDate(session.created_at)}</span>}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {loading && (
            <div className="text-center py-12">
              <Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" />
              <span className="text-[13px] text-zinc-600">Cargando mensajes...</span>
            </div>
          )}

          {error && (
            <div className="text-center text-red-400 text-[13px] py-8">{error}</div>
          )}

          {!loading && runs.length === 0 && (
            <div className="text-center text-zinc-600 text-[13px] py-12">
              No hay mensajes en esta sesion.
            </div>
          )}

          {runs.map((run) => (
            <div key={run.run_id} className="space-y-3">
              {/* User input */}
              {run.input && (
                <div className="flex justify-end">
                  <div className="max-w-[70%] bg-emerald-600/15 border border-emerald-500/20 rounded-2xl rounded-br-md px-4 py-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <User size={10} className="text-zinc-500" />
                      <span className="text-[10px] text-zinc-500">Usuario</span>
                    </div>
                    <p className="text-[13px] text-zinc-200 whitespace-pre-wrap">
                      {run.input}
                    </p>
                  </div>
                </div>
              )}

              {/* Agent output */}
              {(run.output || run.content) && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-lg bg-[#141418] border border-[#1e1e24] flex items-center justify-center shrink-0 mt-0.5">
                    <Bot size={12} className="text-emerald-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    {run.agent_name && (
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-[11px] font-medium text-emerald-400">
                          {run.agent_name}
                        </span>
                        {run.created_at && (
                          <span className="text-[10px] text-zinc-600">
                            {formatDate(run.created_at)}
                          </span>
                        )}
                      </div>
                    )}
                    <div className="agent-response text-[13px] text-zinc-300 leading-relaxed bg-[#0f0f12] border border-[#1e1e24] rounded-xl px-4 py-3">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {(run.output || run.content) as string}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Session list                                                        */
/* ------------------------------------------------------------------ */

function SessionCard({
  session,
  onClick,
}: {
  session: SessionInfo;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 hover:bg-[#111115] transition-all duration-150 group"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-zinc-800/50 flex items-center justify-center shrink-0">
            <MessageSquare size={14} className="text-zinc-500" />
          </div>
          <div className="min-w-0">
            <div className="text-[13px] font-medium text-white truncate max-w-[350px] group-hover:text-emerald-400 transition-colors">
              {session.session_id}
            </div>
            <div className="flex items-center gap-3 text-[11px] text-zinc-600 mt-0.5">
              {session.team_id && (
                <span className="bg-zinc-900 px-1.5 py-0.5 rounded text-[10px]">
                  {session.team_id}
                </span>
              )}
              {session.agent_id && (
                <span className="bg-zinc-900 px-1.5 py-0.5 rounded text-[10px]">
                  {session.agent_id}
                </span>
              )}
              {session.updated_at && (
                <span className="flex items-center gap-1">
                  <Clock size={9} />
                  {timeAgo(session.updated_at)}
                </span>
              )}
            </div>
          </div>
        </div>
        <ChevronRight
          size={14}
          className="text-zinc-700 group-hover:text-zinc-500 transition-colors shrink-0"
        />
      </div>
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* History page                                                        */
/* ------------------------------------------------------------------ */

export default function HistoryPage() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [selected, setSelected] = useState<SessionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchSessions = useCallback(() => {
    setLoading(true);
    listSessions()
      .then((data) => {
        const list = Array.isArray(data) ? data : [];
        // Sort by updated_at descending
        list.sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0));
        setSessions(list);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  if (selected) {
    return <SessionDetail session={selected} onBack={() => setSelected(null)} />;
  }

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="Historial" badge={`${sessions.length} sesiones`}>
        <button
          onClick={fetchSessions}
          className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors"
          title="Actualizar"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </PageHeader>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-2">
          {error && (
            <div className="text-center text-red-400 text-[13px] bg-red-500/10 border border-red-500/20 rounded-xl p-4">
              {error}
            </div>
          )}

          {loading && sessions.length === 0 && (
            <div className="text-center py-12">
              <Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" />
              <span className="text-[13px] text-zinc-600">Cargando sesiones...</span>
            </div>
          )}

          {!loading && !error && sessions.length === 0 && (
            <div className="text-center py-16">
              <div className="w-14 h-14 rounded-2xl bg-zinc-800/50 flex items-center justify-center mx-auto mb-4">
                <Clock size={24} className="text-zinc-600" />
              </div>
              <p className="text-[14px] text-zinc-500 mb-1">No hay sesiones</p>
              <p className="text-[11px] text-zinc-700">
                Las sesiones aparecen cuando chateas con NEXUS o ejecutas workflows.
              </p>
            </div>
          )}

          {sessions.map((session) => (
            <SessionCard
              key={session.session_id}
              session={session}
              onClick={() => setSelected(session)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
