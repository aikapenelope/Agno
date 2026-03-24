const TWENTY_URL = process.env.NEXT_PUBLIC_TWENTY_URL || "http://localhost:3000";
const TWENTY_KEY = process.env.NEXT_PUBLIC_TWENTY_API_KEY || "";

async function twentyRequest<T>(path: string, init?: RequestInit): Promise<T> {
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
    throw new Error(`Twenty ${res.status}: ${text}`);
  }
  return res.json();
}

/* ------------------------------------------------------------------ */
/* People (Contacts)                                                   */
/* ------------------------------------------------------------------ */

export interface Person {
  id: string;
  name?: { firstName?: string; lastName?: string };
  emails?: Array<{ address?: string }>;
  phones?: Array<{ number?: string }>;
  company?: { name?: string };
  jobTitle?: string;
  city?: string;
  createdAt?: string;
  updatedAt?: string;
}

export const listPeople = (limit = 50) =>
  twentyRequest<{ data: { people: Person[] } }>(`/people?limit=${limit}`).then(
    (r) => r?.data?.people || [],
  );

export const createPerson = (data: {
  firstName: string;
  lastName: string;
  email?: string;
  phone?: string;
  jobTitle?: string;
  city?: string;
}) =>
  twentyRequest<unknown>("/people", {
    method: "POST",
    body: JSON.stringify({
      name: { firstName: data.firstName, lastName: data.lastName },
      emails: data.email ? [{ address: data.email }] : undefined,
      phones: data.phone ? [{ number: data.phone }] : undefined,
      jobTitle: data.jobTitle,
      city: data.city,
    }),
  });

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

export const listCompanies = (limit = 50) =>
  twentyRequest<{ data: { companies: Company[] } }>(
    `/companies?limit=${limit}`,
  ).then((r) => r?.data?.companies || []);

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

export const listTasks = (limit = 50) =>
  twentyRequest<{ data: { tasks: Task[] } }>(`/tasks?limit=${limit}`).then(
    (r) => r?.data?.tasks || [],
  );

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

export const listNotes = (limit = 50) =>
  twentyRequest<{ data: { notes: Note[] } }>(`/notes?limit=${limit}`).then(
    (r) => r?.data?.notes || [],
  );

export const createNote = (data: { title: string; body: string }) =>
  twentyRequest<unknown>("/notes", {
    method: "POST",
    body: JSON.stringify(data),
  });
