const TWENTY_URL = process.env.NEXT_PUBLIC_TWENTY_URL || "http://localhost:3000";
const TWENTY_KEY = process.env.NEXT_PUBLIC_TWENTY_API_KEY || "";

/* ------------------------------------------------------------------ */
/* Generic request helper                                              */
/* ------------------------------------------------------------------ */

async function twentyRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (!TWENTY_KEY) {
    throw new Error("NEXT_PUBLIC_TWENTY_API_KEY not configured");
  }
  const res = await fetch(`${TWENTY_URL}/rest${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${TWENTY_KEY}`,
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Twenty ${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

/**
 * Twenty REST API response format:
 * { data: { people: [...] }, totalCount: N, pageInfo: {...} }
 */
function extractArray<T>(response: unknown, key: string): T[] {
  if (!response) return [];
  if (Array.isArray(response)) return response;
  const r = response as Record<string, unknown>;

  // { data: { people: [...] } }
  if (r.data && typeof r.data === "object" && !Array.isArray(r.data)) {
    const nested = r.data as Record<string, unknown>;
    if (Array.isArray(nested[key])) return nested[key] as T[];
  }

  // { data: [...] }
  if (Array.isArray(r.data)) return r.data as T[];

  // { people: [...] }
  if (Array.isArray(r[key])) return r[key] as T[];

  return [];
}

/* ------------------------------------------------------------------ */
/* People (Contacts)                                                   */
/* ------------------------------------------------------------------ */

// Twenty's actual schema (from API response)
export interface Person {
  id: string;
  name: { firstName: string; lastName: string };
  emails: { primaryEmail: string; additionalEmails: string[] };
  phones: {
    primaryPhoneNumber: string;
    primaryPhoneCountryCode: string;
    primaryPhoneCallingCode: string;
    additionalPhones: string[];
  };
  jobTitle: string;
  city: string;
  avatarUrl: string;
  companyId: string | null;
  createdAt: string;
  updatedAt: string;
}

export function personDisplayName(p: Person): string {
  return [p.name?.firstName, p.name?.lastName].filter(Boolean).join(" ") || "Sin nombre";
}

export function personEmail(p: Person): string {
  return p.emails?.primaryEmail || "";
}

export function personPhone(p: Person): string {
  const calling = p.phones?.primaryPhoneCallingCode || "";
  const number = p.phones?.primaryPhoneNumber || "";
  if (!number) return "";
  return calling ? `${calling}${number}` : number;
}

export const listPeople = async (limit = 50): Promise<Person[]> => {
  const response = await twentyRequest<unknown>(`/people?limit=${limit}`);
  return extractArray<Person>(response, "people");
};

export const createPerson = (data: {
  firstName: string;
  lastName?: string;
  email?: string;
  phone?: string;
  jobTitle?: string;
  city?: string;
}) =>
  twentyRequest<unknown>("/people", {
    method: "POST",
    body: JSON.stringify({
      name: { firstName: data.firstName, lastName: data.lastName || "" },
      emails: { primaryEmail: data.email || "", additionalEmails: [] },
      phones: {
        primaryPhoneNumber: data.phone || "",
        primaryPhoneCountryCode: "",
        primaryPhoneCallingCode: "",
        additionalPhones: [],
      },
      jobTitle: data.jobTitle || "",
      city: data.city || "",
    }),
  });

/* ------------------------------------------------------------------ */
/* Companies                                                           */
/* ------------------------------------------------------------------ */

export interface Company {
  id: string;
  name: string;
  domainName: string;
  employees: number;
  address: string;
  createdAt: string;
}

export const listCompanies = async (limit = 50): Promise<Company[]> => {
  const response = await twentyRequest<unknown>(`/companies?limit=${limit}`);
  return extractArray<Company>(response, "companies");
};

export const createCompany = (data: {
  name: string;
  domainName?: string;
  employees?: number;
}) =>
  twentyRequest<unknown>("/companies", {
    method: "POST",
    body: JSON.stringify({
      name: data.name,
      domainName: data.domainName || "",
      employees: data.employees || 0,
    }),
  });

/* ------------------------------------------------------------------ */
/* Tasks                                                               */
/* ------------------------------------------------------------------ */

export interface Task {
  id: string;
  title: string;
  body: string;
  status: string;
  dueAt: string | null;
  createdAt: string;
}

export const listTasks = async (limit = 50): Promise<Task[]> => {
  const response = await twentyRequest<unknown>(`/tasks?limit=${limit}`);
  return extractArray<Task>(response, "tasks");
};

export const createTask = (data: { title: string; body?: string }) =>
  twentyRequest<unknown>("/tasks", {
    method: "POST",
    body: JSON.stringify({ title: data.title, body: data.body || "" }),
  });

/* ------------------------------------------------------------------ */
/* Notes                                                               */
/* ------------------------------------------------------------------ */

export interface Note {
  id: string;
  title: string;
  body: string;
  createdAt: string;
}

export const listNotes = async (limit = 50): Promise<Note[]> => {
  const response = await twentyRequest<unknown>(`/notes?limit=${limit}`);
  return extractArray<Note>(response, "notes");
};

export const createNote = (data: { title: string; body: string }) =>
  twentyRequest<unknown>("/notes", {
    method: "POST",
    body: JSON.stringify({ title: data.title, body: data.body }),
  });
