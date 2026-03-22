"use client";

import { useState } from "react";
import {
  Smartphone,
  Search,
  Send,
  User,
  Clock,
  Filter,
  MessageSquare,
} from "lucide-react";
import { runTeam } from "@/lib/api";
import PageHeader from "@/components/layout/page-header";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface Conversation {
  id: string;
  phone: string;
  name: string;
  product: "whabi" | "docflow" | "aurora" | "general";
  lastMessage: string;
  timestamp: string;
  status: "active" | "waiting" | "resolved";
  unread: number;
}

/* ------------------------------------------------------------------ */
/* Mock data (real data comes from GET /sessions?team_id=whatsapp-support) */
/* ------------------------------------------------------------------ */

const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: "1",
    phone: "+57 300 123 4567",
    name: "Clinica Norte",
    product: "docflow",
    lastMessage: "Necesito ayuda con la historia clinica del paciente",
    timestamp: "14:32",
    status: "active",
    unread: 2,
  },
  {
    id: "2",
    phone: "+57 311 987 6543",
    name: "Maria Lopez",
    product: "whabi",
    lastMessage: "Como configuro las campanas automaticas?",
    timestamp: "13:15",
    status: "waiting",
    unread: 0,
  },
  {
    id: "3",
    phone: "+57 320 555 1234",
    name: "TechStart SAS",
    product: "aurora",
    lastMessage: "La app de voz no reconoce comandos en español",
    timestamp: "12:40",
    status: "active",
    unread: 1,
  },
  {
    id: "4",
    phone: "+57 315 222 3333",
    name: "Dr. Rodriguez",
    product: "docflow",
    lastMessage: "Gracias, ya quedo resuelto",
    timestamp: "11:20",
    status: "resolved",
    unread: 0,
  },
];

const PRODUCT_COLORS: Record<string, string> = {
  whabi: "bg-green-500/10 text-green-400",
  docflow: "bg-blue-500/10 text-blue-400",
  aurora: "bg-violet-500/10 text-violet-400",
  general: "bg-zinc-800 text-zinc-400",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-emerald-500",
  waiting: "bg-amber-500",
  resolved: "bg-zinc-600",
};

/* ------------------------------------------------------------------ */
/* Conversation list                                                   */
/* ------------------------------------------------------------------ */

function ConversationList({
  conversations,
  selected,
  onSelect,
  filter,
  onFilterChange,
  search,
  onSearchChange,
}: {
  conversations: Conversation[];
  selected: string | null;
  onSelect: (id: string) => void;
  filter: string;
  onFilterChange: (f: string) => void;
  search: string;
  onSearchChange: (s: string) => void;
}) {
  return (
    <div className="w-[340px] h-full flex flex-col border-r border-[#1e1e24] bg-[#0c0c0f]">
      {/* Search */}
      <div className="p-3 border-b border-[#1e1e24]">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Buscar conversacion..."
            className="w-full bg-[#0f0f12] border border-[#1e1e24] rounded-lg pl-9 pr-3 py-2 text-[12px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700 transition-colors"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-1 px-3 py-2 border-b border-[#1e1e24]">
        {["all", "whabi", "docflow", "aurora"].map((f) => (
          <button
            key={f}
            onClick={() => onFilterChange(f)}
            className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-colors ${
              filter === f
                ? "bg-white/[0.06] text-white"
                : "text-zinc-600 hover:text-zinc-400"
            }`}
          >
            {f === "all" ? "Todos" : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.map((conv) => (
          <button
            key={conv.id}
            onClick={() => onSelect(conv.id)}
            className={`w-full text-left px-4 py-3 border-b border-[#1e1e24] hover:bg-white/[0.02] transition-colors ${
              selected === conv.id ? "bg-white/[0.04]" : ""
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${STATUS_COLORS[conv.status]}`} />
                <span className="text-[13px] font-medium text-white">{conv.name}</span>
              </div>
              <span className="text-[10px] text-zinc-600">{conv.timestamp}</span>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-[11px] text-zinc-500 truncate max-w-[220px]">{conv.lastMessage}</p>
              <div className="flex items-center gap-2">
                <span className={`text-[9px] px-1.5 py-0.5 rounded ${PRODUCT_COLORS[conv.product]}`}>
                  {conv.product}
                </span>
                {conv.unread > 0 && (
                  <span className="min-w-[16px] h-[16px] flex items-center justify-center rounded-full bg-emerald-500 text-[9px] font-bold text-white px-1">
                    {conv.unread}
                  </span>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Conversation thread                                                 */
/* ------------------------------------------------------------------ */

function ConversationThread({ conversation }: { conversation: Conversation }) {
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [agentPreview, setAgentPreview] = useState<string | null>(null);

  async function previewResponse() {
    if (!reply.trim()) return;
    setSending(true);
    try {
      const data = await runTeam("whatsapp-support", reply.trim(), `wa-${conversation.id}`);
      const content = typeof data.content === "string" ? data.content : JSON.stringify(data);
      setAgentPreview(content);
    } catch {
      setAgentPreview("Error al generar preview");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-6 border-b border-[#1e1e24] shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
            <User size={14} className="text-zinc-400" />
          </div>
          <div>
            <div className="text-[13px] font-medium text-white">{conversation.name}</div>
            <div className="text-[11px] text-zinc-600">{conversation.phone}</div>
          </div>
        </div>
        <span className={`text-[10px] px-2 py-0.5 rounded ${PRODUCT_COLORS[conversation.product]}`}>
          {conversation.product}
        </span>
      </div>

      {/* Messages placeholder */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="text-center text-zinc-700 text-[12px] py-8">
          <MessageSquare size={24} className="mx-auto mb-3 text-zinc-700" />
          Historial de conversacion
          <br />
          <span className="text-[11px]">
            Conecta WhatsApp para ver mensajes en tiempo real
          </span>
        </div>

        {/* Last message */}
        <div className="flex justify-start mt-4">
          <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl px-4 py-3 max-w-[80%]">
            <p className="text-[13px] text-zinc-300">{conversation.lastMessage}</p>
            <span className="text-[10px] text-zinc-600 mt-1 block">{conversation.timestamp}</span>
          </div>
        </div>

        {/* Agent preview */}
        {agentPreview && (
          <div className="flex justify-end mt-4">
            <div className="bg-emerald-600/10 border border-emerald-500/20 rounded-xl px-4 py-3 max-w-[80%]">
              <div className="text-[10px] text-emerald-400 mb-1 font-medium">Preview del agente</div>
              <p className="text-[13px] text-zinc-300">{agentPreview}</p>
            </div>
          </div>
        )}
      </div>

      {/* Reply input */}
      <div className="px-6 pb-5 pt-2 border-t border-[#1e1e24]">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            placeholder="Escribe una respuesta..."
            className="flex-1 bg-[#0f0f12] border border-[#1e1e24] rounded-xl px-4 py-2.5 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700 transition-colors"
          />
          <button
            onClick={previewResponse}
            disabled={sending || !reply.trim()}
            className="p-2.5 rounded-xl bg-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-700 disabled:opacity-30 transition-colors"
            title="Preview respuesta del agente"
          >
            <Filter size={14} />
          </button>
          <button
            disabled={!reply.trim()}
            className="p-2.5 rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={14} />
          </button>
        </div>
        <p className="text-[10px] text-zinc-700 mt-1.5 ml-1">
          Filtro = preview del agente &middot; Enviar = respuesta directa por WhatsApp
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* WhatsApp page                                                       */
/* ------------------------------------------------------------------ */

export default function WhatsAppPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const filtered = MOCK_CONVERSATIONS.filter((c) => {
    if (filter !== "all" && c.product !== filter) return false;
    if (search && !c.name.toLowerCase().includes(search.toLowerCase()) && !c.phone.includes(search)) return false;
    return true;
  });

  const selectedConv = MOCK_CONVERSATIONS.find((c) => c.id === selected);

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="WhatsApp">
        <div className="flex items-center gap-1.5 text-[11px] text-zinc-600">
          <Clock size={11} />
          Actualizado hace 30s
        </div>
      </PageHeader>

      <div className="flex flex-1 overflow-hidden">
        <ConversationList
          conversations={filtered}
          selected={selected}
          onSelect={setSelected}
          filter={filter}
          onFilterChange={setFilter}
          search={search}
          onSearchChange={setSearch}
        />

        {selectedConv ? (
          <ConversationThread conversation={selectedConv} />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Smartphone size={32} className="mx-auto mb-3 text-zinc-700" />
              <p className="text-[14px] text-zinc-500">Selecciona una conversacion</p>
              <p className="text-[11px] text-zinc-700 mt-1">
                Las conversaciones de WhatsApp aparecen aqui
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
