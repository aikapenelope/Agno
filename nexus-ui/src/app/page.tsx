"use client";

import { CopilotKit } from "@copilotkit/react-core/v2";
import Sidebar from "@/components/layout/sidebar";
import NexusWorkspace from "@/components/chat/nexus-workspace";
import NexusOverlay from "@/components/chat/nexus-overlay";
import { useState } from "react";

export default function Home() {
  const [overlayOpen, setOverlayOpen] = useState(false);

  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="nexus">
      <div className="flex h-screen overflow-hidden">
        <Sidebar onOpenCopilot={() => setOverlayOpen(true)} />

        {/* Main content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="h-14 flex items-center justify-between px-6 border-b border-[#1e1e24] shrink-0 bg-[#09090b]">
            <div className="flex items-center gap-3">
              <h2 className="text-[15px] font-medium text-white">
                Command Center
              </h2>
              <span className="text-[11px] text-zinc-600 bg-zinc-900 px-2 py-0.5 rounded-full">
                46 agentes &middot; 7 teams &middot; 7 workflows
              </span>
            </div>
            <button
              onClick={() => setOverlayOpen(!overlayOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400 text-[13px] font-medium hover:bg-emerald-600/20 transition-colors"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              NEXUS AI
            </button>
          </header>

          {/* Dashboard content */}
          <NexusWorkspace />
        </div>

        {/* Copilot overlay panel (slides from right) */}
        {overlayOpen && (
          <NexusOverlay onClose={() => setOverlayOpen(false)} />
        )}
      </div>
    </CopilotKit>
  );
}
