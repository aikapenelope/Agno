"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { BookOpen, Search, Upload, FileText, Loader2, RefreshCw, X, File } from "lucide-react";
import PageHeader from "@/components/layout/page-header";
import { listKnowledge, searchKnowledge, uploadKnowledge, type KnowledgeContent } from "@/lib/api";

function formatDate(ts?: number): string {
  if (!ts) return "";
  return new Date(ts * 1000).toLocaleDateString("es", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function KnowledgePage() {
  const [items, setItems] = useState<KnowledgeContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<unknown[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchKnowledge = useCallback(() => {
    setLoading(true);
    listKnowledge().then((d) => { setItems(Array.isArray(d) ? d : []); setError(""); }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchKnowledge(); }, [fetchKnowledge]);

  async function handleSearch() {
    if (!search.trim()) { setSearchResults(null); return; }
    setSearching(true);
    try {
      const results = await searchKnowledge(search.trim());
      setSearchResults(Array.isArray(results) ? results : []);
    } catch { setSearchResults([]); }
    finally { setSearching(false); }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadKnowledge(file);
      fetchKnowledge();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al subir");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="Knowledge Base" badge={`${items.length} documentos`}>
        <label className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400 text-[12px] font-medium hover:bg-emerald-600/20 transition-colors cursor-pointer ${uploading ? "opacity-50" : ""}`}>
          {uploading ? <Loader2 size={12} className="animate-spin" /> : <Upload size={12} />}
          Subir archivo
          <input ref={fileRef} type="file" accept=".pdf,.txt,.md,.csv,.json" onChange={handleUpload} className="hidden" disabled={uploading} />
        </label>
        <button onClick={fetchKnowledge} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </PageHeader>

      {/* Search */}
      <div className="px-6 py-3 flex gap-2">
        <div className="relative flex-1 max-w-lg">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSearch()} placeholder="Buscar en la knowledge base..." className="w-full bg-[#0f0f12] border border-[#1e1e24] rounded-lg pl-9 pr-3 py-2 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700 transition-colors" />
        </div>
        <button onClick={handleSearch} disabled={searching || !search.trim()} className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 text-[12px] hover:bg-zinc-700 disabled:opacity-40 transition-colors">
          {searching ? <Loader2 size={12} className="animate-spin" /> : "Buscar"}
        </button>
        {searchResults && <button onClick={() => setSearchResults(null)} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400"><X size={14} /></button>}
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6">
        <div className="max-w-3xl mx-auto">
          {error && <div className="text-center text-red-400 text-[13px] bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-4">{error}</div>}

          {/* Search results */}
          {searchResults && (
            <div className="mb-6">
              <h3 className="text-[13px] font-medium text-white mb-3">Resultados de busqueda ({searchResults.length})</h3>
              {searchResults.length === 0 ? (
                <p className="text-[13px] text-zinc-600">No se encontraron resultados para &quot;{search}&quot;</p>
              ) : (
                <div className="space-y-2">
                  {searchResults.map((r, i) => (
                    <div key={i} className="bg-[#0f0f12] border border-emerald-500/20 rounded-xl p-4">
                      <pre className="text-[11px] text-zinc-300 whitespace-pre-wrap overflow-x-auto max-h-[150px]">{typeof r === "string" ? r : JSON.stringify(r, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Document list */}
          {loading && items.length === 0 && <div className="text-center py-12"><Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /><span className="text-[13px] text-zinc-600">Cargando documentos...</span></div>}

          {!loading && items.length === 0 && !error && (
            <div className="text-center py-16">
              <BookOpen size={28} className="mx-auto mb-3 text-zinc-700" />
              <p className="text-[14px] text-zinc-500 mb-1">Knowledge base vacia</p>
              <p className="text-[11px] text-zinc-700">Sube archivos PDF, TXT, MD, CSV, o JSON. Tambien puedes agregar archivos en la carpeta knowledge/ del proyecto.</p>
            </div>
          )}

          <div className="space-y-2">
            {items.map((item) => (
              <div key={item.content_id} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center"><FileText size={14} className="text-blue-400" /></div>
                    <div>
                      <h3 className="text-[13px] font-medium text-white">{item.name || item.content_id}</h3>
                      <div className="flex items-center gap-2 text-[11px] text-zinc-600">
                        {item.content_type && <span>{item.content_type}</span>}
                        {item.source && <span>• {item.source}</span>}
                        {item.created_at && <span>• {formatDate(item.created_at)}</span>}
                      </div>
                    </div>
                  </div>
                  {item.status && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${item.status === "indexed" ? "bg-emerald-500/10 text-emerald-400" : "bg-zinc-800 text-zinc-500"}`}>
                      {item.status}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
