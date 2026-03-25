"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Users,
  Building2,
  ClipboardList,
  FileText,
  Plus,
  Search,
  Loader2,
  RefreshCw,
  User,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  X,
} from "lucide-react";
import PageHeader from "@/components/layout/page-header";
import {
  listPeople,
  listCompanies,
  listTasks,
  listNotes,
  createPerson,
  type Person,
  type Company,
  type Task,
  type Note,
} from "@/lib/twenty";

/* ------------------------------------------------------------------ */
/* Tabs                                                                */
/* ------------------------------------------------------------------ */

type Tab = "contacts" | "companies" | "tasks" | "notes";

const TABS: Array<{ id: Tab; label: string; icon: typeof Users }> = [
  { id: "contacts", label: "Contactos", icon: Users },
  { id: "companies", label: "Empresas", icon: Building2 },
  { id: "tasks", label: "Tareas", icon: ClipboardList },
  { id: "notes", label: "Notas", icon: FileText },
];

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

function formatDate(d?: string): string {
  if (!d) return "";
  return new Date(d).toLocaleDateString("es", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

// Use personDisplayName from twenty.ts
import { personDisplayName, personEmail, personPhone } from "@/lib/twenty";

/* ------------------------------------------------------------------ */
/* Create contact modal                                                */
/* ------------------------------------------------------------------ */

function CreateContactModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    if (!firstName.trim()) return;
    setSaving(true);
    try {
      await createPerson({ firstName, lastName, email, phone, jobTitle });
      onCreated();
      onClose();
    } catch { /* ignore */ }
    finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div className="bg-[#0c0c0f] border border-[#1e1e24] rounded-2xl w-full max-w-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-[14px] font-medium text-white">Nuevo Contacto</h3>
          <button onClick={onClose} className="p-1 text-zinc-500 hover:text-white"><X size={14} /></button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Nombre *" className="bg-zinc-900 border border-[#1e1e24] rounded-lg px-3 py-2 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700" />
          <input value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Apellido" className="bg-zinc-900 border border-[#1e1e24] rounded-lg px-3 py-2 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700" />
        </div>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className="w-full bg-zinc-900 border border-[#1e1e24] rounded-lg px-3 py-2 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700" />
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Telefono" className="w-full bg-zinc-900 border border-[#1e1e24] rounded-lg px-3 py-2 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700" />
        <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} placeholder="Cargo" className="w-full bg-zinc-900 border border-[#1e1e24] rounded-lg px-3 py-2 text-[13px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700" />
        <button onClick={handleSave} disabled={saving || !firstName.trim()} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 text-white text-[13px] font-medium hover:bg-emerald-500 disabled:opacity-40 transition-colors">
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />} Crear Contacto
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Tab content                                                         */
/* ------------------------------------------------------------------ */

function ContactsTab({ people, loading, search }: { people: Person[]; loading: boolean; search: string }) {
  const filtered = people.filter((p) => personDisplayName(p).toLowerCase().includes(search.toLowerCase()));
  if (loading) return <div className="text-center py-12"><Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /></div>;
  if (filtered.length === 0) return <div className="text-center py-12 text-zinc-600 text-[13px]">No hay contactos{search ? ` para "${search}"` : ""}</div>;

  return (
    <div className="space-y-1.5">
      {filtered.map((p) => (
        <div key={p.id} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-emerald-500/10 flex items-center justify-center"><User size={14} className="text-emerald-400" /></div>
              <div>
                <div className="text-[13px] font-medium text-white">{personDisplayName(p)}</div>
                <div className="flex items-center gap-3 text-[11px] text-zinc-600 mt-0.5">
                  {p.jobTitle && <span className="flex items-center gap-1"><Briefcase size={9} />{p.jobTitle}</span>}
                  {p.companyId && <span className="flex items-center gap-1"><Building2 size={9} />Empresa vinculada</span>}
                  {p.city && <span className="flex items-center gap-1"><MapPin size={9} />{p.city}</span>}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 text-[11px] text-zinc-600">
              {personEmail(p) && <span className="flex items-center gap-1"><Mail size={9} />{personEmail(p)}</span>}
              {personPhone(p) && <span className="flex items-center gap-1"><Phone size={9} />{personPhone(p)}</span>}
              {p.createdAt && <span>{formatDate(p.createdAt)}</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function CompaniesTab({ companies, loading }: { companies: Company[]; loading: boolean }) {
  if (loading) return <div className="text-center py-12"><Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /></div>;
  if (companies.length === 0) return <div className="text-center py-12 text-zinc-600 text-[13px]">No hay empresas</div>;
  return (
    <div className="space-y-1.5">
      {companies.map((c) => (
        <div key={c.id} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center"><Building2 size={14} className="text-blue-400" /></div>
              <div>
                <div className="text-[13px] font-medium text-white">{c.name || "Sin nombre"}</div>
                <div className="flex items-center gap-3 text-[11px] text-zinc-600 mt-0.5">
                  {c.domainName && <span>{c.domainName}</span>}
                  {c.employees && <span>{c.employees} empleados</span>}
                </div>
              </div>
            </div>
            {c.createdAt && <span className="text-[11px] text-zinc-700">{formatDate(c.createdAt)}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

function TasksTab({ tasks, loading }: { tasks: Task[]; loading: boolean }) {
  if (loading) return <div className="text-center py-12"><Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /></div>;
  if (tasks.length === 0) return <div className="text-center py-12 text-zinc-600 text-[13px]">No hay tareas</div>;
  return (
    <div className="space-y-1.5">
      {tasks.map((t) => (
        <div key={t.id} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[13px] font-medium text-white">{t.title || "Sin titulo"}</div>
              {t.body && <p className="text-[11px] text-zinc-600 mt-1 line-clamp-2">{t.body}</p>}
            </div>
            <div className="flex items-center gap-2">
              {t.status && <span className={`text-[10px] px-2 py-0.5 rounded-full ${t.status === "DONE" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>{t.status}</span>}
              {t.dueAt && <span className="text-[11px] text-zinc-600">{formatDate(t.dueAt)}</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function NotesTab({ notes, loading }: { notes: Note[]; loading: boolean }) {
  if (loading) return <div className="text-center py-12"><Loader2 size={20} className="animate-spin mx-auto mb-3 text-zinc-500" /></div>;
  if (notes.length === 0) return <div className="text-center py-12 text-zinc-600 text-[13px]">No hay notas</div>;
  return (
    <div className="space-y-1.5">
      {notes.map((n) => (
        <div key={n.id} className="bg-[#0f0f12] border border-[#1e1e24] rounded-xl p-4 hover:border-zinc-700/50 transition-colors">
          <div className="text-[13px] font-medium text-white mb-1">{n.title || "Sin titulo"}</div>
          {n.body && <p className="text-[12px] text-zinc-500 line-clamp-3 whitespace-pre-line">{n.body}</p>}
          {n.createdAt && <span className="text-[10px] text-zinc-700 mt-2 block">{formatDate(n.createdAt)}</span>}
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* CRM Page                                                            */
/* ------------------------------------------------------------------ */

export default function CrmPage() {
  const [tab, setTab] = useState<Tab>("contacts");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [people, setPeople] = useState<Person[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [showCreate, setShowCreate] = useState(false);

  const fetchAll = useCallback(() => {
    setLoading(true);
    setError("");
    Promise.all([
      listPeople().catch(() => []),
      listCompanies().catch(() => []),
      listTasks().catch(() => []),
      listNotes().catch(() => []),
    ]).then(([p, c, t, n]) => {
      setPeople(p);
      setCompanies(c);
      setTasks(t);
      setNotes(n);
    }).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  return (
    <div className="h-full flex flex-col">
      <PageHeader title="CRM" badge={`${people.length} contactos · ${companies.length} empresas`}>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400 text-[12px] font-medium hover:bg-emerald-600/20 transition-colors">
          <Plus size={12} /> Nuevo contacto
        </button>
        <button onClick={fetchAll} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-400 hover:bg-white/5 transition-colors">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </PageHeader>

      {/* Tabs + Search */}
      <div className="px-6 py-3 flex items-center justify-between border-b border-[#1e1e24]">
        <div className="flex gap-1">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors ${tab === t.id ? "bg-white/[0.06] text-white" : "text-zinc-600 hover:text-zinc-400"}`}>
              <t.icon size={12} /> {t.label}
            </button>
          ))}
        </div>
        <div className="relative w-[250px]">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar..." className="w-full bg-[#0f0f12] border border-[#1e1e24] rounded-lg pl-8 pr-3 py-1.5 text-[12px] text-white placeholder-zinc-600 outline-none focus:border-zinc-700" />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto">
          {error && (
            <div className="text-center text-amber-400 text-[13px] bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-4">
              Twenty CRM no disponible: {error}
              <br />
              <span className="text-[11px] text-zinc-600">
                Verifica que Twenty esta corriendo en localhost:3000 y NEXT_PUBLIC_TWENTY_API_KEY esta configurado
              </span>
            </div>
          )}

          {tab === "contacts" && <ContactsTab people={people} loading={loading} search={search} />}
          {tab === "companies" && <CompaniesTab companies={companies} loading={loading} />}
          {tab === "tasks" && <TasksTab tasks={tasks} loading={loading} />}
          {tab === "notes" && <NotesTab notes={notes} loading={loading} />}
        </div>
      </div>

      {showCreate && <CreateContactModal onClose={() => setShowCreate(false)} onCreated={fetchAll} />}
    </div>
  );
}
