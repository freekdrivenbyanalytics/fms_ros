import type {
  Assignment,
  Contract,
  CreateAssignmentInput,
  Customer,
  CustomerLocation,
  Employee,
  OptimizationApplyResult,
  OptimizationProposal,
  Region,
  ServiceVisit,
  Skill,
} from "./types";

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

export function listRegions(): Promise<Region[]> {
  return fetch(`${API_URL}/regions`).then((res) => handleResponse<Region[]>(res));
}

export function listSkills(): Promise<Skill[]> {
  return fetch(`${API_URL}/skills`).then((res) => handleResponse<Skill[]>(res));
}

export function listCustomers(): Promise<Customer[]> {
  return fetch(`${API_URL}/customers`).then((res) => handleResponse<Customer[]>(res));
}

export function listCustomerLocations(): Promise<CustomerLocation[]> {
  return fetch(`${API_URL}/customer-locations`).then((res) =>
    handleResponse<CustomerLocation[]>(res)
  );
}

export function listContracts(): Promise<Contract[]> {
  return fetch(`${API_URL}/contracts`).then((res) => handleResponse<Contract[]>(res));
}

export function syncCustomers(): Promise<Customer[]> {
  return fetch(`${API_URL}/customers/sync`, { method: "POST" }).then((res) =>
    handleResponse<Customer[]>(res)
  );
}

export function createAssignment(input: CreateAssignmentInput): Promise<Assignment> {
  return fetch(`${API_URL}/assignments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Assignment>(res));
}

export function proposeOptimization(): Promise<OptimizationProposal> {
  return fetch(`${API_URL}/optimize/propose`, { method: "POST" }).then((res) =>
    handleResponse<OptimizationProposal>(res)
  );
}

export function applyOptimization(
  scheduled: CreateAssignmentInput[]
): Promise<OptimizationApplyResult> {
  return fetch(`${API_URL}/optimize/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scheduled }),
  }).then((res) => handleResponse<OptimizationApplyResult>(res));
}
