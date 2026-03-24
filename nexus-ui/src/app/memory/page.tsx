"use client";

import { useState, useEffect, useCallback } from "react";
import { Brain, Trash2, Loader2, RefreshCw, Tag, User, Clock } from "lucide-react";
import PageHeader from "@/components/layout/page-header";
import { listMemories, listMemoryTopics, deleteMemory, type Memory } from "@/lib/api";

function formatDate(ts?: number): string {
  if (!ts) return "";
  return new Date(ts * 1000).toLocaleDateString("es", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<string>("all");
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchData = useCallback(() => {
    setLoading(true);
    Promise.all([
      listMemories().catch(() => []),
      listMemoryTopics().catch(() => []),
    ]).then(([m, t]) => {
      setMemories(Array.isArray(m) ? m : []);
      setTopics(Array.isArray(t) ? t : []);
      setError("");
    }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  async function handleDelete(id: string) {
    setDeleting(id);
    try {
      await deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar");
    } finally {
      setDeleting(null);
    }
  }

  const filtered = filter === "all" ? memories : memories.filter((m) => m.topic === filter || m.memory_type === filter);

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="Memory" badge={`${memories.length} memorias`}>
        <button onClick={fetchData} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </PageHeader>

      {/* Filter tabs */}
      {topics.length > 0 && (
        <div className="px-6 py-3 flex gap-1.5 flex-wrap border-b border-[#1e1e24]">
          <button onClick={() => setFilter("all")} className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${filter === "all" ? "bg-white/[0.06] text-white" : "text-zinc-600 hover:text-zinc-400"}`}>
            Todas ({memories.length})
          </button>
          {topics.map((t) => (
            <button key={t} onClick={() => setFilter(t)} className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${filter === t ? "bg-white/[0.06] text-white" : "text-zinc-600 hover:text-zinc-400"}`}>
              {t}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-3xl mx-auto">
          {error && <div className="text-center text-red-400 text-[13px] bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-4">{error}</div>}
          {loading && memories.length === 0 && <div className="text-center py-12"><Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /><span className="text-[13px] text-zinc-600">Cargando memorias...</span></div>}

          {!loading && memories.length === 0 && !error && (
            <div className="text-center py-16">
              <Brain size={28} className="mx-auto mb-3 text-zinc-700" />
              <p className="text-[14px] text-zinc-500 mb-1">Sin memorias</p>
              <p className="text-[11px] text-zinc-700">Las memorias se crean automaticamente cuando los agentes aprenden sobre usuarios, entidades, y patrones.</p>
            </div>
          )}

          <div className="space-y-2">
            {filtered.map((mem) => (
              <div key={mem.id} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors group">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      {mem.memory_type && (
                        <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${
                          mem.memory_type === "user_profile" ? "bg-emerald-500/10 text-emerald-400" :
                          mem.memory_type === "entity" ? "bg-blue-500/10 text-blue-400" :
                          mem.memory_type === "learned_knowledge" ? "bg-violet-500/10 text-violet-400" :
                          "bg-zinc-800 text-zinc-400"
                        }`}>
                          {mem.memory_type}
                        </span>
                      )}
                      {mem.topic && <span className="text-[9px] text-zinc-600 bg-zinc-900 px-1.5 py-0.5 rounded flex items-center gap-0.5"><Tag size={8} />{mem.topic}</span>}
                      {mem.user_id && <span className="text-[9px] text-zinc-600 flex items-center gap-0.5"><User size={8} />{mem.user_id}</span>}
                    </div>
                    <p className="text-[13px] text-zinc-300 whitespace-pre-wrap leading-relaxed">
                      {mem.content || JSON.stringify(mem.metadata, null, 2)}
                    </p>
                    {mem.created_at && (
                      <div className="flex items-center gap-1 mt-2 text-[10px] text-zinc-700"><Clock size={9} />{formatDate(mem.created_at)}</div>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(mem.id)}
                    disabled={deleting === mem.id}
                    className="p-1.5 rounded-lg text-zinc-700 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all shrink-0"
                  >
                    {deleting === mem.id ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
