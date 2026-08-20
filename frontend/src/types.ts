export type VisitStatus = "unassigned" | "assigned";

export interface Region {
  id: number;
  name: string;
}

export interface Customer {
  id: number;
  name: string;
}

export interface CustomerLocation {
  id: number;
  address: string;
  latitude: number;
  longitude: number;
  customer: Customer;
  region: Region;
}

export interface Employee {
  id: number;
  name: string;
  work_start: string;
  work_end: string;
  latitude: number;
  longitude: number;
  regions: Region[];
}

export interface ServiceVisit {
  id: number;
  duration_minutes: number;
  requested_date: string;
  status: VisitStatus;
  customer_location: CustomerLocation;
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
