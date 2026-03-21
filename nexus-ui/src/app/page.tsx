"use client";

import { useState, useRef, useEffect, FormEvent } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7777";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  timestamp: Date;
}

/**
 * NEXUS UI — Chat with the NEXUS Master Team
 *
 * Connects directly to AgentOS REST API (no CopilotKit needed).
 * Uses streaming via the /v1/teams/NEXUS/runs endpoint.
 *
 * NEXUS routes your message to the best specialist:
 * - Research, Analytics, Email, Scheduling, Billing, Code Review,
 *   Personal Assistant, Onboarding, Content, and more.
 */
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(`nexus-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`);
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
      formData.append("stream", "true");
      formData.append("session_id", sessionId);
      formData.append("user_id", "nexus-ui-user");

      const response = await fetch(`${API_URL}/teams/nexus/runs`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      // Parse SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "",
        agent: "NEXUS",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setLoading(false);

      if (reader) {
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                const chunk =
                  data.content ||
                  data.text ||
                  (typeof data === "string" ? data : "");
                if (chunk) {
                  setMessages((prev) => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last && last.id === assistantMessage.id) {
                      last.content += chunk;
                      if (data.agent_name) last.agent = data.agent_name;
                    }
                    return [...updated];
                  });
                }
              } catch {
                // Skip non-JSON SSE lines (event names, comments)
              }
            }
          }
        }
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Unknown error"}. Verifica que AgentOS esta corriendo en ${API_URL}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0a]">
      {/* Header */}
      <header className="bg-[#1a1a2e] border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div>
            <h1 className="text-xl font-bold text-white">NEXUS</h1>
            <p className="text-sm text-gray-400">
              AikaLabs — 12 agentes especializados
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {["Research", "Analytics", "Content", "Support", "Email", "Billing"].map(
              (tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-gray-800 text-gray-300 text-xs rounded"
                >
                  {tag}
                </span>
              )
            )}
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-lg mb-2">Hola! Soy NEXUS.</p>
              <p className="text-sm">
                Tengo 12 agentes especializados: investigacion, analytics,
                emails, facturacion, scheduling, code review, y mas.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-2 max-w-md mx-auto">
                {[
                  "Cuantos leads tenemos esta semana?",
                  "Investiga LangChain DeepAgents",
                  "Redacta un email de seguimiento",
                  "Genera cotizacion para Clinica Norte",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setInput(suggestion)}
                    className="text-left text-xs p-3 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-600 transition-colors text-gray-400"
                  >
                    {suggestion}
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
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-[#e94560] text-white"
                    : "bg-gray-900 border border-gray-800 text-gray-200"
                }`}
              >
                {msg.role === "assistant" && msg.agent && (
                  <div className="text-xs text-gray-500 mb-1">{msg.agent}</div>
                )}
                <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.1s]" />
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 px-6 py-4 bg-[#0a0a0a]">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe tu mensaje..."
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[#e94560] transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-[#e94560] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#d63d56] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Enviar
          </button>
        </form>
      </div>
    </div>
  );
}
