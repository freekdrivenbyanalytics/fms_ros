import type {
  Assignment,
  Contract,
  ContractCreateInput,
  ContractLine,
  ContractLineCreateInput,
  ContractLineUpdateInput,
  ContractUpdateInput,
  CreateAssignmentInput,
  Customer,
  CustomerLocation,
  Employee,
  EmployeeCreateInput,
  EmployeeScheduleDayOverride,
  EmployeeScheduleDayOverrideBulkInput,
  EmployeeScheduleDayOverrideInput,
  EmployeeScheduleTemplate,
  EmployeeScheduleTemplateInput,
  EmployeeUpdateInput,
  OptimizationApplyResult,
  OptimizationProposal,
  Region,
  RegionCreateInput,
  RegionUpdateInput,
  ServiceVisit,
  Skill,
  SkillCreateInput,
  SkillUpdateInput,
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

export function createEmployee(input: EmployeeCreateInput): Promise<Employee> {
  return fetch(`${API_URL}/employees`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Employee>(res));
}

export function updateEmployee(id: number, input: EmployeeUpdateInput): Promise<Employee> {
  return fetch(`${API_URL}/employees/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Employee>(res));
}

export async function deleteEmployee(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/employees/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
}

export function createScheduleTemplate(
  employeeId: number,
  input: EmployeeScheduleTemplateInput
): Promise<EmployeeScheduleTemplate> {
  return fetch(`${API_URL}/employees/${employeeId}/schedule-templates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<EmployeeScheduleTemplate>(res));
}

export function updateScheduleTemplate(
  id: number,
  input: EmployeeScheduleTemplateInput
): Promise<EmployeeScheduleTemplate> {
  return fetch(`${API_URL}/schedule-templates/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<EmployeeScheduleTemplate>(res));
}

export async function deleteScheduleTemplate(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/schedule-templates/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
}

export function createScheduleOverride(
  employeeId: number,
  input: EmployeeScheduleDayOverrideInput
): Promise<EmployeeScheduleDayOverride> {
  return fetch(`${API_URL}/employees/${employeeId}/schedule-overrides`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<EmployeeScheduleDayOverride>(res));
}

export function updateScheduleOverride(
  id: number,
  input: EmployeeScheduleDayOverrideInput
): Promise<EmployeeScheduleDayOverride> {
  return fetch(`${API_URL}/schedule-overrides/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<EmployeeScheduleDayOverride>(res));
}

export async function deleteScheduleOverride(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/schedule-overrides/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
}

export function createScheduleOverridesBulk(
  employeeId: number,
  input: EmployeeScheduleDayOverrideBulkInput
): Promise<EmployeeScheduleDayOverride[]> {
  return fetch(`${API_URL}/employees/${employeeId}/schedule-overrides/bulk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<EmployeeScheduleDayOverride[]>(res));
}

export function listServiceVisits(
  range?: { startDate?: string; endDate?: string }
): Promise<ServiceVisit[]> {
  const params = new URLSearchParams();
  if (range?.startDate) params.set("start_date", range.startDate);
  if (range?.endDate) params.set("end_date", range.endDate);
  const query = params.toString();
  return fetch(`${API_URL}/service-visits${query ? `?${query}` : ""}`).then((res) =>
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

export function createRegion(input: RegionCreateInput): Promise<Region> {
  return fetch(`${API_URL}/regions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Region>(res));
}

export function updateRegion(id: number, input: RegionUpdateInput): Promise<Region> {
  return fetch(`${API_URL}/regions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Region>(res));
}

export async function deleteRegion(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/regions/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
}

export function listSkills(): Promise<Skill[]> {
  return fetch(`${API_URL}/skills`).then((res) => handleResponse<Skill[]>(res));
}

export function createSkill(input: SkillCreateInput): Promise<Skill> {
  return fetch(`${API_URL}/skills`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Skill>(res));
}

export function updateSkill(id: number, input: SkillUpdateInput): Promise<Skill> {
  return fetch(`${API_URL}/skills/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Skill>(res));
}

export async function deleteSkill(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/skills/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
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

export function createContract(input: ContractCreateInput): Promise<Contract> {
  return fetch(`${API_URL}/contracts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Contract>(res));
}

export function updateContract(
  id: number,
  input: ContractUpdateInput
): Promise<Contract> {
  return fetch(`${API_URL}/contracts/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<Contract>(res));
}

export async function deleteContract(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/contracts/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
}

export function createContractLine(
  contractId: number,
  input: ContractLineCreateInput
): Promise<ContractLine> {
  return fetch(`${API_URL}/contracts/${contractId}/lines`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<ContractLine>(res));
}

export function updateContractLine(
  id: number,
  input: ContractLineUpdateInput
): Promise<ContractLine> {
  return fetch(`${API_URL}/contract-lines/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then((res) => handleResponse<ContractLine>(res));
}

export async function deleteContractLine(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/contract-lines/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
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

export async function unassignVisit(serviceVisitId: number): Promise<void> {
  const res = await fetch(`${API_URL}/assignments/${serviceVisitId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Request failed with status ${res.status}`;
    throw new Error(message);
  }
}

export function setAssignmentPinned(
  serviceVisitId: number,
  pinned: boolean
): Promise<Assignment> {
  return fetch(`${API_URL}/assignments/${serviceVisitId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pinned }),
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
