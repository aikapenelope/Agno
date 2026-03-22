"use client";

import { useState, useEffect } from "react";
import {
  Users,
  Loader2,
  Send,
  ArrowLeft,
  ChevronRight,
  Network,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { listTeams, runTeam, type TeamInfo } from "@/lib/api";
import PageHeader from "@/components/layout/page-header";

const TEAM_META: Record<string, { icon: string; color: string }> = {
  nexus: { icon: "⚡", color: "bg-emerald-500/10" },
  cerebro: { icon: "🧠", color: "bg-violet-500/10" },
  "content-factory": { icon: "📝", color: "bg-cyan-500/10" },
  "product-dev": { icon: "🛠", color: "bg-amber-500/10" },
  "creative-studio": { icon: "🎨", color: "bg-pink-500/10" },
  "marketing-latam": { icon: "📊", color: "bg-blue-500/10" },
  "whatsapp-support": { icon: "💬", color: "bg-green-500/10" },
};

function TeamCard({ team, onClick }: { team: TeamInfo; onClick: () => void }) {
  const id = team.team_id || team.name;
  const meta = TEAM_META[id] || { icon: "👥", color: "bg-zinc-800" };
  const memberCount = team.members?.length || 0;

  return (
    <button
      onClick={onClick}
      className="text-left bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5 hover:border-zinc-700/50 hover:bg-[#111115] transition-all duration-150 group w-full"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${meta.color} flex items-center justify-center`}>
            <span className="text-lg">{meta.icon}</span>
          </div>
          <div>
            <h3 className="text-[14px] font-medium text-white group-hover:text-emerald-400 transition-colors">
              {team.name}
            </h3>
            <p className="text-[11px] text-zinc-600">
              {team.mode || "route"} &middot; {memberCount} miembros
            </p>
          </div>
        </div>
        <ChevronRight size={16} className="text-zinc-700 group-hover:text-zinc-500 transition-colors" />
      </div>
      {team.description && (
        <p className="text-[12px] text-zinc-500 mt-3 line-clamp-2 leading-relaxed">
          {team.description}
        </p>
      )}
    </button>
  );
}

function TeamDetail({ team, onBack }: { team: TeamInfo; onBack: () => void }) {
  const [messages, setMessages] = useState<Array<{ id: string; role: string; content: string }>>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `team-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`);
  const id = team.team_id || team.name;
  const meta = TEAM_META[id] || { icon: "👥", color: "bg-zinc-800" };

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setMessages((p) => [...p, { id: `u-${Date.now()}`, role: "user", content: msg }]);
    setInput("");
    setLoading(true);
    try {
      const data = await runTeam(id, msg, sessionId);
      const content = typeof data.content === "string" ? data.content : JSON.stringify(data);
      setMessages((p) => [...p, { id: `a-${Date.now()}`, role: "assistant", content }]);
    } catch (err) {
      setMessages((p) => [...p, { id: `e-${Date.now()}`, role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Fallo"}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="h-14 flex items-center gap-3 px-6 border-b border-[#1e1e24] shrink-0">
        <button onClick={onBack} className="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-white/5 transition-colors">
          <ArrowLeft size={16} />
        </button>
        <div className={`w-8 h-8 rounded-lg ${meta.color} flex items-center justify-center`}>
          <span>{meta.icon}</span>
        </div>
        <div>
          <h2 className="text-[14px] font-medium text-white">{team.name}</h2>
          <p className="text-[11px] text-zinc-600">{team.mode || "route"} &middot; {team.members?.length || 0} miembros</p>
        </div>
      </div>

      {team.members && team.members.length > 0 && (
        <div className="px-6 py-3 border-b border-[#1e1e24] flex gap-2 flex-wrap">
          {team.members.map((m) => (
            <span key={m.name} className="text-[10px] text-zinc-500 bg-zinc-900 px-2 py-0.5 rounded-full">
              {m.name}
            </span>
          ))}
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-zinc-600 text-[13px] mt-12">
            Chat directo con <span className="text-emerald-400">{team.name}</span>
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
            <Loader2 size={14} className="animate-spin text-emerald-400" /> Procesando...
          </div>
        )}
      </div>

      <form onSubmit={send} className="px-6 pb-5 pt-2">
        <div className="flex items-center gap-2 bg-[#0f0f12] border border-[#1e1e24] rounded-xl px-4 py-2.5 focus-within:border-zinc-700 transition-colors">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder={`Mensaje para ${team.name}...`} className="flex-1 bg-transparent text-[13px] text-white placeholder-zinc-600 outline-none" disabled={loading} />
          <button type="submit" disabled={loading || !input.trim()} className="p-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
            <Send size={13} />
          </button>
        </div>
      </form>
    </div>
  );
}

export default function TeamsPage() {
  const [teams, setTeams] = useState<TeamInfo[]>([]);
  const [selected, setSelected] = useState<TeamInfo | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listTeams()
      .then((data) => setTeams(Array.isArray(data) ? data : []))
      .catch((err) => setError(err.message));
  }, []);

  if (selected) return <TeamDetail team={selected} onBack={() => setSelected(null)} />;

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="Teams" />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto">
          {/* Hierarchy diagram */}
          <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Network size={14} className="text-zinc-500" />
              <span className="text-[12px] text-zinc-500 font-medium">Jerarquia</span>
            </div>
            <div className="text-[12px] text-zinc-400 font-mono leading-loose">
              <div>NEXUS Master (father team)</div>
              <div className="ml-4">├── 12 agentes individuales</div>
              <div className="ml-4">├── Cerebro (research)</div>
              <div className="ml-4">├── Content Factory (content)</div>
              <div className="ml-4">├── Product Development (coordinate)</div>
              <div className="ml-4">├── Creative Studio (media)</div>
              <div className="ml-4">└── Marketing Latam (coordinate)</div>
              <div className="mt-2">WhatsApp Support (independiente)</div>
              <div className="ml-4">├── Whabi Support</div>
              <div className="ml-4">├── Docflow Support</div>
              <div className="ml-4">├── Aurora Support</div>
              <div className="ml-4">└── General Support</div>
            </div>
          </div>

          {error && <div className="text-center text-red-400 text-[13px] py-8">{error}</div>}
          {!error && teams.length === 0 && (
            <div className="text-center text-zinc-600 text-[13px] py-12">
              <Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /> Cargando teams...
            </div>
          )}
          <div className="space-y-3">
            {teams.map((team) => (
              <TeamCard key={team.team_id || team.name} team={team} onClick={() => setSelected(team)} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
