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
 * Twenty API returns data in different formats depending on version.
 * This helper extracts an array from whatever format comes back:
 * - { data: { people: [...] } }  (GraphQL-style)
 * - { data: [...] }              (REST v2)
 * - { people: [...] }            (REST v1)
 * - [...]                        (plain array)
 */
function extractArray<T>(response: unknown, key: string): T[] {
  if (!response) return [];
  if (Array.isArray(response)) return response;

  const r = response as Record<string, unknown>;

  // { data: { people: [...] } }
  if (r.data && typeof r.data === "object" && !Array.isArray(r.data)) {
    const nested = r.data as Record<string, unknown>;
    if (Array.isArray(nested[key])) return nested[key] as T[];
    // Maybe it's { data: [...] } inside
    const values = Object.values(nested);
    for (const v of values) {
      if (Array.isArray(v)) return v as T[];
    }
  }

  // { data: [...] }
  if (Array.isArray(r.data)) return r.data as T[];

  // { people: [...] }
  if (Array.isArray(r[key])) return r[key] as T[];

  // Try any array value
  for (const v of Object.values(r)) {
    if (Array.isArray(v)) return v as T[];
  }

  console.warn(`Twenty: could not extract array "${key}" from response:`, JSON.stringify(response).slice(0, 300));
  return [];
}

/* ------------------------------------------------------------------ */
/* People (Contacts)                                                   */
/* ------------------------------------------------------------------ */

export interface Person {
  id: string;
  name?: { firstName?: string; lastName?: string };
  emails?: Array<{ address?: string; primaryEmail?: string }>;
  phones?: Array<{ number?: string; primaryPhoneNumber?: string }>;
  company?: { name?: string };
  companyId?: string;
  jobTitle?: string;
  city?: string;
  createdAt?: string;
  updatedAt?: string;
  // Twenty may use flat fields instead of nested
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
}

export function personDisplayName(p: Person): string {
  if (p.name?.firstName || p.name?.lastName) {
    return [p.name.firstName, p.name.lastName].filter(Boolean).join(" ");
  }
  if (p.firstName || p.lastName) {
    return [p.firstName, p.lastName].filter(Boolean).join(" ");
  }
  return "Sin nombre";
}

export function personEmail(p: Person): string {
  return p.emails?.[0]?.address || p.emails?.[0]?.primaryEmail || p.email || "";
}

export function personPhone(p: Person): string {
  return p.phones?.[0]?.number || p.phones?.[0]?.primaryPhoneNumber || p.phone || "";
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
}) => {
  // Try multiple field formats since Twenty schema varies
  const body: Record<string, unknown> = {};

  // Try nested name first, then flat
  body.name = { firstName: data.firstName, lastName: data.lastName || "" };

  if (data.email) {
    body.emails = [{ address: data.email }];
  }
  if (data.phone) {
    body.phones = [{ number: data.phone }];
  }
  if (data.jobTitle) body.jobTitle = data.jobTitle;
  if (data.city) body.city = data.city;

  return twentyRequest<unknown>("/people", {
    method: "POST",
    body: JSON.stringify(body),
  });
};

/* ------------------------------------------------------------------ */
/* Companies                                                           */
/* ------------------------------------------------------------------ */

export interface Company {
  id: string;
  name?: string;
  domainName?: string;
  employees?: number;
  address?: string;
  createdAt?: string;
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
    body: JSON.stringify(data),
  });

/* ------------------------------------------------------------------ */
/* Tasks                                                               */
/* ------------------------------------------------------------------ */

export interface Task {
  id: string;
  title?: string;
  body?: string;
  status?: string;
  dueAt?: string;
  assignee?: { name?: { firstName?: string; lastName?: string } };
  createdAt?: string;
}

export const listTasks = async (limit = 50): Promise<Task[]> => {
  const response = await twentyRequest<unknown>(`/tasks?limit=${limit}`);
  return extractArray<Task>(response, "tasks");
};

export const createTask = (data: { title: string; body?: string; dueAt?: string }) =>
  twentyRequest<unknown>("/tasks", {
    method: "POST",
    body: JSON.stringify(data),
  });

/* ------------------------------------------------------------------ */
/* Notes                                                               */
/* ------------------------------------------------------------------ */

export interface Note {
  id: string;
  title?: string;
  body?: string;
  createdAt?: string;
}

export const listNotes = async (limit = 50): Promise<Note[]> => {
  const response = await twentyRequest<unknown>(`/notes?limit=${limit}`);
  return extractArray<Note>(response, "notes");
};

export const createNote = (data: { title: string; body: string }) =>
  twentyRequest<unknown>("/notes", {
    method: "POST",
    body: JSON.stringify(data),
  });
