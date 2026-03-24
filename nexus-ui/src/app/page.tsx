"use client";

import { useState, useEffect } from "react";
import { CopilotKit } from "@copilotkit/react-core/v2";
import Sidebar from "@/components/layout/sidebar";
import NexusOverlay from "@/components/chat/nexus-overlay";
import {
  Bot,
  Users,
  Workflow,
  MessageSquare,
  Smartphone,
  TrendingUp,
  Clock,
  CheckCircle,
  Loader2,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { listAgents, listTeams, listWorkflows, listSessions, listTraces, approvalCount } from "@/lib/api";

function StatCard({ label, value, sub, icon: Icon, color, href }: { label: string; value: string; sub: string; icon: typeof Bot; color: string; href: string }) {
  return (
    <Link href={href} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[12px] text-zinc-500 font-medium">{label}</span>
        <div className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center`}><Icon size={14} className="text-white" /></div>
      </div>
      <div className="text-2xl font-semibold text-white tracking-tight">{value}</div>
      <div className="text-[11px] text-zinc-600 mt-1">{sub}</div>
    </Link>
  );
}

function QuickCard({ label, sub, icon: Icon, color, href }: { label: string; sub: string; icon: typeof Bot; color: string; href: string }) {
  return (
    <Link href={href} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 flex items-center gap-3 hover:border-zinc-700/50 transition-colors">
      <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}><Icon size={18} className="text-white" /></div>
      <div>
        <div className="text-[13px] text-white font-medium">{label}</div>
        <div className="text-[11px] text-zinc-600">{sub}</div>
      </div>
    </Link>
  );
}

function DashboardContent() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ agents: 0, teams: 0, workflows: 0, sessions: 0, traces: 0, pendingApprovals: 0 });

  useEffect(() => {
    Promise.all([
      listAgents().catch(() => []),
      listTeams().catch(() => []),
      listWorkflows().catch(() => []),
      listSessions().catch(() => []),
      listTraces(1).catch(() => []),
      approvalCount().catch(() => ({ count: 0 })),
    ]).then(([a, t, w, s, tr, ap]) => {
      setStats({
        agents: Array.isArray(a) ? a.length : 0,
        teams: Array.isArray(t) ? t.length : 0,
        workflows: Array.isArray(w) ? w.length : 0,
        sessions: Array.isArray(s) ? s.length : 0,
        traces: Array.isArray(tr) ? tr.length : 0,
        pendingApprovals: (ap as { count?: number }).count || 0,
      });
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 size={24} className="animate-spin mx-auto mb-3 text-zinc-500" />
          <p className="text-[13px] text-zinc-600">Conectando con AgentOS...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Agentes" value={String(stats.agents)} sub="Registrados en AgentOS" icon={Bot} color="bg-emerald-600/20" href="/agents" />
          <StatCard label="Teams" value={String(stats.teams)} sub={`${stats.workflows} workflows`} icon={Users} color="bg-blue-600/20" href="/teams" />
          <StatCard label="Sesiones" value={String(stats.sessions)} sub="Total historico" icon={MessageSquare} color="bg-violet-600/20" href="/history" />
          <StatCard label="Aprobaciones" value={String(stats.pendingApprovals)} sub="Pendientes" icon={CheckCircle} color="bg-amber-600/20" href="/approvals" />
        </div>

        {/* Quick access */}
        <div className="grid grid-cols-4 gap-4">
          <QuickCard label="Chat" sub="Hablar con NEXUS" icon={MessageSquare} color="bg-emerald-600/10" href="/chat" />
          <QuickCard label="Topologia" sub="Mapa de agentes" icon={Zap} color="bg-violet-600/10" href="/topology" />
          <QuickCard label="WhatsApp" sub="Conversaciones" icon={Smartphone} color="bg-green-600/10" href="/whatsapp" />
          <QuickCard label="Analytics" sub="Metricas y costos" icon={TrendingUp} color="bg-blue-600/10" href="/analytics" />
        </div>

        {/* Recent activity placeholder */}
        <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[14px] font-medium text-white">Sistema</h3>
            <Clock size={14} className="text-zinc-600" />
          </div>
          <div className="grid grid-cols-3 gap-4 text-[12px]">
            <div className="bg-zinc-900/50 rounded-lg p-3">
              <span className="text-zinc-600">Modelo principal</span>
              <div className="text-white mt-1">MiniMax M2.7</div>
            </div>
            <div className="bg-zinc-900/50 rounded-lg p-3">
              <span className="text-zinc-600">Reasoning</span>
              <div className="text-white mt-1">GPT-5-mini (OpenRouter)</div>
            </div>
            <div className="bg-zinc-900/50 rounded-lg p-3">
              <span className="text-zinc-600">Framework</span>
              <div className="text-white mt-1">Agno + AgentOS</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [overlayOpen, setOverlayOpen] = useState(false);

  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="nexus">
      <div className="flex h-screen overflow-hidden">
        <Sidebar onOpenCopilot={() => setOverlayOpen(true)} />
        <div className="flex-1 flex flex-col overflow-hidden">
          <header className="h-14 flex items-center justify-between px-6 border-b border-[#1e1e24] shrink-0 bg-[#09090b]">
            <div className="flex items-center gap-3">
              <h2 className="text-[15px] font-medium text-white">Command Center</h2>
            </div>
            <button onClick={() => setOverlayOpen(!overlayOpen)} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400 text-[13px] font-medium hover:bg-emerald-600/20 transition-colors">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />NEXUS AI
            </button>
          </header>
          <DashboardContent />
        </div>
        {overlayOpen && <NexusOverlay onClose={() => setOverlayOpen(false)} />}
      </div>
    </CopilotKit>
  );
}
