"use client";

import { useState, useRef, useEffect, FormEvent } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7777";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  timestamp: Date;
}

interface TeamInfo {
  name: string;
  id: string;
  description?: string;
  mode?: string;
  members?: number;
  icon: string;
  color: string;
  health: number;
  subtitle: string;
}

interface AgentMetric {
  name: string;
  health: number;
  icon: string;
  bars: number[];
}

interface SystemLayer {
  label: string;
  tag: string;
}

/* ------------------------------------------------------------------ */
/* Static data (matches the visual reference)                          */
/* ------------------------------------------------------------------ */

const TEAMS: TeamInfo[] = [
  {
    name: "NEXUS Master",
    id: "nexus",
    icon: "⚡",
    color: "text-accent",
    health: 99.9,
    subtitle: "Core System",
  },
  {
    name: "Marketing Latam",
    id: "marketing-latam",
    icon: "📊",
    color: "text-warn",
    health: 92.4,
    subtitle: "Latam Region",
  },
  {
    name: "WhatsApp Support",
    id: "whatsapp-support",
    icon: "💬",
    color: "text-accent",
    health: 74.2,
    subtitle: "WhatsApp Integration",
  },
  {
    name: "Product Dev",
    id: "product-dev",
    icon: "🛠",
    color: "text-[#8b5cf6]",
    health: 57.9,
    subtitle: "Coordinate Mode",
  },
  {
    name: "Creative Studio",
    id: "creative-studio",
    icon: "🎨",
    color: "text-pink-400",
    health: 88.1,
    subtitle: "NanoBanana / Gemini",
  },
  {
    name: "Content Factory",
    id: "content-factory",
    icon: "📝",
    color: "text-cyan-400",
    health: 91.3,
    subtitle: "Scripts & Audits",
  },
  {
    name: "Cerebro",
    id: "cerebro",
    icon: "🧠",
    color: "text-violet-400",
    health: 95.7,
    subtitle: "Multi-source Research",
  },
];

const AGENT_METRICS: AgentMetric[] = [
  {
    name: "Agente Invest.",
    health: 95,
    icon: "🔍",
    bars: [50, 50, 40, 30, 20, 10, 15, 30, 50, 60, 55, 60, 50, 45, 40, 30, 20, 40, 60, 70],
  },
  {
    name: "Agente Creativo",
    health: 84,
    icon: "🎨",
    bars: [35, 55, 20, 15, 40, 30, 50, 35, 20, 20, 55, 25],
  },
];

const SYSTEM_LAYERS: SystemLayer[] = [
  { label: "Estado General", tag: "Fijado" },
  { label: "Carga de Trabajo", tag: "Fijado" },
  { label: "Tráfico de Red", tag: "Capa Base" },
  { label: "Alertas de Error (Alta Res.)", tag: "Fijado" },
  { label: "Mapa de Memoria", tag: "Fijado" },
  { label: "Mapa de Latencia", tag: "Fijado" },
  { label: "Estadísticas de Fallos", tag: "Fijado" },
  { label: "Uso de APIs (Externa)", tag: "Fijado" },
  { label: "CRM Sync", tag: "Fijado" },
  { label: "OpenRouter Load", tag: "Fijado" },
  { label: "MiniMax Load", tag: "Fijado" },
  { label: "WhatsApp Queue", tag: "Fijado" },
  { label: "AgentOS Version", tag: "Sistema" },
];

const TABS = [
  "Dashboard",
  "Automatización",
  "Comparación",
  "Flujos Inteligentes",
  "Análisis",
];

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function barColor(pct: number): string {
  if (pct >= 40) return "bg-accent";
  if (pct >= 25) return "bg-warn";
  return "bg-danger";
}

/* ------------------------------------------------------------------ */
/* Component: Left Sidebar                                             */
/* ------------------------------------------------------------------ */

function LeftSidebar({
  expandedTeam,
  setExpandedTeam,
}: {
  expandedTeam: string | null;
  setExpandedTeam: (id: string | null) => void;
}) {
  return (
    <aside className="w-[320px] bg-panel flex flex-col border-r border-white/5 relative z-10">
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3">
        {/* Team list */}
        {TEAMS.map((t) => {
          const isExpanded = expandedTeam === t.id;
          return (
            <div key={t.id} className="mb-1">
              {/* Header row */}
              <button
                onClick={() => setExpandedTeam(isExpanded ? null : t.id)}
                className="flex items-center justify-between w-full p-3 hover:bg-white/5 rounded-xl cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className={`text-lg ${t.color}`}>{t.icon}</span>
                  <div className="text-left">
                    <div className="text-white text-[13px] font-medium leading-snug">
                      {t.name}
                    </div>
                    <div className="text-neutral-500 text-[11px]">
                      {t.subtitle}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-white text-[13px]">
                  <span>
                    {t.health}{" "}
                    <span className="text-neutral-500 text-[11px]">%</span>
                  </span>
                  <span className="text-neutral-500 text-[14px]">
                    {isExpanded ? "▲" : "▼"}
                  </span>
                </div>
              </button>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="bg-card rounded-xl p-3 mb-2 border border-white/5">
                  <div className="space-y-3 mb-3">
                    {[
                      { icon: "📡", label: "API Calls", sub: "Nivel Estable", val: "92.2 %" },
                      { icon: "🌐", label: "Latencia de Red", sub: "Nivel Estable", val: "74.5 ms" },
                      { icon: "💾", label: "Memoria RAM", sub: "Optimizando", val: "28.1 %" },
                      { icon: "🗄", label: "Base de Datos", sub: "Vectorial", val: "16.7 %" },
                    ].map((m) => (
                      <div
                        key={m.label}
                        className="flex justify-between items-center px-1"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-neutral-500 text-[15px]">
                            {m.icon}
                          </span>
                          <div>
                            <div className="text-white text-[12px]">
                              {m.label}
                            </div>
                            <div className="text-neutral-500 text-[10px]">
                              {m.sub}
                            </div>
                          </div>
                        </div>
                        <div className="text-white text-[13px]">{m.val}</div>
                      </div>
                    ))}
                  </div>

                  {/* 2x2 grid stats */}
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { label: "Carga CPU", val: "19", unit: "%" },
                      { label: "Tasa de Éxito", val: "91", unit: "%" },
                      { label: "Tokens Usados", val: "30", unit: "k" },
                      { label: "Errores Gen.", val: "50", unit: "/h" },
                      { label: "Almacenamiento", val: "95", unit: "%" },
                      { label: "Carga de Trabajo", val: "74", unit: "%" },
                    ].map((s) => (
                      <div key={s.label} className="bg-subcard p-3 rounded-[10px]">
                        <div className="text-neutral-400 text-[11px] mb-1 leading-none">
                          {s.label}
                        </div>
                        <div className="text-white text-[15px] font-medium">
                          {s.val}{" "}
                          <span className="text-neutral-500 text-[10px]">
                            {s.unit}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {/* Agent mini charts */}
        <div className="px-2 space-y-5 mt-4 mb-6">
          {AGENT_METRICS.map((a) => (
            <div key={a.name}>
              <div className="flex justify-between items-center mb-3">
                <div className="text-white text-[12px] font-medium flex items-center gap-1">
                  {a.icon} {a.name}
                </div>
                <div className="text-accent text-[11px] flex items-center gap-1">
                  ❤ {a.health}{" "}
                  <span className="text-neutral-500">HP</span>
                </div>
              </div>
              <div className="h-10 flex items-end justify-between gap-[2px]">
                {a.bars.map((pct, i) => (
                  <div
                    key={i}
                    className={`w-full ${barColor(pct)} rounded-[1px]`}
                    style={{ height: `${pct}%` }}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

/* ------------------------------------------------------------------ */
/* Component: Right Sidebar                                            */
/* ------------------------------------------------------------------ */

function RightSidebar() {
  const [search, setSearch] = useState("");
  const filtered = SYSTEM_LAYERS.filter((l) =>
    l.label.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <aside className="w-[300px] bg-panel flex flex-col border-l border-white/5 relative z-10">
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-white text-[15px] font-medium">
            Capas de Sistema &amp; Datos
          </h2>
          <div className="flex items-center gap-3 text-neutral-400">
            <button className="hover:text-white transition-colors">📌</button>
            <button className="hover:text-white transition-colors">⚙</button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500 text-[14px]">
            🔍
          </span>
          <input
            type="text"
            placeholder="Buscar Datos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-[#1e1e20] border border-transparent focus:border-neutral-700 outline-none rounded-lg pl-9 pr-3 py-2 text-[13px] text-white placeholder-neutral-500 transition-colors"
          />
        </div>

        {/* Layer list */}
        <div className="space-y-4">
          {filtered.map((l) => (
            <div
              key={l.label}
              className="flex justify-between items-center group"
            >
              <div>
                <div className="text-white text-[13px] font-medium group-hover:text-accent transition-colors cursor-pointer">
                  {l.label}
                </div>
                <div className="text-neutral-600 text-[11px]">{l.tag}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

/* ------------------------------------------------------------------ */
/* Component: Network Map SVG                                          */
/* ------------------------------------------------------------------ */

function NetworkMap() {
  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      preserveAspectRatio="xMidYMid slice"
      viewBox="0 0 800 600"
    >
      {/* Connection lines */}
      <path
        d="M 400 300 L 550 150 L 650 350 L 400 450 Z"
        fill="none"
        stroke="rgba(255,255,255,0.1)"
        strokeWidth="1"
        strokeDasharray="4 4"
      />
      <path
        d="M 200 200 L 400 300 L 300 500 Z"
        fill="none"
        stroke="rgba(255,255,255,0.1)"
        strokeWidth="1"
        strokeDasharray="4 4"
      />

      {/* Zone 1 */}
      <g transform="translate(80, -50)">
        <polygon
          points="350,150 480,80 550,200 600,220 500,320 400,280 380,200"
          fill="rgba(255,255,255,0.03)"
          stroke="rgba(255,255,255,0.8)"
          strokeWidth="2"
          strokeLinejoin="round"
        />
      </g>

      {/* Zone 2 */}
      <g transform="translate(50, 100)">
        <polygon
          points="250,300 350,280 450,250 500,400 550,450 400,500 280,450 300,380"
          fill="rgba(255,255,255,0.04)"
          stroke="rgba(255,255,255,0.8)"
          strokeWidth="2"
          strokeLinejoin="round"
        />
      </g>

      {/* Decorative circles */}
      <circle
        cx="250"
        cy="450"
        r="80"
        fill="rgba(59,130,246,0.05)"
        stroke="rgba(59,130,246,0.2)"
        strokeWidth="1"
        strokeDasharray="2 4"
      />
      <circle
        cx="250"
        cy="450"
        r="60"
        fill="none"
        stroke="rgba(59,130,246,0.1)"
        strokeWidth="1"
      />
      <circle
        cx="250"
        cy="450"
        r="40"
        fill="none"
        stroke="rgba(59,130,246,0.2)"
        strokeWidth="1"
      />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/* Component: Center Panel (Map + Chat)                                */
/* ------------------------------------------------------------------ */

function CenterPanel({
  messages,
  input,
  setInput,
  loading,
  onSend,
  chatOpen,
  setChatOpen,
  messagesEndRef,
}: {
  messages: Message[];
  input: string;
  setInput: (v: string) => void;
  loading: boolean;
  onSend: (e: FormEvent) => void;
  chatOpen: boolean;
  setChatOpen: (v: boolean) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}) {
  return (
    <main className="flex-1 relative map-bg overflow-hidden">
      <NetworkMap />

      {/* Zone labels */}
      <div className="absolute top-[180px] left-[55%] bg-black/70 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10 text-white text-[12px] font-medium shadow-lg">
        Agentes
      </div>
      <div className="absolute top-[420px] left-[55%] bg-black/70 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10 text-white text-[12px] font-medium shadow-lg">
        Workflows
      </div>

      {/* Zoom controls */}
      <div className="absolute right-6 top-[40%] flex flex-col bg-panel/90 backdrop-blur border border-white/10 rounded-xl overflow-hidden shadow-xl">
        <button className="w-9 h-9 flex items-center justify-center text-neutral-400 hover:text-white hover:bg-white/10 transition-colors border-b border-white/10">
          +
        </button>
        <button className="w-9 h-9 flex items-center justify-center text-neutral-400 hover:text-white hover:bg-white/10 transition-colors">
          −
        </button>
      </div>

      {/* Timestamp */}
      <div className="absolute bottom-5 left-5 text-neutral-500 text-[11px] font-medium tracking-wide">
        AgentOS-hub: {new Date().toISOString().slice(0, 10)}
      </div>

      {/* Chat toggle button */}
      {!chatOpen && (
        <button
          onClick={() => setChatOpen(true)}
          className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-card/95 backdrop-blur-xl border border-white/10 rounded-[14px] px-6 py-3 flex items-center gap-3 shadow-2xl hover:border-accent/50 transition-colors"
        >
          <span className="text-lg">💬</span>
          <span className="text-white text-[13px] font-medium">
            Hablar con NEXUS
          </span>
        </button>
      )}

      {/* Chat panel (slides up from bottom) */}
      {chatOpen && (
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] max-h-[500px] bg-card/95 backdrop-blur-xl border border-white/10 rounded-t-[18px] shadow-2xl flex flex-col">
          {/* Chat header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <span className="text-accent text-lg">⚡</span>
              <span className="text-white text-[13px] font-medium">
                NEXUS Chat
              </span>
              <span className="text-neutral-500 text-[11px]">
                46 agentes disponibles
              </span>
            </div>
            <button
              onClick={() => setChatOpen(false)}
              className="text-neutral-500 hover:text-white transition-colors text-[14px]"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto custom-scrollbar px-4 py-3 space-y-3 min-h-[200px] max-h-[350px]">
            {messages.length === 0 && (
              <div className="text-center text-neutral-500 mt-8">
                <p className="text-[13px] mb-3">
                  Pregunta lo que necesites. NEXUS routea al mejor agente.
                </p>
                <div className="grid grid-cols-2 gap-2 max-w-sm mx-auto">
                  {[
                    "Investiga Mastra AI",
                    "Crea plan de marketing para Whabi",
                    "Genera imagen para Instagram",
                    "Analiza feedback de Docflow",
                  ].map((s) => (
                    <button
                      key={s}
                      onClick={() => setInput(s)}
                      className="text-left text-[11px] p-2.5 bg-subcard border border-white/5 rounded-lg hover:border-accent/30 transition-colors text-neutral-400"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-xl px-3.5 py-2.5 ${
                    msg.role === "user"
                      ? "bg-accent/20 text-white border border-accent/20"
                      : "bg-subcard border border-white/5 text-gray-200"
                  }`}
                >
                  {msg.role === "assistant" && msg.agent && (
                    <div className="text-[10px] text-accent mb-1 font-medium">
                      {msg.agent}
                    </div>
                  )}
                  <div className="whitespace-pre-wrap text-[13px] leading-relaxed">
                    {msg.content}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-subcard border border-white/5 rounded-xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce [animation-delay:0.1s]" />
                    <div className="w-2 h-2 bg-accent rounded-full animate-bounce [animation-delay:0.2s]" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={onSend}
            className="flex gap-2 px-4 py-3 border-t border-white/5"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Escribe tu mensaje..."
              className="flex-1 bg-[#1e1e20] border border-transparent focus:border-accent/50 outline-none rounded-lg px-3.5 py-2.5 text-[13px] text-white placeholder-neutral-500 transition-colors"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-accent text-white px-5 py-2.5 rounded-lg text-[13px] font-medium hover:bg-accent/80 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Enviar
            </button>
          </form>
        </div>
      )}
    </main>
  );
}

/* ------------------------------------------------------------------ */
/* Page: Main Dashboard                                                */
/* ------------------------------------------------------------------ */

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [activeTab, setActiveTab] = useState("Dashboard");
  const [expandedTeam, setExpandedTeam] = useState<string | null>(
    "marketing-latam",
  );
  const [chatOpen, setChatOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(
      `nexus-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    );
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("message", userMessage.content);
      formData.append("stream", "false");
      formData.append("session_id", sessionId);
      formData.append("user_id", "nexus-ui-user");

      const response = await fetch(`${API_URL}/teams/nexus/runs`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();

      const content =
        typeof data.content === "string"
          ? data.content
          : data.content?.text ||
            data.messages?.[data.messages.length - 1]?.content ||
            JSON.stringify(data);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content,
        agent: data.agent_name || "NEXUS",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `Error: ${error instanceof Error ? error.message : "Unknown error"}. Verifica que AgentOS esta corriendo en ${API_URL}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex items-center justify-center p-4 lg:p-8 bg-[#8a8a8e]">
      {/* Device wrapper */}
      <div className="w-full max-w-[1440px] h-[850px] bg-[#0a0a0c] rounded-[24px] shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden flex flex-col ring-1 ring-white/10">
        {/* Header */}
        <header className="h-[68px] flex items-center px-6 shrink-0 border-b border-white/5 bg-[#0a0a0c] relative z-10">
          {/* Logo */}
          <div className="flex items-center gap-3 w-[300px]">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              className="w-6 h-6 text-white"
            >
              <path
                d="M12 2L12 6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M12 18L12 22"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M4.93 4.93L7.76 7.76"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M16.24 16.24L19.07 19.07"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M2 12L6 12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M18 12L22 12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M4.93 19.07L7.76 16.24"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M16.24 7.76L19.07 4.93"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <circle cx="12" cy="12" r="3" fill="currentColor" />
            </svg>
            <div className="text-[15px] text-white font-medium tracking-wide">
              NEXUS{" "}
              <span className="text-neutral-500 font-normal">Insights</span>
            </div>
          </div>

          {/* Center tabs */}
          <nav className="flex-1 flex justify-center">
            <div className="flex items-center gap-1">
              {TABS.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-full text-[13px] transition-colors ${
                    activeTab === tab
                      ? "bg-[#1c1c1e] text-white font-medium"
                      : "text-neutral-400 hover:text-white hover:bg-white/5"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </nav>

          {/* Right spacer */}
          <div className="w-[300px]" />
        </header>

        {/* Main content */}
        <div className="flex flex-1 overflow-hidden">
          <LeftSidebar
            expandedTeam={expandedTeam}
            setExpandedTeam={setExpandedTeam}
          />

          <CenterPanel
            messages={messages}
            input={input}
            setInput={setInput}
            loading={loading}
            onSend={sendMessage}
            chatOpen={chatOpen}
            setChatOpen={setChatOpen}
            messagesEndRef={messagesEndRef}
          />

          <RightSidebar />
        </div>
      </div>
    </div>
  );
}
