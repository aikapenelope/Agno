"use client";

import { useCallback } from "react";
import { useAgent, useCopilotKit } from "@copilotkit/react-core/v2";
import {
  CopilotChat,
  CopilotChatToolCallsView,
} from "@copilotkit/react-core/v2";
import { randomUUID } from "@copilotkit/shared";
import {
  X,
  Search,
  FileText,
  Image,
  Mail,
  Loader2,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/* Custom message views (adapted from atomic-crm)                      */
/* ------------------------------------------------------------------ */

function AssistantMessage({
  message,
  messages,
  isRunning,
}: {
  message: {
    id: string;
    role: string;
    content?: string;
    toolCalls?: unknown[];
  };
  messages: unknown[];
  isRunning: boolean;
  [key: string]: unknown;
}) {
  const hasToolCalls = message.toolCalls && message.toolCalls.length > 0;
  const textContent = message.content?.trim();
  const isLatest =
    (messages as Array<{ id: string }>)?.at(-1)?.id === message.id;
  const isThinking = isRunning && isLatest && !textContent && !hasToolCalls;

  if (isThinking) {
    return (
      <div className="flex items-center gap-2 py-3 text-sm text-zinc-500">
        <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
        <span>Procesando...</span>
      </div>
    );
  }

  if (!textContent && !hasToolCalls) return null;

  return (
    <div className="space-y-2 py-1.5">
      {hasToolCalls && (
        <CopilotChatToolCallsView
          message={message as Parameters<typeof CopilotChatToolCallsView>[0]["message"]}
          messages={messages as Parameters<typeof CopilotChatToolCallsView>[0]["messages"]}
        />
      )}
      {textContent && (
        <div className="flex items-start gap-2.5">
          <div className="w-6 h-6 rounded-md bg-emerald-500/10 flex items-center justify-center shrink-0 mt-0.5">
            <span className="text-[10px]">🤖</span>
          </div>
          <div className="text-[13px] leading-relaxed text-zinc-300 whitespace-pre-line">
            {textContent}
            {isRunning && isLatest && (
              <span className="inline-block w-1.5 h-4 bg-emerald-400/50 animate-pulse ml-0.5 align-text-bottom" />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function UserMessage({
  message,
}: {
  message: { content?: string };
  [key: string]: unknown;
}) {
  if (!message?.content?.trim()) return null;
  return (
    <div className="py-1 flex justify-end">
      <div className="bg-zinc-800/80 border border-zinc-700/50 rounded-xl px-3.5 py-2 max-w-[85%]">
        <p className="text-[13px] text-zinc-200">{message.content}</p>
      </div>
    </div>
  );
}

const NullSlot = () => null;

/* ------------------------------------------------------------------ */
/* Overlay Panel                                                       */
/* ------------------------------------------------------------------ */

export default function NexusOverlay({ onClose }: { onClose: () => void }) {
  const { agent } = useAgent();
  const { copilotkit } = useCopilotKit();

  const triggerAgent = useCallback(
    async (prompt: string) => {
      agent.addMessage({ id: randomUUID(), role: "user", content: prompt });
      await copilotkit.runAgent({ agent });
    },
    [agent, copilotkit],
  );

  const quickActions = [
    {
      label: "Investigar",
      icon: Search,
      prompt: "Investiga las ultimas tendencias en AI agents para Latam",
    },
    {
      label: "Contenido",
      icon: FileText,
      prompt: "Crea un plan de contenido semanal para Whabi en Instagram",
    },
    {
      label: "Imagen",
      icon: Image,
      prompt: "Genera una imagen profesional para el lanzamiento de Aurora",
    },
    {
      label: "Email",
      icon: Mail,
      prompt: "Redacta un email de seguimiento para un lead de Docflow",
    },
  ];

  return (
    <div className="w-[420px] h-screen bg-[#0c0c0f] border-l border-[#1e1e24] flex flex-col shrink-0 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e1e24] shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <h3 className="text-[14px] font-medium text-white">NEXUS AI</h3>
          <span className="text-[10px] text-zinc-600 bg-zinc-900 px-1.5 py-0.5 rounded">
            46 agentes
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-md text-zinc-500 hover:text-white hover:bg-white/5 transition-colors"
        >
          <X size={14} />
        </button>
      </div>

      {/* Quick actions */}
      <div className="flex gap-1.5 flex-wrap px-4 py-2.5 border-b border-[#1e1e24] shrink-0">
        {quickActions.map((action) => (
          <button
            key={action.label}
            disabled={agent.isRunning}
            onClick={() => triggerAgent(action.prompt)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-zinc-900 border border-zinc-800 text-[11px] text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 disabled:opacity-40 transition-colors"
          >
            <action.icon size={12} />
            {action.label}
          </button>
        ))}
      </div>

      {/* Chat */}
      <div className="flex-1 min-h-0">
        <CopilotChat
          className="h-full [&_[data-testid=copilot-welcome-screen]]:px-0"
          messageView={{
            assistantMessage: AssistantMessage as Parameters<typeof CopilotChat>[0]["messageView"] extends { assistantMessage?: infer T } ? T : never,
            userMessage: UserMessage as Parameters<typeof CopilotChat>[0]["messageView"] extends { userMessage?: infer T } ? T : never,
          }}
          scrollView={{
            feather: NullSlot,
            scrollToBottomButton: NullSlot,
          }}
        />
      </div>
    </div>
  );
}
