"use client";

import { useState, FormEvent } from "react";
import {
  Database,
  Users,
  Building2,
  Plus,
  Send,
  Loader2,
  Search,
  ClipboardList,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { runAgent } from "@/lib/api";

const QUICK_ACTIONS = [
  { label: "Listar contactos recientes", icon: Users, prompt: "Lista los contactos mas recientes del CRM" },
  { label: "Listar empresas", icon: Building2, prompt: "Lista todas las empresas registradas en el CRM" },
  { label: "Actividad reciente", icon: ClipboardList, prompt: "Muestra la actividad reciente del CRM: notas, tareas, interacciones" },
  { label: "Agregar contacto", icon: Plus, prompt: "Quiero agregar un nuevo contacto al CRM. Pideme los datos." },
];

interface CrmMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function CrmPage() {
  const [messages, setMessages] = useState<CrmMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `crm-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    setMessages((p) => [...p, { id: `u-${Date.now()}`, role: "user", content: msg, timestamp: new Date() }]);
    setInput("");
    setLoading(true);

    try {
      const data = await runAgent("Automation Agent", msg, sessionId);
      const content = typeof data.content === "string" ? data.content : JSON.stringify(data);
      setMessages((p) => [...p, { id: `a-${Date.now()}`, role: "assistant", content, timestamp: new Date() }]);
    } catch (err) {
      setMessages((p) => [...p, { id: `e-${Date.now()}`, role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Fallo"}`, timestamp: new Date() }]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    send();
  }

  return (
    <div className="h-full flex flex-col">
      <header className="h-14 flex items-center justify-between px-6 border-b border-[#1e1e24] shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-[15px] font-medium text-white">CRM</h2>
          <span className="text-[11px] text-zinc-600 bg-zinc-900 px-2 py-0.5 rounded-full">
            Twenty via Automation Agent
          </span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar: quick actions */}
        <div className="w-[260px] border-r border-[#1e1e24] bg-[#0c0c0f] p-4 flex flex-col gap-2">
          <div className="text-[11px] text-zinc-600 font-medium uppercase tracking-wider mb-2">
            Acciones rapidas
          </div>
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.label}
              onClick={() => send(action.prompt)}
              disabled={loading}
              className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-[#0f0f12] border border-[#1e1e24] text-[12px] text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 disabled:opacity-40 transition-colors text-left"
            >
              <action.icon size={14} className="text-zinc-600 shrink-0" />
              {action.label}
            </button>
          ))}

          <div className="mt-auto pt-4 border-t border-[#1e1e24]">
            <div className="text-[10px] text-zinc-700 leading-relaxed">
              Los datos vienen de Twenty CRM via el Automation Agent y sus MCP tools (n8n + Twenty).
            </div>
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-zinc-600 text-[13px] mt-16">
                <Database size={28} className="mx-auto mb-3 text-zinc-700" />
                <p className="mb-1">Interfaz CRM via Automation Agent</p>
                <p className="text-[11px] text-zinc-700">
                  Usa las acciones rapidas o escribe lo que necesitas del CRM.
                </p>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-xl px-4 py-3 ${msg.role === "user" ? "bg-emerald-600/15 border border-emerald-500/20" : "bg-[#0f0f12] border border-[#1e1e24]"}`}>
                  <div className="agent-response text-[13px] text-zinc-300 leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-zinc-500 text-[12px]">
                <Loader2 size={14} className="animate-spin text-emerald-400" /> Consultando CRM...
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="px-6 pb-5 pt-2">
            <div className="flex items-center gap-2 bg-[#0f0f12] border border-[#1e1e24] rounded-xl px-4 py-2.5 focus-within:border-zinc-700 transition-colors">
              <Search size={14} className="text-zinc-600 shrink-0" />
              <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Buscar contactos, empresas, o pedir acciones..." className="flex-1 bg-transparent text-[13px] text-white placeholder-zinc-600 outline-none" disabled={loading} />
              <button type="submit" disabled={loading || !input.trim()} className="p-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                <Send size={13} />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
