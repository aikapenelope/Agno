"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  Bot,
  Users,
  Workflow,
  CheckCircle,
  Calendar,
  BarChart3,
  Settings,
  Smartphone,
  Database,
} from "lucide-react";
import { useEffect, useState } from "react";
import { approvalCount } from "@/lib/api";

interface NavItem {
  href: string;
  label: string;
  icon: typeof MessageSquare;
  badge?: boolean;
}

const NAV: NavItem[] = [
  { href: "/", label: "Chat", icon: MessageSquare },
  { href: "/whatsapp", label: "WhatsApp", icon: Smartphone },
  { href: "/crm", label: "CRM", icon: Database },
  { href: "/agents", label: "Agentes", icon: Bot },
  { href: "/teams", label: "Teams", icon: Users },
  { href: "/workflows", label: "Workflows", icon: Workflow },
  { href: "/approvals", label: "Aprobaciones", icon: CheckCircle, badge: true },
  { href: "/schedules", label: "Schedules", icon: Calendar },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Ajustes", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [pending, setPending] = useState(0);

  useEffect(() => {
    const poll = () =>
      approvalCount()
        .then((d) => setPending(d.count ?? 0))
        .catch(() => {});
    poll();
    const id = setInterval(poll, 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <aside className="w-[220px] h-screen flex flex-col bg-[#0c0c0f] border-r border-[#1e1e24] shrink-0">
      {/* Logo */}
      <div className="h-16 flex items-center gap-2.5 px-5 border-b border-[#1e1e24]">
        <div className="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
        </div>
        <div>
          <span className="text-[15px] font-semibold text-white tracking-tight">
            NEXUS
          </span>
          <span className="text-[11px] text-zinc-500 ml-1.5">v2</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2.5 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all duration-150 group ${
                active
                  ? "bg-white/[0.06] text-white font-medium"
                  : "text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.03]"
              }`}
            >
              <Icon
                size={16}
                className={
                  active
                    ? "text-emerald-400"
                    : "text-zinc-600 group-hover:text-zinc-400"
                }
              />
              <span className="flex-1">{label}</span>
              {badge && pending > 0 && (
                <span className="min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-red-500/90 text-[10px] font-bold text-white px-1">
                  {pending}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[#1e1e24]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] text-zinc-500">AgentOS conectado</span>
        </div>
      </div>
    </aside>
  );
}
