import type { Assignment, CreateAssignmentInput, Employee, ServiceVisit } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export function listEmployees(): Promise<Employee[]> {
  return fetch(`${API_URL}/employees`).then((res) => handleResponse<Employee[]>(res));
}

export function listServiceVisits(): Promise<ServiceVisit[]> {
  return fetch(`${API_URL}/service-visits`).then((res) =>
    handleResponse<ServiceVisit[]>(res)
  );
}

export function listAssignments(): Promise<Assignment[]> {
  return fetch(`${API_URL}/assignments`).then((res) =>
    handleResponse<Assignment[]>(res)
  );
}

export function createAssignment(input: CreateAssignmentInput): Promise<Assignment> {
  return fetch(`${API_URL}/assignments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Assignment>(res));
}
