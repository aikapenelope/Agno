"use client";

import { useState } from "react";
import { Settings, Check, AlertCircle, ExternalLink } from "lucide-react";
import PageHeader from "@/components/layout/page-header";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7777";

interface ApiKeyConfig {
  name: string;
  envVar: string;
  description: string;
  required: boolean;
  docsUrl?: string;
}

const API_KEYS: ApiKeyConfig[] = [
  { name: "OpenRouter", envVar: "OPENROUTER_API_KEY", description: "Modelos OpenAI via OpenRouter (reasoning, learning, followups)", required: true, docsUrl: "https://openrouter.ai/keys" },
  { name: "MiniMax", envVar: "MINIMAX_API_KEY", description: "Modelo principal para tool calling (suscripcion)", required: true, docsUrl: "https://platform.minimax.io" },
  { name: "Voyage AI", envVar: "VOYAGE_API_KEY", description: "Embeddings para knowledge base y learning", required: true, docsUrl: "https://dash.voyageai.com" },
  { name: "Tavily", envVar: "TAVILY_API_KEY", description: "Busqueda web de alta calidad (1000 gratis/mes)", required: false, docsUrl: "https://tavily.com" },
  { name: "Exa", envVar: "EXA_API_KEY", description: "Busqueda semantica para papers y contenido nicho", required: false, docsUrl: "https://exa.ai" },
  { name: "Google (NanoBanana)", envVar: "GOOGLE_API_KEY", description: "Generacion de imagenes con Gemini", required: false, docsUrl: "https://aistudio.google.com/apikey" },
  { name: "WhatsApp", envVar: "WHATSAPP_ACCESS_TOKEN", description: "Integracion WhatsApp Business API", required: false },
  { name: "GitHub", envVar: "GITHUB_TOKEN", description: "Acceso a repos para Code Review Agent", required: false },
  { name: "N8N", envVar: "N8N_API_KEY", description: "MCP server para workflows de automatizacion", required: false },
  { name: "Twenty CRM", envVar: "TWENTY_API_KEY", description: "MCP server para CRM", required: false },
];

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(API_URL);
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="Ajustes" />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-8">
          {/* Connection */}
          <section>
            <h3 className="text-[13px] font-medium text-white mb-4 flex items-center gap-2">
              <Settings size={14} className="text-zinc-500" />
              Conexion
            </h3>
            <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5 space-y-4">
              <div>
                <label className="text-[11px] text-zinc-500 mb-1.5 block">AgentOS URL</label>
                <input
                  type="text"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  className="w-full bg-[#0a0a0c] border border-[#1e1e24] rounded-lg px-3 py-2 text-[13px] text-white font-mono outline-none focus:border-zinc-700 transition-colors"
                />
                <p className="text-[10px] text-zinc-700 mt-1">
                  Configura via NEXT_PUBLIC_API_URL en .env.local
                </p>
              </div>
              <button
                onClick={handleSave}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-[12px] font-medium hover:bg-emerald-500 transition-colors"
              >
                {saved ? <Check size={12} /> : <Settings size={12} />}
                {saved ? "Guardado" : "Guardar"}
              </button>
            </div>
          </section>

          {/* API Keys */}
          <section>
            <h3 className="text-[13px] font-medium text-white mb-4">API Keys</h3>
            <p className="text-[11px] text-zinc-600 mb-4">
              Las API keys se configuran como variables de entorno en ~/.zshrc.
              Esta vista muestra cuales estan configuradas.
            </p>
            <div className="space-y-2">
              {API_KEYS.map((key) => (
                <div
                  key={key.envVar}
                  className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 flex items-center justify-between hover:border-zinc-700/50 transition-colors"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${key.required ? "bg-amber-500" : "bg-zinc-700"}`} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-medium text-white">{key.name}</span>
                        {key.required && (
                          <span className="text-[9px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                            Requerido
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-zinc-600 truncate">{key.description}</p>
                      <code className="text-[10px] text-zinc-700 font-mono">{key.envVar}</code>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    {key.docsUrl && (
                      <a
                        href={key.docsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors"
                      >
                        <ExternalLink size={12} />
                      </a>
                    )}
                    <div className="text-zinc-600">
                      <AlertCircle size={14} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* System info */}
          <section>
            <h3 className="text-[13px] font-medium text-white mb-4">Sistema</h3>
            <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
              <div className="grid grid-cols-2 gap-4 text-[12px]">
                <div>
                  <span className="text-zinc-600">Agentes</span>
                  <span className="text-white ml-2">46</span>
                </div>
                <div>
                  <span className="text-zinc-600">Teams</span>
                  <span className="text-white ml-2">7</span>
                </div>
                <div>
                  <span className="text-zinc-600">Workflows</span>
                  <span className="text-white ml-2">7</span>
                </div>
                <div>
                  <span className="text-zinc-600">Skills</span>
                  <span className="text-white ml-2">24</span>
                </div>
                <div>
                  <span className="text-zinc-600">Framework</span>
                  <span className="text-white ml-2">Agno + AgentOS</span>
                </div>
                <div>
                  <span className="text-zinc-600">Frontend</span>
                  <span className="text-white ml-2">Next.js + CopilotKit v2</span>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
