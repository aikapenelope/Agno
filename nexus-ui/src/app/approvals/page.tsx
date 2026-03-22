"use client";

import { useState, useEffect, useCallback } from "react";
import {
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  RefreshCw,
  Shield,
  CreditCard,
  FileText,
  AlertTriangle,
} from "lucide-react";
import { listApprovals, resolveApproval, type Approval } from "@/lib/api";
import PageHeader from "@/components/layout/page-header";

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function toolIcon(name?: string) {
  if (!name) return AlertTriangle;
  if (name.includes("payment") || name.includes("invoice")) return CreditCard;
  if (name.includes("file") || name.includes("article") || name.includes("video"))
    return FileText;
  return Shield;
}

function timeAgo(ts?: number): string {
  if (!ts) return "";
  const diff = Math.floor((Date.now() / 1000 - ts) / 60);
  if (diff < 1) return "ahora";
  if (diff < 60) return `hace ${diff}m`;
  if (diff < 1440) return `hace ${Math.floor(diff / 60)}h`;
  return `hace ${Math.floor(diff / 1440)}d`;
}

/* ------------------------------------------------------------------ */
/* Approval Card                                                       */
/* ------------------------------------------------------------------ */

function ApprovalCard({
  approval,
  onResolve,
  resolving,
}: {
  approval: Approval;
  onResolve: (id: string, status: "approved" | "rejected") => void;
  resolving: string | null;
}) {
  const Icon = toolIcon(approval.source_name);
  const isPending = approval.status === "pending";
  const isResolving = resolving === approval.id;
  const ctx = approval.context || {};

  return (
    <div
      className={`bg-[#0f0f12] border rounded-xl p-5 transition-colors ${
        isPending
          ? "border-amber-500/20 hover:border-amber-500/40"
          : "border-[#1e1e24] opacity-60"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        {/* Left: info */}
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
              isPending ? "bg-amber-500/10" : "bg-zinc-800"
            }`}
          >
            <Icon
              size={18}
              className={isPending ? "text-amber-400" : "text-zinc-500"}
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-[13px] font-medium text-white">
                {approval.source_name || "Aprobacion pendiente"}
              </h3>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                  isPending
                    ? "bg-amber-500/10 text-amber-400"
                    : approval.status === "approved"
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "bg-red-500/10 text-red-400"
                }`}
              >
                {isPending
                  ? "Pendiente"
                  : approval.status === "approved"
                    ? "Aprobado"
                    : "Rechazado"}
              </span>
            </div>

            {/* Context details */}
            {Object.keys(ctx).length > 0 && (
              <div className="space-y-1 mt-2">
                {Object.entries(ctx).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className="text-[11px] text-zinc-600 min-w-[80px]">
                      {key}:
                    </span>
                    <span className="text-[11px] text-zinc-400 truncate">
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {approval.created_at && (
              <div className="flex items-center gap-1 mt-2 text-[10px] text-zinc-600">
                <Clock size={10} />
                {timeAgo(approval.created_at)}
              </div>
            )}
          </div>
        </div>

        {/* Right: actions */}
        {isPending && (
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => onResolve(approval.id, "rejected")}
              disabled={isResolving}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-[12px] font-medium hover:bg-red-500/20 disabled:opacity-40 transition-colors"
            >
              {isResolving ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <XCircle size={12} />
              )}
              Rechazar
            </button>
            <button
              onClick={() => onResolve(approval.id, "approved")}
              disabled={isResolving}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-600 text-white text-[12px] font-medium hover:bg-emerald-500 disabled:opacity-40 transition-colors"
            >
              {isResolving ? (
                <Loader2 size={12} className="animate-spin" />
              ) : (
                <CheckCircle size={12} />
              )}
              Aprobar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Approvals page                                                      */
/* ------------------------------------------------------------------ */

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<"all" | "pending" | "resolved">("all");

  const fetchApprovals = useCallback(() => {
    setLoading(true);
    listApprovals()
      .then((data) => {
        setApprovals(Array.isArray(data) ? data : []);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchApprovals();
    const id = setInterval(fetchApprovals, 15_000);
    return () => clearInterval(id);
  }, [fetchApprovals]);

  async function handleResolve(id: string, status: "approved" | "rejected") {
    setResolving(id);
    try {
      await resolveApproval(id, status);
      setApprovals((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status } : a)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al resolver");
    } finally {
      setResolving(null);
    }
  }

  const filtered = approvals.filter((a) => {
    if (filter === "pending") return a.status === "pending";
    if (filter === "resolved") return a.status !== "pending";
    return true;
  });

  const pendingCount = approvals.filter((a) => a.status === "pending").length;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <PageHeader title="Aprobaciones">
        <div className="flex items-center gap-2">
          {/* Filter tabs */}
          {(["all", "pending", "resolved"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-[12px] transition-colors ${
                filter === f
                  ? "bg-white/[0.06] text-white font-medium"
                  : "text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.03]"
              }`}
            >
              {f === "all" ? "Todas" : f === "pending" ? "Pendientes" : "Resueltas"}
            </button>
          ))}
          <button
            onClick={fetchApprovals}
            className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors ml-2"
            title="Actualizar"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </PageHeader>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-3">
          {error && (
            <div className="text-center text-red-400 text-[13px] bg-red-500/10 border border-red-500/20 rounded-xl p-4">
              {error}
            </div>
          )}

          {!error && loading && approvals.length === 0 && (
            <div className="text-center text-zinc-600 text-[13px] py-12">
              <Loader2
                size={20}
                className="animate-spin mx-auto mb-3 text-zinc-500"
              />
              Cargando aprobaciones...
            </div>
          )}

          {!error && !loading && filtered.length === 0 && (
            <div className="text-center py-16">
              <div className="w-14 h-14 rounded-2xl bg-zinc-800/50 flex items-center justify-center mx-auto mb-4">
                <CheckCircle size={24} className="text-zinc-600" />
              </div>
              <p className="text-[14px] text-zinc-500 mb-1">
                {filter === "pending"
                  ? "No hay aprobaciones pendientes"
                  : "No hay aprobaciones"}
              </p>
              <p className="text-[11px] text-zinc-700">
                Las aprobaciones aparecen cuando un agente necesita confirmacion
                para pagos, archivos, o acciones criticas.
              </p>
            </div>
          )}

          {filtered.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onResolve={handleResolve}
              resolving={resolving}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
