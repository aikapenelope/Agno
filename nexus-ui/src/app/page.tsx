"use client";

import { CopilotChat } from "@copilotkit/react-ui";

/**
 * NEXUS UI — Main Page
 *
 * Full-screen chat interface connected to the NEXUS Master Team.
 * NEXUS routes your message to the best specialist agent:
 *
 * - "investiga X"              → Research Agent
 * - "cuantos leads esta semana" → Dash (analytics)
 * - "guardame esta nota"        → Pal (personal assistant)
 * - "redacta un email para X"   → Email Agent
 * - "recuerdame llamar a X"     → Scheduler Agent
 * - "genera cotizacion para X"  → Invoice Agent
 * - "revisa este codigo"        → Code Review Agent
 * - "como configuro Whabi"      → Onboarding Agent
 * - "busca tendencias de AI"    → Trend Scout
 * - "metricas de Instagram"     → Analytics Agent
 */
export default function Home() {
  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-[#1a1a2e] border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">NEXUS</h1>
            <p className="text-sm text-gray-400">
              AikaLabs — 12 agentes especializados a tu servicio
            </p>
          </div>
          <div className="flex gap-2">
            <span className="px-2 py-1 bg-green-900/30 text-green-400 text-xs rounded">
              Research
            </span>
            <span className="px-2 py-1 bg-blue-900/30 text-blue-400 text-xs rounded">
              Analytics
            </span>
            <span className="px-2 py-1 bg-purple-900/30 text-purple-400 text-xs rounded">
              Content
            </span>
            <span className="px-2 py-1 bg-yellow-900/30 text-yellow-400 text-xs rounded">
              Support
            </span>
          </div>
        </div>
      </header>

      {/* Chat */}
      <div className="flex-1 overflow-hidden">
        <CopilotChat
          labels={{
            title: "NEXUS",
            initial:
              "Hola! Soy NEXUS, el orquestador de AikaLabs. " +
              "Tengo 12 agentes especializados: investigacion, analytics, " +
              "emails, facturacion, scheduling, code review, y mas. " +
              "En que te puedo ayudar?",
            placeholder: "Escribe tu mensaje...",
          }}
          className="h-full"
        />
      </div>
    </div>
  );
}
