"use client";

import Link from "next/link";
import { Home, ChevronRight } from "lucide-react";

interface PageHeaderProps {
  title: string;
  badge?: string;
  children?: React.ReactNode;
}

export default function PageHeader({ title, badge, children }: PageHeaderProps) {
  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-[#1e1e24] shrink-0">
      <div className="flex items-center gap-2">
        <Link
          href="/"
          className="p-1.5 rounded-lg text-zinc-600 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
          title="Dashboard"
        >
          <Home size={14} />
        </Link>
        <ChevronRight size={12} className="text-zinc-700" />
        <h2 className="text-[15px] font-medium text-white">{title}</h2>
        {badge && (
          <span className="text-[11px] text-zinc-600 bg-zinc-900 px-2 py-0.5 rounded-full">
            {badge}
          </span>
        )}
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </header>
  );
}
