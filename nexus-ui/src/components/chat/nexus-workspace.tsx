"use client";

import {
  Bot,
  Users,
  Workflow,
  MessageSquare,
  Smartphone,
  TrendingUp,
  Clock,
  CheckCircle,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/* Dashboard workspace (main content area)                             */
/* ------------------------------------------------------------------ */

interface StatCardProps {
  label: string;
  value: string;
  sub: string;
  icon: typeof Bot;
  color: string;
}

function StatCard({ label, value, sub, icon: Icon, color }: StatCardProps) {
  return (
    <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[12px] text-zinc-500 font-medium">{label}</span>
        <div
          className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center`}
        >
          <Icon size={14} className="text-white" />
        </div>
      </div>
      <div className="text-2xl font-semibold text-white tracking-tight">
        {value}
      </div>
      <div className="text-[11px] text-zinc-600 mt-1">{sub}</div>
    </div>
  );
}

interface TeamRowProps {
  name: string;
  mode: string;
  members: number;
  status: "active" | "idle";
}

function TeamRow({ name, mode, members, status }: TeamRowProps) {
  return (
    <div className="flex items-center justify-between py-2.5 px-1 hover:bg-white/[0.02] rounded-lg transition-colors">
      <div className="flex items-center gap-3">
        <div
          className={`w-2 h-2 rounded-full ${status === "active" ? "bg-emerald-500" : "bg-zinc-600"}`}
        />
        <div>
          <div className="text-[13px] text-white font-medium">{name}</div>
          <div className="text-[11px] text-zinc-600">
            {mode} &middot; {members} miembros
          </div>
        </div>
      </div>
      <span
        className={`text-[10px] px-2 py-0.5 rounded-full ${
          status === "active"
            ? "bg-emerald-500/10 text-emerald-400"
            : "bg-zinc-800 text-zinc-500"
        }`}
      >
        {status === "active" ? "Activo" : "Idle"}
      </span>
    </div>
  );
}

interface WorkflowRowProps {
  name: string;
  description: string;
}

function WorkflowRow({ name, description }: WorkflowRowProps) {
  return (
    <div className="flex items-center justify-between py-2.5 px-1 hover:bg-white/[0.02] rounded-lg transition-colors">
      <div>
        <div className="text-[13px] text-white font-medium">{name}</div>
        <div className="text-[11px] text-zinc-600 max-w-[300px] truncate">
          {description}
        </div>
      </div>
      <button className="text-[11px] text-emerald-400 hover:text-emerald-300 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 transition-colors">
        Ejecutar
      </button>
    </div>
  );
}

export default function NexusWorkspace() {
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Stats grid */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            label="Agentes Activos"
            value="46"
            sub="7 teams configurados"
            icon={Bot}
            color="bg-emerald-600/20"
          />
          <StatCard
            label="Teams"
            value="7"
            sub="5 sub-teams en NEXUS"
            icon={Users}
            color="bg-blue-600/20"
          />
          <StatCard
            label="Workflows"
            value="7"
            sub="Deep research, SEO, social"
            icon={Workflow}
            color="bg-violet-600/20"
          />
          <StatCard
            label="Sesiones Hoy"
            value="--"
            sub="Conecta AgentOS para ver"
            icon={MessageSquare}
            color="bg-amber-600/20"
          />
        </div>

        {/* Two column layout */}
        <div className="grid grid-cols-2 gap-6">
          {/* Teams */}
          <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[14px] font-medium text-white">Teams</h3>
              <span className="text-[11px] text-zinc-600">7 configurados</span>
            </div>
            <div className="space-y-1">
              <TeamRow
                name="NEXUS Master"
                mode="route"
                members={17}
                status="active"
              />
              <TeamRow
                name="Cerebro"
                mode="route"
                members={3}
                status="active"
              />
              <TeamRow
                name="Content Factory"
                mode="route"
                members={3}
                status="idle"
              />
              <TeamRow
                name="Product Development"
                mode="coordinate"
                members={3}
                status="idle"
              />
              <TeamRow
                name="Creative Studio"
                mode="route"
                members={3}
                status="idle"
              />
              <TeamRow
                name="Marketing Latam"
                mode="coordinate"
                members={3}
                status="idle"
              />
              <TeamRow
                name="WhatsApp Support"
                mode="route"
                members={4}
                status="active"
              />
            </div>
          </div>

          {/* Workflows */}
          <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[14px] font-medium text-white">Workflows</h3>
              <span className="text-[11px] text-zinc-600">7 disponibles</span>
            </div>
            <div className="space-y-1">
              <WorkflowRow
                name="Deep Research"
                description="Plan → Parallel scouts → Quality gate → Report"
              />
              <WorkflowRow
                name="Content Production"
                description="Trend → Compact → Script → Creative review"
              />
              <WorkflowRow
                name="SEO Content"
                description="Keyword → Article → Audit loop"
              />
              <WorkflowRow
                name="Social Media"
                description="Trend → Parallel(IG/TW/LI) → Audit"
              />
              <WorkflowRow
                name="Competitor Intel"
                description="Parallel(3 scouts) → Synthesis"
              />
              <WorkflowRow
                name="Client Research"
                description="Parallel(web + knowledge) → Synthesis"
              />
              <WorkflowRow
                name="Media Generation"
                description="Router(image vs video) → Generation"
              />
            </div>
          </div>
        </div>

        {/* Quick access row */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 flex items-center gap-3 hover:border-zinc-700/50 transition-colors cursor-pointer">
            <div className="w-10 h-10 rounded-lg bg-green-600/10 flex items-center justify-center">
              <Smartphone size={18} className="text-green-400" />
            </div>
            <div>
              <div className="text-[13px] text-white font-medium">
                WhatsApp
              </div>
              <div className="text-[11px] text-zinc-600">
                Conversaciones en vivo
              </div>
            </div>
          </div>
          <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 flex items-center gap-3 hover:border-zinc-700/50 transition-colors cursor-pointer">
            <div className="w-10 h-10 rounded-lg bg-amber-600/10 flex items-center justify-center">
              <CheckCircle size={18} className="text-amber-400" />
            </div>
            <div>
              <div className="text-[13px] text-white font-medium">
                Aprobaciones
              </div>
              <div className="text-[11px] text-zinc-600">
                Pagos y archivos pendientes
              </div>
            </div>
          </div>
          <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 flex items-center gap-3 hover:border-zinc-700/50 transition-colors cursor-pointer">
            <div className="w-10 h-10 rounded-lg bg-blue-600/10 flex items-center justify-center">
              <TrendingUp size={18} className="text-blue-400" />
            </div>
            <div>
              <div className="text-[13px] text-white font-medium">
                Analytics
              </div>
              <div className="text-[11px] text-zinc-600">
                Tokens, costos, rendimiento
              </div>
            </div>
          </div>
        </div>

        {/* Recent activity */}
        <div className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[14px] font-medium text-white">
              Actividad Reciente
            </h3>
            <Clock size={14} className="text-zinc-600" />
          </div>
          <div className="text-center py-8 text-zinc-600 text-[13px]">
            Conecta AgentOS para ver la actividad en tiempo real.
            <br />
            <span className="text-[11px] text-zinc-700">
              python nexus.py → http://localhost:7777
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
