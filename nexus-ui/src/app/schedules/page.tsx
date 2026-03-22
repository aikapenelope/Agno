"use client";

import { useState, useEffect } from "react";
import {
  Calendar,
  Plus,
  Play,
  Pause,
  Trash2,
  Loader2,
  Clock,
  RefreshCw,
} from "lucide-react";
import { listSchedules } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7777";

interface Schedule {
  id: string;
  name: string;
  cron_expr: string;
  endpoint: string;
  enabled: boolean;
  last_run?: string;
  next_run?: string;
}

function cronToHuman(cron: string): string {
  const parts = cron.split(" ");
  if (parts.length < 5) return cron;
  const [min, hour, , , dow] = parts;
  const days = dow === "*" ? "todos los dias" : dow === "1-5" ? "L-V" : `dia ${dow}`;
  return `${hour}:${min.padStart(2, "0")} ${days}`;
}

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCron, setNewCron] = useState("0 8 * * 1-5");
  const [newEndpoint, setNewEndpoint] = useState("/agents/Research Agent/runs");
  const [newMessage, setNewMessage] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchSchedules();
  }, []);

  function fetchSchedules() {
    setLoading(true);
    listSchedules()
      .then((data) => setSchedules(Array.isArray(data) ? data as Schedule[] : []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  async function toggleSchedule(id: string, enabled: boolean) {
    const action = enabled ? "disable" : "enable";
    await fetch(`${API_URL}/schedules/${id}/${action}`, { method: "POST" });
    setSchedules((prev) => prev.map((s) => (s.id === id ? { ...s, enabled: !enabled } : s)));
  }

  async function triggerSchedule(id: string) {
    await fetch(`${API_URL}/schedules/${id}/trigger`, { method: "POST" });
  }

  async function deleteSchedule(id: string) {
    await fetch(`${API_URL}/schedules/${id}`, { method: "DELETE" });
    setSchedules((prev) => prev.filter((s) => s.id !== id));
  }

  async function createSchedule() {
    if (!newName.trim() || !newCron.trim()) return;
    setCreating(true);
    try {
      const res = await fetch(`${API_URL}/schedules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newName,
          cron_expr: newCron,
          endpoint: newEndpoint,
          method: "POST",
          payload: { message: newMessage || "Ejecutar tarea programada" },
          timezone: "America/Bogota",
        }),
      });
      if (res.ok) {
        setShowCreate(false);
        setNewName("");
        setNewMessage("");
        fetchSchedules();
      }
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="h-full flex flex-col">
      <header className="h-14 flex items-center justify-between px-6 border-b border-[#1e1e24] shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-[15px] font-medium text-white">Schedules</h2>
          <span className="text-[11px] text-zinc-600 bg-zinc-900 px-2 py-0.5 rounded-full">
            {schedules.length} programados
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400 text-[12px] font-medium hover:bg-emerald-600/20 transition-colors">
            <Plus size={12} /> Nuevo
          </button>
          <button onClick={fetchSchedules} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {/* Create form */}
          {showCreate && (
            <div className="bg-[#0f0f12] border border-emerald-500/20 rounded-xl p-5 space-y-3">
              <h3 className="text-[13px] font-medium text-white">Nuevo Schedule</h3>
              <input type="text" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Nombre (ej: daily-research)" className="w-full bg-[#0a0a0c] border border-[#1e1e24] rounded-lg px-3 py-2 text-[12px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700" />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-zinc-600 mb-1 block">Cron</label>
                  <input type="text" value={newCron} onChange={(e) => setNewCron(e.target.value)} className="w-full bg-[#0a0a0c] border border-[#1e1e24] rounded-lg px-3 py-2 text-[12px] text-white font-mono outline-none focus:border-zinc-700" />
                </div>
                <div>
                  <label className="text-[10px] text-zinc-600 mb-1 block">Endpoint</label>
                  <input type="text" value={newEndpoint} onChange={(e) => setNewEndpoint(e.target.value)} className="w-full bg-[#0a0a0c] border border-[#1e1e24] rounded-lg px-3 py-2 text-[12px] text-white font-mono outline-none focus:border-zinc-700" />
                </div>
              </div>
              <input type="text" value={newMessage} onChange={(e) => setNewMessage(e.target.value)} placeholder="Mensaje para el agente..." className="w-full bg-[#0a0a0c] border border-[#1e1e24] rounded-lg px-3 py-2 text-[12px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700" />
              <button onClick={createSchedule} disabled={creating || !newName.trim()} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-[12px] font-medium hover:bg-emerald-500 disabled:opacity-30 transition-colors">
                {creating ? <Loader2 size={12} className="animate-spin" /> : <Plus size={12} />}
                Crear Schedule
              </button>
            </div>
          )}

          {error && <div className="text-center text-red-400 text-[13px] py-4">{error}</div>}

          {!error && !loading && schedules.length === 0 && (
            <div className="text-center py-16">
              <Calendar size={28} className="mx-auto mb-3 text-zinc-700" />
              <p className="text-[14px] text-zinc-500 mb-1">No hay schedules configurados</p>
              <p className="text-[11px] text-zinc-700">Crea uno para automatizar tareas recurrentes.</p>
            </div>
          )}

          {schedules.map((s) => (
            <div key={s.id} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${s.enabled ? "bg-emerald-500" : "bg-zinc-600"}`} />
                  <div>
                    <h3 className="text-[13px] font-medium text-white">{s.name}</h3>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[11px] text-zinc-600 font-mono">{s.cron_expr}</span>
                      <span className="text-[10px] text-zinc-700">({cronToHuman(s.cron_expr)})</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  <button onClick={() => triggerSchedule(s.id)} className="p-1.5 rounded-lg text-zinc-600 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors" title="Ejecutar ahora">
                    <Play size={13} />
                  </button>
                  <button onClick={() => toggleSchedule(s.id, s.enabled)} className="p-1.5 rounded-lg text-zinc-600 hover:text-amber-400 hover:bg-amber-500/10 transition-colors" title={s.enabled ? "Pausar" : "Activar"}>
                    {s.enabled ? <Pause size={13} /> : <Clock size={13} />}
                  </button>
                  <button onClick={() => deleteSchedule(s.id)} className="p-1.5 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-colors" title="Eliminar">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
