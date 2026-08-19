export type VisitStatus = "unassigned" | "assigned";

export interface Employee {
  id: number;
  name: string;
  work_start: string;
  work_end: string;
  latitude: number;
  longitude: number;
}

export interface ServiceVisit {
  id: number;
  customer_name: string;
  address: string;
  latitude: number;
  longitude: number;
  duration_minutes: number;
  requested_date: string;
  status: VisitStatus;
}

export interface Assignment {
  service_visit_id: number;
  employee_id: number;
  planned_start: string;
  planned_end: string;
  employee: Employee;
  service_visit: ServiceVisit;
}

export interface CreateAssignmentInput {
  service_visit_id: number;
  employee_id: number;
  planned_start: string;
}
