"use client";

import { useState, useEffect, FormEvent } from "react";
import {
  Bot,
  Search,
  Send,
  ArrowLeft,
  Wrench,
  MessageSquare,
  Loader2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { listAgents, runAgent, type AgentInfo } from "@/lib/api";
import PageHeader from "@/components/layout/page-header";

/* ------------------------------------------------------------------ */
/* Agent Card                                                          */
/* ------------------------------------------------------------------ */

function AgentCard({
  agent,
  onClick,
}: {
  agent: AgentInfo;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="text-left bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 hover:bg-[#111115] transition-all duration-150 group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="w-9 h-9 rounded-lg bg-emerald-500/10 flex items-center justify-center">
          <Bot size={16} className="text-emerald-400" />
        </div>
        <div className="w-2 h-2 rounded-full bg-emerald-500" title="Activo" />
      </div>
      <h3 className="text-[13px] font-medium text-white mb-1 group-hover:text-emerald-400 transition-colors">
        {agent.name}
      </h3>
      <p className="text-[11px] text-zinc-600 line-clamp-2 leading-relaxed">
        {agent.role || agent.description || "Agente especializado"}
      </p>
      {(agent.model?.model || agent.model?.name) && (
        <div className="mt-3 text-[10px] text-zinc-700 bg-zinc-900/50 px-2 py-0.5 rounded inline-block">
          {agent.model.model || agent.model.name}
        </div>
      )}
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* Agent Detail + Direct Chat                                          */
/* ------------------------------------------------------------------ */

interface ChatMsg {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

function AgentDetail({
  agent,
  onBack,
}: {
  agent: AgentInfo;
  onBack: () => void;
}) {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(
    () => `agent-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
  );

  async function send(e: FormEvent) {
    e.preventDefault();
    const msg = input.trim();
    if (!msg || loading) return;

    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: "user", content: msg, timestamp: new Date() },
    ]);
    setInput("");
    setLoading(true);

    try {
      const data = await runAgent(agent.id || agent.name, msg, sessionId);
      const content =
        typeof data.content === "string"
          ? data.content
          : ((data.content as Record<string, unknown>)?.text as string) ||
            JSON.stringify(data);

      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: "assistant", content, timestamp: new Date() },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Fallo"}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="h-14 flex items-center gap-3 px-6 border-b border-[#1e1e24] shrink-0">
        <button
          onClick={onBack}
          className="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-colors"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
          <Bot size={14} className="text-emerald-400" />
        </div>
        <div>
          <h2 className="text-[14px] font-medium text-white">{agent.name}</h2>
          <p className="text-[11px] text-zinc-600">
            {agent.role || "Agente especializado"}
          </p>
        </div>
      </div>

      {/* Info bar */}
      <div className="px-6 py-3 border-b border-[#1e1e24] flex gap-4">
        {(agent.model?.model || agent.model?.name) && (
          <div className="flex items-center gap-1.5 text-[11px] text-zinc-500">
            <Bot size={11} />
            <span>{agent.model.model || agent.model.name}</span>
          </div>
        )}
        {agent.tools && agent.tools.length > 0 && (
          <div className="flex items-center gap-1.5 text-[11px] text-zinc-500">
            <Wrench size={11} />
            <span>{agent.tools.length} tools</span>
          </div>
        )}
        <div className="flex items-center gap-1.5 text-[11px] text-zinc-500">
          <MessageSquare size={11} />
          <span>Chat directo (sin routing)</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-zinc-600 text-[13px] mt-12">
            Habla directamente con <span className="text-emerald-400">{agent.name}</span>.
            <br />
            <span className="text-[11px] text-zinc-700">
              Sin routing de NEXUS — va directo al agente.
            </span>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-emerald-600/15 border border-emerald-500/20"
                  : "bg-[#0f0f12] border border-[#1e1e24]"
              }`}
            >
              <div className="agent-response text-[13px] text-zinc-300 leading-relaxed">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-zinc-500 text-[12px]">
            <Loader2 size={14} className="animate-spin text-emerald-400" />
            Procesando...
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={send}
        className="px-6 pb-5 pt-2"
      >
        <div className="flex items-center gap-2 bg-[#0f0f12] border border-[#1e1e24] rounded-xl px-4 py-2.5 focus-within:border-zinc-700 transition-colors">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Mensaje para ${agent.name}...`}
            className="flex-1 bg-transparent text-[13px] text-white placeholder-zinc-600 outline-none"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={13} />
          </button>
        </div>
      </form>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Agents page                                                         */
/* ------------------------------------------------------------------ */

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<AgentInfo | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listAgents()
      .then((data) => {
        const list = Array.isArray(data) ? data : [];
        setAgents(list);
      })
      .catch((err) => setError(err.message));
  }, []);

  const filtered = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      (a.role || "").toLowerCase().includes(search.toLowerCase()),
  );

  if (selected) {
    return <AgentDetail agent={selected} onBack={() => setSelected(null)} />;
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <PageHeader title="Agentes" badge={`${agents.length} registrados`} />

      {/* Search */}
      <div className="px-6 py-4">
        <div className="relative max-w-md">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar agente..."
            className="w-full bg-[#0f0f12] border border-[#1e1e24] rounded-lg pl-9 pr-3 py-2 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700 transition-colors"
          />
        </div>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto px-6 pb-6">
        {error && (
          <div className="text-center text-red-400 text-[13px] py-8">
            {error}
            <br />
            <span className="text-[11px] text-zinc-600">
              Verifica que AgentOS esta corriendo
            </span>
          </div>
        )}
        {!error && filtered.length === 0 && agents.length === 0 && (
          <div className="text-center text-zinc-600 text-[13px] py-12">
            <Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" />
            Cargando agentes...
          </div>
        )}
        <div className="grid grid-cols-3 gap-3">
          {filtered.map((agent) => (
            <AgentCard
              key={agent.id || agent.name}
              agent={agent}
              onClick={() => setSelected(agent)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
