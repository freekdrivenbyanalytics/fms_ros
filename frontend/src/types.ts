export type VisitStatus = "unassigned" | "assigned";

export interface Region {
  id: number;
  name: string;
}

export interface Skill {
  id: number;
  name: string;
}

export interface Customer {
  id: number;
  version: number | null;
  url: string | null;
  name: string;
  organization_number: string | null;
  global_location_number: number | null;
  supplier_number: number | null;
  customer_number: number | null;
  is_supplier: boolean | null;
  is_customer: boolean | null;
  is_inactive: boolean | null;
  email: string | null;
  invoice_email: string | null;
  overdue_notice_email: string | null;
  phone_number: string | null;
  phone_number_mobile: string | null;
  description: string | null;
  language: string | null;
  display_name: string | null;
  is_private_individual: boolean | null;
  single_customer_invoice: boolean | null;
  invoice_send_method: string | null;
  email_attachment_type: string | null;
  invoices_due_in: number | null;
  invoices_due_in_type: string | null;
  is_factoring: boolean | null;
  invoice_send_sms_notification: boolean | null;
  invoice_sms_notification_number: string | null;
  is_automatic_soft_reminder_enabled: boolean | null;
  is_automatic_reminder_enabled: boolean | null;
  is_automatic_notice_of_debt_collection_enabled: boolean | null;
  discount_percentage: number | null;
  website: string | null;
  account_manager: Record<string, unknown> | null;
  department: Record<string, unknown> | null;
  postal_address: Record<string, unknown> | null;
  physical_address: Record<string, unknown> | null;
  delivery_address: Record<string, unknown> | null;
  category1: Record<string, unknown> | null;
  category2: Record<string, unknown> | null;
  category3: Record<string, unknown> | null;
  currency: Record<string, unknown> | null;
  ledger_account: Record<string, unknown> | null;
  bank_account_presentation: unknown[] | null;
}

export interface CustomerLocation {
  id: number;
  address: string;
  latitude: number | null;
  longitude: number | null;
  customer: Customer;
  region: Region | null;
}

export interface Contract {
  id: number;
  start_date: string;
  interval_days: number;
  duration_minutes: number;
  customer_location: CustomerLocation;
  required_skills: Skill[];
}

export interface Employee {
  id: number;
  name: string;
  work_start: string;
  work_end: string;
  latitude: number;
  longitude: number;
  regions: Region[];
  skills: Skill[];
}

export interface ServiceVisit {
  id: number;
  requested_date: string;
  status: VisitStatus;
  contract: Contract;
}

export interface Assignment {
  service_visit_id: number;
  employee_id: number;
  planned_start: string;
  planned_end: string;
  pinned: boolean;
  employee: Employee;
  service_visit: ServiceVisit;
}

export interface CreateAssignmentInput {
  service_visit_id: number;
  employee_id: number;
  planned_start: string;
}

export interface ProposedAssignment {
  service_visit_id: number;
  employee_id: number;
  planned_start: string;
  planned_end: string;
  employee: Employee;
  service_visit: ServiceVisit;
}

export interface OptimizationProposal {
  scheduled: ProposedAssignment[];
  unscheduled_visit_ids: number[];
}

export interface OptimizationApplyResult {
  created: Assignment[];
  skipped_visit_ids: number[];
}
