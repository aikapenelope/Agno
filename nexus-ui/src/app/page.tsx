"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { Send, Paperclip, Sparkles, RotateCcw, ChevronDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { runTeam } from "@/lib/api";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  timestamp: Date;
  isPaused?: boolean;
  runId?: string;
}

/* ------------------------------------------------------------------ */
/* Constants                                                           */
/* ------------------------------------------------------------------ */

const SUGGESTIONS = [
  { text: "Investiga las ultimas tendencias en AI agents", icon: "🔍" },
  { text: "Crea un plan de marketing para Whabi", icon: "📊" },
  { text: "Genera una imagen para Instagram de Aurora", icon: "🎨" },
  { text: "Analiza el feedback de clientes de Docflow", icon: "📋" },
  { text: "Redacta un email de seguimiento para un lead", icon: "✉️" },
  { text: "Revisa el codigo del ultimo PR", icon: "💻" },
];

/* ------------------------------------------------------------------ */
/* Component: Empty State                                              */
/* ------------------------------------------------------------------ */

function EmptyState({ onSelect }: { onSelect: (text: string) => void }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6">
      <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center mb-6">
        <Sparkles size={24} className="text-emerald-400" />
      </div>
      <h1 className="text-2xl font-semibold text-white mb-2 tracking-tight">
        NEXUS Command Center
      </h1>
      <p className="text-sm text-zinc-500 mb-8 max-w-md text-center leading-relaxed">
        46 agentes especializados, 7 teams, 7 workflows.
        Pregunta lo que necesites — NEXUS routea al mejor especialista.
      </p>
      <div className="grid grid-cols-2 gap-2.5 max-w-lg w-full">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.text}
            onClick={() => onSelect(s.text)}
            className="text-left px-4 py-3 rounded-xl bg-[#0f0f12] border border-[#1e1e24] hover:border-zinc-700 hover:bg-[#141418] transition-all duration-150 group"
          >
            <span className="text-sm mr-2">{s.icon}</span>
            <span className="text-[13px] text-zinc-400 group-hover:text-zinc-300 leading-snug">
              {s.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Component: Message Bubble                                           */
/* ------------------------------------------------------------------ */

function MessageBubble({ msg }: { msg: Message }) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70%] bg-emerald-600/15 border border-emerald-500/20 rounded-2xl rounded-br-md px-4 py-3">
          <p className="text-[14px] text-zinc-100 leading-relaxed whitespace-pre-wrap">
            {msg.content}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 max-w-[85%]">
      {/* Agent avatar */}
      <div className="w-7 h-7 rounded-lg bg-[#141418] border border-[#1e1e24] flex items-center justify-center shrink-0 mt-0.5">
        <span className="text-[11px]">🤖</span>
      </div>
      <div className="flex-1 min-w-0">
        {msg.agent && (
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-[11px] font-medium text-emerald-400">
              {msg.agent}
            </span>
            <span className="text-[10px] text-zinc-600">
              {msg.timestamp.toLocaleTimeString("es", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>
        )}
        <div className="agent-response text-[14px] text-zinc-300 leading-relaxed">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {msg.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Component: Loading Indicator                                        */
/* ------------------------------------------------------------------ */

function LoadingIndicator() {
  return (
    <div className="flex gap-3 max-w-[85%]">
      <div className="w-7 h-7 rounded-lg bg-[#141418] border border-[#1e1e24] flex items-center justify-center shrink-0">
        <span className="text-[11px]">🤖</span>
      </div>
      <div className="flex items-center gap-1.5 py-3">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce" />
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:100ms]" />
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce [animation-delay:200ms]" />
        <span className="text-[12px] text-zinc-600 ml-2">Procesando...</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Page: Chat                                                          */
/* ------------------------------------------------------------------ */

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(
    () => `nexus-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
  );
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  async function send(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    const userMessage: Message = {
      id: `u-${Date.now()}`,
      role: "user",
      content: msg,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const data = await runTeam("nexus", msg, sessionId);

      const content =
        typeof data.content === "string"
          ? data.content
          : (data.content as Record<string, unknown>)?.text as string ||
            JSON.stringify(data);

      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content,
          agent: (data.agent_name as string) || "NEXUS",
          timestamp: new Date(),
          isPaused: Boolean(data.is_paused),
          runId: data.run_id as string | undefined,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Conexion fallida"}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    send();
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="h-full flex flex-col bg-[#09090b]">
      {/* Header */}
      <header className="h-14 flex items-center justify-between px-6 border-b border-[#1e1e24] shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-[15px] font-medium text-white">Chat</h2>
          <span className="text-[11px] text-zinc-600 bg-zinc-900 px-2 py-0.5 rounded-full">
            NEXUS Master Team
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMessages([])}
            className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors"
            title="Nueva conversacion"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </header>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {!hasMessages ? (
          <EmptyState onSelect={(t) => send(t)} />
        ) : (
          <div className="max-w-3xl mx-auto px-6 py-6 space-y-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {loading && <LoadingIndicator />}
          </div>
        )}
      </div>

      {/* Scroll to bottom */}
      {hasMessages && (
        <div className="flex justify-center -mt-4 mb-1 relative z-10">
          <button
            onClick={() =>
              scrollRef.current?.scrollTo({
                top: scrollRef.current.scrollHeight,
                behavior: "smooth",
              })
            }
            className="w-7 h-7 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-700 transition-colors shadow-lg"
          >
            <ChevronDown size={14} />
          </button>
        </div>
      )}

      {/* Input area */}
      <div className="px-6 pb-5 pt-2">
        <form
          onSubmit={handleSubmit}
          className="max-w-3xl mx-auto relative"
        >
          <div className="flex items-end gap-2 bg-[#0f0f12] border border-[#1e1e24] rounded-2xl px-4 py-3 focus-within:border-zinc-700 transition-colors shadow-lg">
            <button
              type="button"
              className="p-1 text-zinc-600 hover:text-zinc-400 transition-colors shrink-0 mb-0.5"
              title="Adjuntar archivo"
            >
              <Paperclip size={16} />
            </button>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe un mensaje..."
              rows={1}
              className="flex-1 bg-transparent text-[14px] text-white placeholder-zinc-600 outline-none resize-none max-h-40 leading-relaxed"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="p-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-150 shrink-0 mb-0.5"
            >
              <Send size={14} />
            </button>
          </div>
          <p className="text-center text-[11px] text-zinc-700 mt-2.5">
            NEXUS routea al mejor agente. Shift+Enter para nueva linea.
          </p>
        </form>
      </div>
    </div>
  );
}
